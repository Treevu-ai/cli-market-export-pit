"""WITS (World Integrated Trade Solution / UNCTAD TRAINS) connector for tariff data."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class WITSRequestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        raw_content: bytes | None = None,
        request_url: str | None = None,
        request_params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.raw_content = raw_content
        self.request_url = request_url
        self.request_params = request_params


@dataclass(frozen=True)
class WITSResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class WITSConnector:
    source = "wits"
    license_name = "WITS / UNCTAD TRAINS; open data, no API key required"
    base_url = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN"
    max_retries = 3
    retryable_statuses = frozenset({429, 500, 502, 503, 504})

    # Confirmed live against the WITS reporter/partner metadata endpoint
    # (wits/datasource/trn/country/{codes}) -- WITS uses UN numeric country
    # codes (ISO 3166-1 numeric), not alpha-2. Only markets PIT actually
    # targets are mapped; unmapped markets skip the request rather than
    # guessing a code.
    REPORTER_CODES: dict[str, str] = {
        "US": "840",
        "EU": "918",
        "PE": "604",
        "MX": "484",
        "CL": "152",
        "AR": "032",
        "CO": "170",
        "BR": "076",
    }
    # PIT's product catalog is Peru-origin exports -- the partner (exporting
    # country whose preferential rate we want) is always Peru.
    PARTNER_CODE = "604"

    def search(self, *, target_market: str, hs_code: str | None) -> WITSResponse:
        if not hs_code:
            return WITSResponse(
                request_url=self.base_url,
                request_params={"target_market": target_market, "hs_code": ""},
                http_status=200,
                raw_content=b"{}",
                works=[],
            )
        reporter = self.REPORTER_CODES.get(target_market.upper())
        if reporter is None:
            return WITSResponse(
                request_url=self.base_url,
                request_params={"target_market": target_market, "hs_code": hs_code},
                http_status=200,
                raw_content=b"{}",
                works=[],
            )

        request_url = (
            f"{self.base_url}/reporter/{reporter}/partner/{self.PARTNER_CODE}"
            f"/product/{hs_code}/year/all/datatype/reported?format=JSON"
        )
        params = {
            "reporter": reporter,
            "partner": self.PARTNER_CODE,
            "product": hs_code,
            "year": "all",
            "datatype": "reported",
        }
        # Confirmed live: WITS returns a bare HTTP 403 for any request with
        # no User-Agent header at all (Python's default urllib UA) -- any
        # custom User-Agent, even a plain self-identifying one, is enough
        # to get past it.
        request = Request(
            request_url,
            headers={"Accept": "application/json", "User-Agent": "PIT/0.1 research-service"},
        )
        # Confirmed live: WITS occasionally times out (a bare TimeoutError,
        # not wrapped in URLError) or 5xx's under repeated calls in a short
        # window, then serves the identical request fine moments later --
        # retry with backoff rather than treating one flaky call as
        # permanently broken.
        last_error: WITSRequestError | None = None
        for attempt in range(self.max_retries):
            try:
                with urlopen(request, timeout=20) as response:
                    raw_content = response.read()
                    http_status = response.status
                break
            except HTTPError as error:
                raw_content = error.read()
                # Confirmed live: WITS returns HTTP 404 with the literal
                # body "{}Not Found - NoRecordsFound" for a genuinely empty
                # tariff schedule -- a normal "nothing found" answer, not a
                # bug.
                if error.code == 404 and b"NoRecordsFound" in raw_content:
                    return WITSResponse(
                        request_url=request_url,
                        request_params=params,
                        http_status=200,
                        raw_content=raw_content,
                        works=[],
                    )
                last_error = WITSRequestError(
                    f"WITS returned HTTP {error.code}",
                    http_status=error.code,
                    raw_content=raw_content,
                    request_url=request_url,
                    request_params=params,
                )
                if error.code in self.retryable_statuses and attempt < self.max_retries - 1:
                    time.sleep(3 * (2**attempt))
                    continue
                raise last_error from error
            except (URLError, TimeoutError) as error:
                last_error = WITSRequestError(
                    f"WITS network error: {error}",
                    request_url=request_url,
                    request_params=params,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(3 * (2**attempt))
                    continue
                raise last_error from error

        try:
            body = json.loads(raw_content)
            works = _normalize_tariff_series(body, hs_code=hs_code, reporter=reporter)
        except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as error:
            raise WITSRequestError(
                "WITS response did not contain tariff data",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        return WITSResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )


def _normalize_tariff_series(body: dict[str, Any], *, hs_code: str, reporter: str) -> list[dict[str, Any]]:
    # SDMX-JSON generic format, confirmed live: dataSets[0].series maps a
    # dimension-index key (e.g. "0:0:0:0:0") to an `observations` dict whose
    # keys are observation indices, in the same order as
    # structure.observation[0].values (the list of years requested).
    datasets = body.get("dataSets", [])
    if not datasets:
        return []
    series = datasets[0].get("series", {})
    observation_dims = body.get("structure", {}).get("dimensions", {}).get("observation", [])
    years = observation_dims[0].get("values", []) if observation_dims else []

    works: list[dict[str, Any]] = []
    for series_key, series_data in series.items():
        observations = series_data.get("observations", {})
        for obs_index, obs_values in observations.items():
            try:
                year = years[int(obs_index)].get("id", "")
            except (IndexError, ValueError, AttributeError):
                year = ""
            simple_average = obs_values[0] if obs_values else None
            if simple_average is None:
                continue
            works.append({
                "hs_code": hs_code,
                "reporter": reporter,
                "partner": WITSConnector.PARTNER_CODE,
                "year": year,
                "simple_average_pct": simple_average,
                "series_key": series_key,
                "source": "wits",
            })
    return works
