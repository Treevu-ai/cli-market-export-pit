from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.gdelt import GDELTConnector, GDELTRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def _http_error(code: int, body: bytes = b"{}"):
    error = HTTPError(url="https://api.gdeltproject.org/api/v2/doc/doc", code=code, msg="err", hdrs=None, fp=None)
    error.read = MagicMock(return_value=body)
    return error


ARTLIST_BODY = b'{"articles":[{"url":"https://x.com/a","title":"A","date":"20260101"}]}'


class GDELTRetryTests(unittest.TestCase):
    """Regression: search() used to have zero retry -- a single 429/5xx
    aborted the whole domain with no attempt to recover, unlike
    semanticscholar.py's proven backoff pattern."""

    def test_search_retries_after_429_and_succeeds(self) -> None:
        connector = GDELTConnector()
        with patch(
            "pit.gdelt.urlopen",
            side_effect=[_http_error(429), _fake_response(ARTLIST_BODY)],
        ), patch("pit.gdelt.time.sleep") as mocked_sleep:
            result = connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(len(result.works), 1)
        mocked_sleep.assert_called_once()

    def test_search_raises_immediately_on_non_retryable_status(self) -> None:
        connector = GDELTConnector()
        with patch("pit.gdelt.urlopen", side_effect=_http_error(404)) as mocked_urlopen:
            with self.assertRaises(GDELTRequestError) as ctx:
                connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(ctx.exception.http_status, 404)
        self.assertEqual(mocked_urlopen.call_count, 1)

    def test_search_raises_gdelt_error_on_timeout_instead_of_crashing(self) -> None:
        """Regression: urlopen's socket timeout surfaces as a bare
        TimeoutError, not wrapped in URLError -- confirmed live (this exact
        exception escaped every connector's except clause and crashed a
        real production pipeline run). Applied the same fix across all 17
        connectors; this is the representative regression test."""
        connector = GDELTConnector()
        with patch("pit.gdelt.urlopen", side_effect=TimeoutError("timed out")), patch("pit.gdelt.time.sleep"):
            with self.assertRaises(GDELTRequestError):
                connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

    def test_search_gives_up_after_max_retries(self) -> None:
        connector = GDELTConnector()
        with patch(
            "pit.gdelt.urlopen",
            side_effect=[_http_error(429), _http_error(429), _http_error(429)],
        ) as mocked_urlopen, patch("pit.gdelt.time.sleep"):
            with self.assertRaises(GDELTRequestError) as ctx:
                connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(ctx.exception.http_status, 429)
        self.assertEqual(mocked_urlopen.call_count, connector.max_retries)


if __name__ == "__main__":
    unittest.main()
