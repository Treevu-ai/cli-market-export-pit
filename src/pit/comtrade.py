"""UN Comtrade connector for trade flows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ISO_TO_COMTRADE: dict[str, str] = {
    "US": "842",
    "DE": "276",
    "PE": "604",
    "GB": "826",
    "FR": "250",
    "ES": "724",
    "IT": "380",
    "MX": "484",
    "BR": "076",
    "CN": "156",
    "JP": "392",
}


class ComtradeRequestError(RuntimeError):
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
class ComtradeResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class ComtradeConnector:
    source = "comtrade"
    license_name = "UN Comtrade; open data with attribution"
    # Confirmed live against the real API portal (comtradedeveloper.un.org,
    # "comtrade" API group, "get" operation): /getData with a "filter" JSON
    # blob and subscription-key=public never existed -- the real shape is
    # path-segmented (typeCode/freqCode/clCode) with flat query params and
    # an Ocp-Apim-Subscription-Key header (standard Azure APIM auth), which
    # "public" was never a valid value for.
    base_url = "https://comtradeapi.un.org/data/v1/get"

    def __init__(self, subscription_key: str | None = None) -> None:
        self.subscription_key = subscription_key or os.getenv("COMTRADE_SUBSCRIPTION_KEY")

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        hs_code: str | None = None,
        # Confirmed live: reporterCode=0 ("World" aggregate) returns zero
        # HS6-level records from the real Comtrade API -- it needs an
        # actual reporting country. PIT's whole premise is Peru's export
        # potential, so Peru (604) is the correct default reporter rather
        # than an aggregate that silently returns nothing.
        reporter_country: str = "604",
        partner_country: str | None = None,
        target_market: str | None = None,
        flow: str = "all",
    ) -> ComtradeResponse:
        resolved_partner = partner_country
        if resolved_partner is None and target_market:
            resolved_partner = ISO_TO_COMTRADE.get(target_market.upper(), "0")
        if resolved_partner is None:
            resolved_partner = "0"
        # period takes a comma-separated list of 4-digit years, not a
        # hyphenated range -- cap the window at 5 years ending on the most
        # recent likely-complete year (data usually lags ~1 year).
        from_year = int(from_publication_date[:4])
        end_year = date.today().year - 1
        years = range(max(from_year, end_year - 4), end_year + 1)
        flow_code = "" if flow == "all" else flow.upper()[:1]
        params: dict[str, str] = {
            "reporterCode": reporter_country,
            "partnerCode": resolved_partner,
            "period": ",".join(str(y) for y in years),
            "cmdCode": hs_code or "",
            "flowCode": flow_code,
            "includeDesc": "true",
        }
        request_url = f"{self.base_url}/C/A/HS?{urlencode(params)}"
        headers = {"User-Agent": "PIT/0.1 research-service"}
        if self.subscription_key:
            headers["Ocp-Apim-Subscription-Key"] = self.subscription_key
        request = Request(request_url, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise ComtradeRequestError(
                f"UN Comtrade returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except (URLError, TimeoutError) as error:
            raise ComtradeRequestError(
                f"UN Comtrade network error: {error}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            records = body.get("data", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise ComtradeRequestError(
                "UN Comtrade response did not contain data",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        # The real API has no page/perPage/limit param (confirmed against
        # its documented parameter list) -- truncate client-side instead.
        works: list[dict[str, Any]] = []
        for record in records[:limit]:
            period = record.get("period")
            works.append({
                "reporter": record.get("reporterDesc"),
                "partner": record.get("partnerDesc"),
                "flow": record.get("flowDesc"),
                "period": str(period) if period else None,
                # Real field names confirmed live: primaryValue (trade value
                # in USD) and netWgt (net weight in kg) -- tradeValue/
                # netWeight don't exist on the real response.
                "trade_value_usd": record.get("primaryValue"),
                "net_weight_kg": record.get("netWgt"),
                "hs_code": record.get("cmdCode"),
                "source": "comtrade",
            })

        return ComtradeResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
