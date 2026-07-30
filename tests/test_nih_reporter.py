from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from pit.nih_reporter import NIHReporterConnector


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class NIHReporterRequestConstructionTests(unittest.TestCase):
    """Regression: search() sent a GET with query-string params, but NIH
    RePORTER's v2 API is POST-only with a JSON criteria body -- every call
    returned HTTP 405 (Method Not Allowed)."""

    def test_search_sends_post_with_json_criteria_body(self) -> None:
        connector = NIHReporterConnector()
        with patch("pit.nih_reporter.urlopen", return_value=_fake_response(b'{"results":[]}')) as mocked_urlopen:
            connector.search(query="blueberry", from_publication_date="2020-01-01", limit=10)

        request = mocked_urlopen.call_args[0][0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, connector.base_url)
        body = json.loads(request.data)
        self.assertEqual(body["criteria"]["advanced_text_search"]["search_text"], "blueberry")
        self.assertEqual(body["criteria"]["project_start_date"]["from_date"], "2020-01-01")
        self.assertEqual(body["limit"], 10)


if __name__ == "__main__":
    unittest.main()
