from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pit.lex_api import LexAPIConnector, LexAPIRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


SEARCH_BODY = (
    b'{"results":[{"celexNumber":"32016R0679","title":"Regulation (EU) 2016/679",'
    b'"documentType":"Regulation","dateOfDocument":"27/04/2016",'
    b'"url":"https://eur-lex.europa.eu/eli/reg/2016/679/oj"}]}'
)


class LexAPIConnectorTests(unittest.TestCase):
    def test_search_sends_api_key_header_and_json_body(self) -> None:
        connector = LexAPIConnector(api_key="lex_live_test")
        with patch("pit.lex_api.urlopen", return_value=_fake_response(SEARCH_BODY)) as mocked_urlopen:
            connector.search(query="mango import requirements", from_publication_date="2021-01-01", limit=5)

        request = mocked_urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://lex-api.com/api/v1/search")
        self.assertEqual(request.get_header("X-api-key"), "lex_live_test")
        self.assertEqual(request.get_method(), "POST")

    def test_search_parses_celex_and_title_fields(self) -> None:
        connector = LexAPIConnector(api_key="lex_live_test")
        with patch("pit.lex_api.urlopen", return_value=_fake_response(SEARCH_BODY)):
            result = connector.search(query="food safety", from_publication_date="2021-01-01", limit=5)

        self.assertEqual(len(result.works), 1)
        work = result.works[0]
        self.assertEqual(work["celex_number"], "32016R0679")
        self.assertEqual(work["title"], "Regulation (EU) 2016/679")
        self.assertEqual(work["date"], "27/04/2016")

    def test_search_raises_without_api_key(self) -> None:
        connector = LexAPIConnector(api_key=None)
        with self.assertRaises(RuntimeError):
            connector.search(query="mango", from_publication_date="2021-01-01", limit=5)

    def test_search_surfaces_credit_exhaustion_as_402(self) -> None:
        connector = LexAPIConnector(api_key="lex_live_test")
        error = __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(
            url="https://lex-api.com/api/v1/search", code=402, msg="Payment Required", hdrs=None, fp=None
        )
        error.read = lambda: b'{"error":"credits exhausted"}'
        with patch("pit.lex_api.urlopen", side_effect=error):
            with self.assertRaises(LexAPIRequestError) as ctx:
                connector.search(query="mango", from_publication_date="2021-01-01", limit=5)
        self.assertEqual(ctx.exception.http_status, 402)
        self.assertIn("credit", str(ctx.exception).lower())

    def test_search_raises_on_timeout_instead_of_crashing(self) -> None:
        connector = LexAPIConnector(api_key="lex_live_test")
        with patch("pit.lex_api.urlopen", side_effect=TimeoutError("timed out")):
            with self.assertRaises(LexAPIRequestError):
                connector.search(query="mango", from_publication_date="2021-01-01", limit=5)


if __name__ == "__main__":
    unittest.main()
