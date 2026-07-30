from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pit.cordis import CORDISConnector


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


# Real shape confirmed live via cordis.europa.eu's own /api/search/results
# calls (captured with a real browser session, no API key required).
SEARCH_BODY = (
    b'{"status":true,"payload":{"total":47,"page":1,"results":'
    b'[{"reference":"708362","id":"708362","acronym":"DIET-SEX-GENOMICS",'
    b'"startDate":"1 {{month_07}} 2016","endDate":"30 {{month_06}} 2018",'
    b'"coordinatedIn":"United Kingdom","contentType":"project",'
    b'"title":"Linking genotype to phenotype - Role of diet on sex-specific reproduction"},'
    b'{"reference":"717034","id":"717034","acronym":"TKI resistance",'
    b'"startDate":"1 {{month_12}} 2010","endDate":"30 {{month_11}} 2012",'
    b'"coordinatedIn":"France","contentType":"project",'
    b'"title":"Resistance mechanisms to tyrosine kinase inhibitors in solid tumors"}]}}'
)


class CORDISRequestConstructionTests(unittest.TestCase):
    """Regression: base_url was /api/search (404 -- the site's SPA shell,
    not a real endpoint). The real endpoint is /api/search/results and
    filters to funded projects via a `contenttype='project'` clause in the
    Lucene-style `q` param -- both confirmed live by reproducing the exact
    calls the CORDIS website itself makes."""

    def test_search_builds_correct_path_and_project_filter(self) -> None:
        connector = CORDISConnector()
        with patch(
            "pit.cordis.urlopen", return_value=_fake_response(SEARCH_BODY)
        ) as mocked_urlopen:
            connector.search(query="camu camu", from_publication_date="2005-01-01", limit=5)

        request = mocked_urlopen.call_args[0][0]
        self.assertTrue(request.full_url.startswith("https://cordis.europa.eu/api/search/results?"))
        self.assertIn("contenttype%3D%27project%27", request.full_url)
        self.assertIn("%27camu%27+AND+%27camu%27", request.full_url.replace("%20", "+"))

    def test_search_parses_project_previews(self) -> None:
        connector = CORDISConnector()
        with patch("pit.cordis.urlopen", return_value=_fake_response(SEARCH_BODY)):
            result = connector.search(query="camu camu", from_publication_date="2005-01-01", limit=5)

        self.assertEqual(len(result.works), 2)
        work = result.works[0]
        self.assertEqual(work["project_id"], "708362")
        self.assertEqual(work["title"], "Linking genotype to phenotype - Role of diet on sex-specific reproduction")
        self.assertIsNone(work["funding_amount"])
        self.assertEqual(work["organizations"], [])

    def test_search_filters_out_projects_older_than_from_date(self) -> None:
        connector = CORDISConnector()
        with patch("pit.cordis.urlopen", return_value=_fake_response(SEARCH_BODY)):
            result = connector.search(query="camu camu", from_publication_date="2015-01-01", limit=5)

        # Only DIET-SEX-GENOMICS (2016) survives the 2015 cutoff; TKI
        # resistance (2010) does not.
        self.assertEqual(len(result.works), 1)
        self.assertEqual(result.works[0]["project_id"], "708362")


if __name__ == "__main__":
    unittest.main()
