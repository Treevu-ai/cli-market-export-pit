from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.usda_fas import USDAFASConnector, USDAFASRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


# Real shape confirmed live for commodity 0711100 (Coffee, Green), world,
# year 2024: attributeId 28/86/88/125/176 are the generic Production/
# Total Supply/Exports/Domestic Consumption/Ending Stocks fields present
# across commodities; others (29 Arabica Production, 58 Bean Imports, ...)
# are commodity-specific sub-splits, not surfaced here.
PSD_BODY = (
    b'[{"commodityCode":"0711100","marketYear":"2024","attributeId":28,"unitId":2,"value":176816.0},'
    b'{"commodityCode":"0711100","marketYear":"2024","attributeId":29,"unitId":2,"value":102276.0},'
    b'{"commodityCode":"0711100","marketYear":"2024","attributeId":88,"unitId":2,"value":147746.0},'
    b'{"commodityCode":"0711100","marketYear":"2024","attributeId":176,"unitId":2,"value":22010.0}]'
)


class USDAFASCommodityMatchTests(unittest.TestCase):
    """Regression: USDA's PSD database only covers ~55 bulk commodities
    (confirmed live via /api/psd/commodities) -- most of PIT's specialty/
    functional product catalog (cacao, palta, quinua, camu camu, ...) has
    no match. Only query terms that genuinely match a PSD commodity should
    fire a request; everything else must skip silently rather than guess."""

    def test_search_skips_request_for_unmatched_product(self) -> None:
        connector = USDAFASConnector(api_key="test-key")
        with patch("pit.usda_fas.urlopen") as mocked_urlopen:
            result = connector.search(query="cacao alto flavanol", market_year="2024")

        mocked_urlopen.assert_not_called()
        self.assertEqual(result.works, [])

    def test_search_skips_request_without_api_key(self) -> None:
        connector = USDAFASConnector(api_key=None)
        with patch("pit.usda_fas.urlopen") as mocked_urlopen:
            result = connector.search(query="cafe tostado especial", market_year="2024")

        mocked_urlopen.assert_not_called()
        self.assertEqual(result.works, [])

    def test_search_matches_coffee_and_builds_correct_url(self) -> None:
        connector = USDAFASConnector(api_key="test-key")
        with patch(
            "pit.usda_fas.urlopen", return_value=_fake_response(PSD_BODY)
        ) as mocked_urlopen:
            connector.search(query="café tostado especial", market_year="2024")

        request = mocked_urlopen.call_args[0][0]
        self.assertEqual(
            request.full_url,
            "https://api.fas.usda.gov/api/psd/commodity/0711100/world/year/2024",
        )
        self.assertEqual(request.get_header("X-api-key"), "test-key")

    def test_search_parses_generic_attributes_only(self) -> None:
        connector = USDAFASConnector(api_key="test-key")
        with patch("pit.usda_fas.urlopen", return_value=_fake_response(PSD_BODY)):
            result = connector.search(query="cafe tostado especial", market_year="2024")

        by_attribute = {w["attribute"]: w["value"] for w in result.works}
        self.assertEqual(by_attribute["production"], 176816.0)
        self.assertEqual(by_attribute["exports"], 147746.0)
        self.assertEqual(by_attribute["ending_stocks"], 22010.0)
        self.assertNotIn("arabica_production", by_attribute)

    def test_search_treats_404_as_empty_result(self) -> None:
        connector = USDAFASConnector(api_key="test-key")
        not_found = HTTPError(
            url="https://api.fas.usda.gov/api/psd/commodity/0711100/world/year/1800",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        not_found.read = lambda: b""
        with patch("pit.usda_fas.urlopen", side_effect=not_found):
            result = connector.search(query="cafe", market_year="1800")

        self.assertEqual(result.http_status, 200)
        self.assertEqual(result.works, [])

    def test_search_raises_on_other_http_errors(self) -> None:
        connector = USDAFASConnector(api_key="test-key")
        server_error = HTTPError(
            url="https://api.fas.usda.gov/api/psd/commodity/0711100/world/year/2024",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=None,
        )
        server_error.read = lambda: b"internal error"
        with patch("pit.usda_fas.urlopen", side_effect=server_error):
            with self.assertRaises(USDAFASRequestError):
                connector.search(query="cafe", market_year="2024")


if __name__ == "__main__":
    unittest.main()
