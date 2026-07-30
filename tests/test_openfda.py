from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pit.openfda import OpenFDAConnector


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class OpenFDAQueryConstructionTests(unittest.TestCase):
    """Regression: OpenFDA returned HTTP 400 because the query was a bare,
    unscoped phrase (Lucene requires a field:value term) and the date range
    used hyphenated ISO dates instead of OpenFDA's required YYYYMMDD."""

    def test_search_builds_field_scoped_query_with_unhyphenated_dates(self) -> None:
        connector = OpenFDAConnector()
        with patch("pit.openfda.urlopen", return_value=_fake_response(b'{"results":[]}')) as mocked_urlopen:
            connector.search(
                query="arándano orgánico",
                from_publication_date="2026-01-01",
                limit=5,
                target_market="US",
            )

        request = mocked_urlopen.call_args[0][0]
        self.assertIn("report_date%3A%5B20260101", request.full_url)
        self.assertIn("product_description%3A", request.full_url)
        self.assertNotIn("2026-01-01", request.full_url)

    def test_search_skips_request_for_non_us_market(self) -> None:
        connector = OpenFDAConnector()
        with patch("pit.openfda.urlopen") as mocked_urlopen:
            result = connector.search(
                query="arándano orgánico", from_publication_date="2026-01-01", limit=5, target_market="PE"
            )

        mocked_urlopen.assert_not_called()
        self.assertEqual(result.works, [])


if __name__ == "__main__":
    unittest.main()
