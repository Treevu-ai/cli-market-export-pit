from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.wits import WITSConnector, WITSRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


# Real SDMX-JSON generic shape confirmed live for reporter=840 (US),
# partner=604 (Peru), product=180610 (cocoa powder): the first element of
# each observation array is the actual SimpleAverage tariff rate (0% here --
# Peru gets a preferential rate under the US-Peru trade agreement), the rest
# are indices into structure.attributes.observation.
TARIFF_BODY = (
    b'{"dataSets":[{"series":{"0:0:0:0:0":{"observations":'
    b'{"0":[0,0,null,0,0,0,0,0,0,0,0,0],"1":[0.5,0,null,0,0,0,0,0,0,0,0,0]}}}}],'
    b'"structure":{"dimensions":{"observation":[{"id":"TIME_PERIOD","values":'
    b'[{"id":"2022","name":"2022"},{"id":"2023","name":"2023"}]}]}}}'
)


class WITSRequestConstructionTests(unittest.TestCase):
    """Regression: WITS uses UN numeric country codes, not alpha-2, and the
    real tariff endpoint requires the /datasource/TRN/reporter/.../partner/...
    path shape -- confirmed live against the actual API with a real
    reporter=840 (US) / partner=604 (Peru) / product=180610 (cocoa powder)
    request."""

    def test_search_builds_correct_url_with_mapped_reporter_and_peru_partner(self) -> None:
        connector = WITSConnector()
        with patch(
            "pit.wits.urlopen", return_value=_fake_response(TARIFF_BODY)
        ) as mocked_urlopen:
            connector.search(target_market="US", hs_code="180610")

        request = mocked_urlopen.call_args[0][0]
        self.assertEqual(
            request.full_url,
            "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/840"
            "/partner/604/product/180610/year/all/datatype/reported?format=JSON",
        )

    def test_search_skips_request_for_unmapped_market(self) -> None:
        connector = WITSConnector()
        with patch("pit.wits.urlopen") as mocked_urlopen:
            result = connector.search(target_market="JP", hs_code="180610")

        mocked_urlopen.assert_not_called()
        self.assertEqual(result.works, [])

    def test_search_skips_request_when_no_hs_code(self) -> None:
        connector = WITSConnector()
        with patch("pit.wits.urlopen") as mocked_urlopen:
            result = connector.search(target_market="US", hs_code=None)

        mocked_urlopen.assert_not_called()
        self.assertEqual(result.works, [])

    def test_search_parses_simple_average_as_first_observation_element(self) -> None:
        connector = WITSConnector()
        with patch("pit.wits.urlopen", return_value=_fake_response(TARIFF_BODY)):
            result = connector.search(target_market="US", hs_code="180610")

        self.assertEqual(len(result.works), 2)
        by_year = {w["year"]: w["simple_average_pct"] for w in result.works}
        self.assertEqual(by_year["2022"], 0)
        self.assertEqual(by_year["2023"], 0.5)

    def test_search_treats_404_no_records_found_as_empty_result(self) -> None:
        connector = WITSConnector()
        not_found = HTTPError(
            url="https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        not_found.read = lambda: b"{}Not Found - NoRecordsFound"
        with patch("pit.wits.urlopen", side_effect=not_found):
            result = connector.search(target_market="US", hs_code="999999")

        self.assertEqual(result.http_status, 200)
        self.assertEqual(result.works, [])

    def test_search_retries_retryable_status_then_raises(self) -> None:
        connector = WITSConnector()
        server_error = HTTPError(
            url="https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=None,
        )
        server_error.read = lambda: b"internal error"
        with patch("pit.wits.urlopen", side_effect=server_error) as mocked_urlopen, patch("pit.wits.time.sleep"):
            with self.assertRaises(WITSRequestError):
                connector.search(target_market="US", hs_code="180610")

        self.assertEqual(mocked_urlopen.call_count, connector.max_retries)

    def test_search_raises_immediately_on_non_retryable_status(self) -> None:
        connector = WITSConnector()
        bad_request = HTTPError(
            url="https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=None,
        )
        bad_request.read = lambda: b"invalid product code"
        with patch("pit.wits.urlopen", side_effect=bad_request) as mocked_urlopen:
            with self.assertRaises(WITSRequestError):
                connector.search(target_market="US", hs_code="180610")

        self.assertEqual(mocked_urlopen.call_count, 1)

    def test_search_sets_a_custom_user_agent(self) -> None:
        """Regression: WITS returns a bare HTTP 403 for any request with no
        User-Agent header at all (Python's default urllib UA) -- confirmed
        live. Any custom User-Agent is enough to get past it."""
        connector = WITSConnector()
        with patch(
            "pit.wits.urlopen", return_value=_fake_response(TARIFF_BODY)
        ) as mocked_urlopen:
            connector.search(target_market="US", hs_code="180610")

        request = mocked_urlopen.call_args[0][0]
        self.assertEqual(request.get_header("User-agent"), "PIT/0.1 research-service")

    def test_search_retries_after_timeout_and_succeeds(self) -> None:
        connector = WITSConnector()
        with patch(
            "pit.wits.urlopen",
            side_effect=[TimeoutError("timed out"), _fake_response(TARIFF_BODY)],
        ) as mocked_urlopen, patch("pit.wits.time.sleep"):
            result = connector.search(target_market="US", hs_code="180610")

        self.assertEqual(mocked_urlopen.call_count, 2)
        self.assertEqual(len(result.works), 2)

    def test_search_raises_wits_error_on_timeout_instead_of_crashing(self) -> None:
        """Regression: WITS occasionally times out via a bare TimeoutError
        (not wrapped in URLError) -- confirmed live -- which would otherwise
        propagate uncaught and crash the whole pipeline run."""
        connector = WITSConnector()
        with patch("pit.wits.urlopen", side_effect=TimeoutError("timed out")), patch("pit.wits.time.sleep"):
            with self.assertRaises(WITSRequestError):
                connector.search(target_market="US", hs_code="180610")


if __name__ == "__main__":
    unittest.main()
