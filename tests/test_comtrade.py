from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pit.comtrade import ComtradeConnector


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


TRADE_BODY = (
    b'{"elapsedTime":"0.3 secs","count":1,"data":[{"reporterDesc":"Peru",'
    b'"partnerDesc":"World","flowDesc":"Export","period":"2022","cmdCode":"0810",'
    b'"primaryValue":1435275025.73,"netWgt":323842388.8}],"error":""}'
)


class ComtradeRequestConstructionTests(unittest.TestCase):
    """Regression: base_url was /getData with a JSON `filter` blob and
    subscription-key=public -- none of that is a real UN Comtrade contract.
    The real API is path-segmented (typeCode/freqCode/clCode) with flat
    query params and an Ocp-Apim-Subscription-Key header; confirmed live
    against the real API with a real subscription key."""

    def test_search_builds_correct_url_and_auth_header(self) -> None:
        connector = ComtradeConnector(subscription_key="test-key")
        with patch("pit.comtrade.urlopen", return_value=_fake_response(TRADE_BODY)) as mocked_urlopen:
            connector.search(
                query="blueberry",
                from_publication_date="2020-01-01",
                limit=5,
                reporter_country="604",
                partner_country="0",
                hs_code="0810",
                flow="X",
            )

        request = mocked_urlopen.call_args[0][0]
        self.assertTrue(request.full_url.startswith("https://comtradeapi.un.org/data/v1/get/C/A/HS?"))
        self.assertIn("reporterCode=604", request.full_url)
        self.assertIn("cmdCode=0810", request.full_url)
        self.assertEqual(request.get_header("Ocp-apim-subscription-key"), "test-key")

    def test_search_parses_real_field_names(self) -> None:
        connector = ComtradeConnector(subscription_key="test-key")
        with patch("pit.comtrade.urlopen", return_value=_fake_response(TRADE_BODY)):
            result = connector.search(
                query="blueberry", from_publication_date="2020-01-01", limit=5, reporter_country="604"
            )

        self.assertEqual(len(result.works), 1)
        work = result.works[0]
        self.assertEqual(work["trade_value_usd"], 1435275025.73)
        self.assertEqual(work["net_weight_kg"], 323842388.8)
        self.assertEqual(work["reporter"], "Peru")


if __name__ == "__main__":
    unittest.main()
