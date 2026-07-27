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
SEARCH_BODY = b'{"ops:searchResult":{"ops:result":[]}}'


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


if __name__ == "__main__":
    unittest.main()
