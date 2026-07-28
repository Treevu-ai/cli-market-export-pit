from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pit.bcrp import BCRPConnector, BCRPRequestError


def _fake_response(body: bytes, status: int = 200):
    response = MagicMock()
    response.read.return_value = body
    response.status = status
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


# Shape verified live against estadisticas.bcrp.gob.pe for series PN01207PM.
_REAL_SHAPE_BODY = (
    b'{"config":{"series":[{"name":"Tipo de cambio - promedio del periodo '
    b'(soles por dolar) - Interbancario - Promedio","dec":"3"}]},'
    b'"periods":[{"name":"Ene.2026","values":["3.356115"]},'
    b'{"name":"Feb.2026","values":["3.35664"]}]}'
)


class BCRPConnectorTests(unittest.TestCase):
    def test_search_normalizes_works_from_real_shaped_payload(self) -> None:
        connector = BCRPConnector()
        with patch("pit.bcrp.urlopen", return_value=_fake_response(_REAL_SHAPE_BODY)):
            response = connector.search(months_back=1)

        self.assertEqual(response.http_status, 200)
        self.assertEqual(len(response.works), 2)
        first = response.works[0]
        self.assertEqual(first["series_code"], "PN01207PM")
        self.assertEqual(first["period"], "Ene.2026")
        self.assertEqual(first["value"], "3.356115")
        self.assertEqual(first["external_id"], "bcrp:PN01207PM:Ene.2026")
        self.assertEqual(first["source"], "bcrp")

    def test_search_builds_url_with_default_series_and_date_range(self) -> None:
        connector = BCRPConnector()
        with patch("pit.bcrp.urlopen", return_value=_fake_response(_REAL_SHAPE_BODY)) as mocked_urlopen:
            response = connector.search(months_back=1)

        called_request = mocked_urlopen.call_args[0][0]
        self.assertIn("/estadisticas/series/api/PN01207PM/json/", called_request.full_url)
        self.assertEqual(called_request.full_url, response.request_url)

    def test_search_joins_multiple_series_codes_with_hyphen(self) -> None:
        connector = BCRPConnector()
        with patch("pit.bcrp.urlopen", return_value=_fake_response(_REAL_SHAPE_BODY)) as mocked_urlopen:
            connector.search(series_codes=["PN01207PM", "PN01288PM"], months_back=1)

        called_request = mocked_urlopen.call_args[0][0]
        self.assertIn("/api/PN01207PM-PN01288PM/json/", called_request.full_url)

    def test_search_http_error_raises_bcrp_request_error(self) -> None:
        connector = BCRPConnector()
        http_error = HTTPError(
            url="https://estadisticas.bcrp.gob.pe/estadisticas/series/api/BAD/json/2026-1/2026-2",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        http_error.read = lambda: b"not found"
        with patch("pit.bcrp.urlopen", side_effect=http_error):
            with self.assertRaises(BCRPRequestError) as raised:
                connector.search(months_back=1)

        self.assertEqual(raised.exception.http_status, 404)

    def test_search_invalid_json_raises_bcrp_request_error(self) -> None:
        # BCRP returns an HTML/WAF challenge page (not a clean JSON error) for
        # unrecognized series codes.
        connector = BCRPConnector()
        html_body = b"<html><body>Incapsula challenge</body></html>"
        with patch("pit.bcrp.urlopen", return_value=_fake_response(html_body)):
            with self.assertRaises(BCRPRequestError):
                connector.search(months_back=1)


if __name__ == "__main__":
    unittest.main()
