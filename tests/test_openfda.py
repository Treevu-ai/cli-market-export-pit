from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.openfda import OpenFDAConnector, OpenFDARequestError


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


class OpenFDANoMatchesTests(unittest.TestCase):
    """Regression: OpenFDA returns HTTP 404 with {"error":{"code":"NOT_FOUND"}}
    when a query genuinely has zero matching recalls -- confirmed live via
    curl for a real product query. This used to raise OpenFDARequestError and
    take down the whole regulatory pipeline step for what is actually the
    normal case (most food products have no recalls)."""

    def test_search_treats_404_not_found_as_empty_results(self) -> None:
        connector = OpenFDAConnector()
        not_found = HTTPError(
            url="https://api.fda.gov/food/enforcement.json",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        not_found.read = lambda: b'{"error":{"code":"NOT_FOUND","message":"No matches found!"}}'
        with patch("pit.openfda.urlopen", side_effect=not_found):
            result = connector.search(
                query="camu camu pulpa congelada", from_publication_date="2022-01-01", limit=5, target_market="US"
            )

        self.assertEqual(result.http_status, 200)
        self.assertEqual(result.works, [])

    def test_search_raises_on_other_404_bodies(self) -> None:
        connector = OpenFDAConnector()
        not_found = HTTPError(
            url="https://api.fda.gov/food/enforcement.json",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        not_found.read = lambda: b"<html>gateway 404</html>"
        with patch("pit.openfda.urlopen", side_effect=not_found):
            with self.assertRaises(OpenFDARequestError):
                connector.search(
                    query="camu camu pulpa congelada", from_publication_date="2022-01-01", limit=5, target_market="US"
                )


if __name__ == "__main__":
    unittest.main()
