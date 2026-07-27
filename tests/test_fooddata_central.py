from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.fooddata_central import FoodDataCentralConnector, FoodDataCentralRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class FoodDataCentralApiKeyLeakTests(unittest.TestCase):
    """The api_key must reach the real request but never the persisted/returned metadata."""

    def test_search_success_does_not_expose_api_key(self) -> None:
        connector = FoodDataCentralConnector(api_key="super-secret-key")
        body = b'{"foods":[{"fdcId":123,"description":"Cocoa beans","dataType":"Foundation"}]}'
        with patch("pit.fooddata_central.urlopen", return_value=_fake_response(body)) as mocked_urlopen:
            response = connector.search(query="cocoa", from_publication_date="2021-01-01", limit=10)

        # The real HTTP call must still carry the key so USDA accepts the request.
        called_request = mocked_urlopen.call_args[0][0]
        self.assertIn("super-secret-key", called_request.full_url)

        # Anything that gets persisted/returned to callers must not contain it.
        self.assertNotIn("super-secret-key", response.request_url)
        self.assertNotIn("super-secret-key", str(response.request_params))

    def test_search_http_error_does_not_expose_api_key(self) -> None:
        connector = FoodDataCentralConnector(api_key="super-secret-key")
        http_error = HTTPError(
            url="https://api.nal.usda.gov/fdc/v1/search",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        http_error.read = lambda: b'{"error":"invalid api key"}'
        with patch("pit.fooddata_central.urlopen", side_effect=http_error):
            with self.assertRaises(FoodDataCentralRequestError) as raised:
                connector.search(query="cocoa", from_publication_date="2021-01-01", limit=10)

        error = raised.exception
        self.assertNotIn("super-secret-key", error.request_url or "")
        self.assertNotIn("super-secret-key", str(error.request_params or {}))


if __name__ == "__main__":
    unittest.main()
