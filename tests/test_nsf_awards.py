from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pit.nsf_awards import NSFAwardsConnector


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


AWARD_BODY = (
    b'{"response":{"award":[{"id":"123","title":"Blueberry study","startDate":"01/01/2020",'
    b'"expDate":"01/01/2022","fundsObligatedAmt":"50000","awardeeName":"Some University",'
    b'"pdPIName":"Jane Doe"}]}}'
)


class NSFAwardsRequestConstructionTests(unittest.TestCase):
    """Regression: base_url was /awards/search?format=json (HTTP 404 --
    not a real NSF route) and startDate/endDate/limit are rejected param
    names (AwardAPI-002); the real path is /awards.json with dateStart/
    dateEnd (MM/DD/YYYY) and rpp. Response awards are nested under
    response.award, and funding/organization fields use different keys
    than what the parser originally read."""

    def test_search_builds_correct_url_and_param_names(self) -> None:
        connector = NSFAwardsConnector()
        with patch("pit.nsf_awards.urlopen", return_value=_fake_response(AWARD_BODY)) as mocked_urlopen:
            connector.search(query="blueberry", from_publication_date="2020-01-01", limit=30)

        request = mocked_urlopen.call_args[0][0]
        self.assertTrue(request.full_url.startswith("https://api.nsf.gov/services/v1/awards.json?"))
        self.assertNotIn("format=", request.full_url)
        self.assertIn("dateStart=01%2F01%2F2020", request.full_url)
        self.assertIn("rpp=25", request.full_url)  # capped at 25, not the requested 30

    def test_search_parses_nested_response_and_correct_field_names(self) -> None:
        connector = NSFAwardsConnector()
        with patch("pit.nsf_awards.urlopen", return_value=_fake_response(AWARD_BODY)):
            result = connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(len(result.works), 1)
        work = result.works[0]
        self.assertEqual(work["title"], "Blueberry study")
        self.assertEqual(work["funding_amount"], "50000")
        self.assertEqual(work["organizations"], ["Some University", "Jane Doe"])


if __name__ == "__main__":
    unittest.main()
