"""FoodData Central connector for nutritional data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class FoodDataCentralRequestError(RuntimeError):
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
class FoodDataCentralResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class FoodDataCentralConnector:
    source = "fooddata_central"
    license_name = "FoodData Central; public domain"
    base_url = "https://api.nal.usda.gov/fdc/v1/search"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search(self, *, query: str, from_publication_date: str, limit: int) -> FoodDataCentralResponse:
        params: dict[str, str] = {
            "query": query,
            "pageSize": str(limit),
            "format": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        request_url = f"{self.base_url}?{urlencode(params)}"
        request = Request(
            request_url,
            headers={"User-Agent": "Pitchavi/0.1 research-service"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise FoodDataCentralRequestError(
                f"FoodData Central returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise FoodDataCentralRequestError(
                f"FoodData Central network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            foods = body.get("foods", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise FoodDataCentralRequestError(
                "FoodData Central response did not contain foods",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for food in foods:
            works.append({
                "fdc_id": food.get("fdcId"),
                "title": food.get("description"),
                "data_type": food.get("dataType"),
                "source": "fooddata_central",
            })

        return FoodDataCentralResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
