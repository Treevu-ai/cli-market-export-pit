from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pit.climatiq import ClimatiqConnector


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


SEARCH_BODY = (
    b'{"current_page":1,"last_page":1,"total_results":1,"results":'
    b'[{"id":"ff8d4531","activity_id":"food-type_blueberries_raw","name":"Blueberry (raw)",'
    b'"category":"Food Production","unit":"kg/kg","factor":0.42}]}'
)


class ClimatiqRequestConstructionTests(unittest.TestCase):
    """Regression: base_url was /v2/search (404 -- never a real endpoint,
    the API key itself was already valid) and the parser read a top-level
    `data` key with a `co2e_factor` field, neither of which the real API
    returns. Confirmed live: the real endpoint is /data/v1/search, requires
    a data_version param, and nests hits under `results` with a `factor`
    field."""

    def test_search_builds_correct_url_with_data_version(self) -> None:
        connector = ClimatiqConnector(api_key="test-key")
        with patch("pit.climatiq.urlopen", return_value=_fake_response(SEARCH_BODY)) as mocked_urlopen:
            connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        request = mocked_urlopen.call_args[0][0]
        self.assertTrue(request.full_url.startswith("https://api.climatiq.io/data/v1/search?"))
        self.assertIn("data_version=", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")

    def test_search_parses_results_key_and_factor_field(self) -> None:
        connector = ClimatiqConnector(api_key="test-key")
        with patch("pit.climatiq.urlopen", return_value=_fake_response(SEARCH_BODY)):
            result = connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(len(result.works), 1)
        work = result.works[0]
        self.assertEqual(work["name"], "Blueberry (raw)")
        self.assertEqual(work["co2e_factor"], 0.42)


if __name__ == "__main__":
    unittest.main()
