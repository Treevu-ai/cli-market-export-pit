from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.epo_ops import EPOOPSConnector, EPOOPSRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


TOKEN_BODY = b'{"access_token":"token-1","expires_in":"1199"}'
# Real shape confirmed live -- ops:searchResult/ops:result (camelCase)
# never existed on the actual API.
SEARCH_BODY = (
    b'{"ops:world-patent-data":{"ops:biblio-search":{"ops:search-result":'
    b'{"ops:publication-reference":[{"@family-id":"123","document-id":'
    b'{"country":{"$":"EP"},"doc-number":{"$":"4781832"},"kind":{"$":"A1"}}}]}}}}'
)


class EPOOPSTokenExpiryTests(unittest.TestCase):
    """Regression: the access token used to be cached forever with no expiry
    tracking, so the patent domain would fail silently ~20min after startup
    once EPO's real token expired, until the process was restarted."""

    def test_get_access_token_is_cached_within_ttl(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        with patch("pit.epo_ops.urlopen", return_value=_fake_response(TOKEN_BODY)) as mocked_urlopen:
            token_1 = connector._get_access_token()
            clock.advance(60)
            token_2 = connector._get_access_token()

        self.assertEqual(token_1, "token-1")
        self.assertEqual(token_2, "token-1")
        self.assertEqual(mocked_urlopen.call_count, 1)

    def test_get_access_token_refreshes_after_ttl_expires(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[
                _fake_response(TOKEN_BODY),
                _fake_response(b'{"access_token":"token-2","expires_in":"1199"}'),
            ],
        ) as mocked_urlopen:
            connector._get_access_token()
            clock.advance(1200)  # past expires_in, well past the safety margin too
            token_2 = connector._get_access_token()

        self.assertEqual(token_2, "token-2")
        self.assertEqual(mocked_urlopen.call_count, 2)

    def test_search_refreshes_expired_token_and_retries_once_on_401(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        unauthorized = HTTPError(
            url="https://ops.epo.org/3.2/rest-services/search",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        unauthorized.read = lambda: b'{"error":"access_token_expired"}'
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[
                _fake_response(TOKEN_BODY),  # initial token fetch
                unauthorized,  # search call with the (now server-side expired) token
                _fake_response(b'{"access_token":"token-2","expires_in":"1199"}'),  # forced refresh
                _fake_response(SEARCH_BODY),  # retried search call succeeds
                _fake_response(b'{"ops:world-patent-data":{"exchange-documents":{"exchange-document":[]}}}'),  # biblio
            ],
        ):
            connector._get_access_token()  # warm the cache, as a long-lived process would have
            response = connector.search(query="cocoa", from_publication_date="2021-01-01", limit=10)

        self.assertEqual(response.http_status, 200)
        self.assertEqual(connector._access_token, "token-2")

    def test_search_raises_if_still_unauthorized_after_refresh(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        unauthorized = HTTPError(
            url="https://ops.epo.org/3.2/rest-services/search",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        unauthorized.read = lambda: b'{"error":"invalid_client"}'
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[
                _fake_response(TOKEN_BODY),
                unauthorized,
                _fake_response(b'{"access_token":"token-2","expires_in":"1199"}'),
                unauthorized,
            ],
        ):
            connector._get_access_token()
            with self.assertRaises(EPOOPSRequestError):
                connector.search(query="cocoa", from_publication_date="2021-01-01", limit=10)


class EPOOPSSearchRequestConstructionTests(unittest.TestCase):
    """Regression: base_url was /3.2/rest-services/search (404 -- the real
    published-data search path has an extra /published-data/ segment),
    range/rows/format were never real query params (400
    CLIENT.InvalidQuery -- pagination is the X-OPS-Range header and date
    filtering is CQL embedded in `q`), and quoting the search term
    (txt="x") or an open-ended date bound (...-30001231) both caused a
    genuine EPO-side 500 -- all confirmed live with a real subscription."""

    def test_search_builds_correct_path_cql_query_and_range_header(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[
                _fake_response(TOKEN_BODY),
                _fake_response(SEARCH_BODY),
                _fake_response(b'{"ops:world-patent-data":{"exchange-documents":{"exchange-document":[]}}}'),
            ],
        ) as mocked_urlopen:
            connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        search_request = mocked_urlopen.call_args_list[1][0][0]
        self.assertTrue(
            search_request.full_url.startswith(
                "https://ops.epo.org/3.2/rest-services/published-data/search?"
            )
        )
        # Unquoted term -- quoting it is what caused the live 500.
        self.assertIn("txt%3Dblueberry", search_request.full_url)
        self.assertIn("pd+within", search_request.full_url.replace("%20", "+"))
        self.assertNotIn("range=", search_request.full_url)
        self.assertNotIn("rows=", search_request.full_url)
        self.assertEqual(search_request.get_header("X-ops-range"), "1-5")

    def test_search_parses_publication_reference_without_requiring_title(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[
                _fake_response(TOKEN_BODY),
                _fake_response(SEARCH_BODY),
                _fake_response(b'{"ops:world-patent-data":{"exchange-documents":{"exchange-document":[]}}}'),
            ],
        ):
            result = connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(len(result.works), 1)
        self.assertEqual(result.works[0]["patent_number"], "EP4781832A1")
        self.assertEqual(result.works[0]["family_id"], "123")


# Real shape confirmed live against
# .../publication/docdb/EP.4781832.A1/biblio -- title is repeated once per
# language, applicant/inventor names appear twice (epodoc + original
# data-format), and IPC text carries irregular fixed-width padding.
BIBLIO_BODY = (
    b'{"ops:world-patent-data":{"exchange-documents":{"exchange-document":'
    b'[{"@country":"EP","@doc-number":"4781832","@kind":"A1","bibliographic-data":'
    b'{"invention-title":[{"@lang":"de","$":"STABILISIERTE"},'
    b'{"@lang":"en","$":"STABILIZED OIL-BASED MICROPARTICLES"}],'
    b'"classifications-ipcr":{"classification-ipcr":'
    b'[{"text":{"$":"A23D   7/   005            A I"}}]},'
    b'"parties":{"applicants":{"applicant":'
    b'[{"@data-format":"epodoc","applicant-name":{"name":{"$":"CUBIQ FOODS S L [ES]"}}},'
    b'{"@data-format":"original","applicant-name":{"name":{"$":"Cubiq Foods, S.L."}}}]}},'
    b'"publication-reference":{"document-id":'
    b'[{"date":{"$":"20260415"}}]}}}]}}}'
)


class EPOOPSBiblioEnrichmentTests(unittest.TestCase):
    """Confirmed live: the /search endpoint never carries title/applicant/IPC
    data, but a follow-up batch call to the /biblio endpoint (comma-separated
    docdb ids in one request) does. search() should enrich each bare result
    with real title/assignees/ipc_codes/publication_date, and must not fail
    the whole search if biblio enrichment errors out."""

    def test_search_enriches_results_with_biblio_details(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[_fake_response(TOKEN_BODY), _fake_response(SEARCH_BODY), _fake_response(BIBLIO_BODY)],
        ) as mocked_urlopen:
            result = connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        biblio_request = mocked_urlopen.call_args_list[2][0][0]
        self.assertTrue(
            biblio_request.full_url.startswith(
                "https://ops.epo.org/3.2/rest-services/published-data/publication/docdb/EP.4781832.A1/biblio"
            )
        )
        work = result.works[0]
        self.assertEqual(work["title"], "STABILIZED OIL-BASED MICROPARTICLES")
        self.assertEqual(work["assignees"], ["CUBIQ FOODS S L [ES]", "Cubiq Foods, S.L."])
        self.assertEqual(work["ipc_codes"], ["A23D 7/ 005 A I"])
        self.assertEqual(work["publication_date"], "20260415")

    def test_search_keeps_bare_results_if_biblio_call_fails(self) -> None:
        clock = FakeClock()
        connector = EPOOPSConnector("key", "secret", time_func=clock)
        biblio_error = HTTPError(
            url="https://ops.epo.org/3.2/rest-services/published-data/publication/docdb/EP.4781832.A1/biblio",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=None,
        )
        biblio_error.read = lambda: b'{"error":"internal"}'
        with patch(
            "pit.epo_ops.urlopen",
            side_effect=[_fake_response(TOKEN_BODY), _fake_response(SEARCH_BODY), biblio_error],
        ):
            result = connector.search(query="blueberry", from_publication_date="2020-01-01", limit=5)

        self.assertEqual(len(result.works), 1)
        self.assertEqual(result.works[0]["patent_number"], "EP4781832A1")
        self.assertEqual(result.works[0]["title"], "")


if __name__ == "__main__":
    unittest.main()
