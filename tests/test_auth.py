from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from pit.api import create_app
from pit.research import ResearchService
from pit.storage import ResearchStore


class SuccessfulConnector:
    source = "openalex"
    license_name = "CC0"
    base_url = "https://api.openalex.org"

    def search(self, *, query: str, from_publication_date: str, limit: int):
        from pit.openalex import OpenAlexResponse

        return OpenAlexResponse(
            request_url="https://api.openalex.org/works",
            request_params={"search": query, "per-page": str(limit)},
            http_status=200,
            raw_content=b'{"results":[{"id":"W1"}]}',
            works=[{"id": "W1", "title": "T", "doi": None, "publication_date": "2022-01-01"}],
        )


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["PIT_JWT_SECRET"] = "test-jwt-secret-for-unit-tests-only-32b"
        os.environ["PIT_ADMIN_SECRET"] = "test-admin-secret"
        self._email_patcher = mock.patch("pit.api.email_service.send_verification_email")
        self.mock_send_verification_email = self._email_patcher.start()

    def tearDown(self) -> None:
        self._email_patcher.stop()
        os.environ.pop("PIT_JWT_SECRET", None)
        os.environ.pop("PIT_ADMIN_SECRET", None)

    def _last_verification_token(self) -> str:
        _, kwargs = self.mock_send_verification_email.call_args
        return kwargs["token"]

    def _client(self, directory: str) -> TestClient:
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        service = ResearchService(store, SuccessfulConnector())
        return TestClient(create_app(service))

    def _client_and_store(self, directory: str) -> tuple[TestClient, ResearchStore]:
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        service = ResearchService(store, SuccessfulConnector())
        return TestClient(create_app(service)), store

    def test_signup_creates_free_tier_user_and_returns_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            response = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            self.assertEqual(response.status_code, 201)
            data = response.json()["data"]
            self.assertEqual(data["tier"], "free")
            self.assertTrue(data["token"])

    def test_signup_defaults_to_spanish_locale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            user = store.get_user_by_email("a@b.com")
            self.assertEqual(user["locale"], "es")
            _, kwargs = self.mock_send_verification_email.call_args
            self.assertEqual(kwargs["locale"], "es")

    def test_signup_respects_english_locale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            client.post(
                "/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!", "locale": "en"}
            )
            user = store.get_user_by_email("a@b.com")
            self.assertEqual(user["locale"], "en")
            _, kwargs = self.mock_send_verification_email.call_args
            self.assertEqual(kwargs["locale"], "en")

    def test_resend_verification_uses_stored_locale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            signup = client.post(
                "/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!", "locale": "en"}
            )
            token = signup.json()["data"]["token"]
            client.post("/v1/auth/resend-verification", headers={"Authorization": f"Bearer {token}"})
            _, kwargs = self.mock_send_verification_email.call_args
            self.assertEqual(kwargs["locale"], "en")

    def test_signup_rejects_duplicate_email(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            response = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Otherpass123!"})
            self.assertEqual(response.status_code, 409)

    def test_login_succeeds_with_correct_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            response = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "Testpass123!"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["data"]["token"])

    def test_login_rejects_wrong_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            response = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "Wrongpass123!"})
            self.assertEqual(response.status_code, 401)

    def test_login_rate_limited_after_ten_attempts_from_same_ip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            for _ in range(10):
                response = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "Wrongpass123!"})
                self.assertEqual(response.status_code, 401)
            eleventh = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "Testpass123!"})
            self.assertEqual(eleventh.status_code, 429)

    def test_login_rejects_unknown_email(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            response = client.post("/v1/auth/login", json={"email": "nobody@b.com", "password": "Testpass123!"})
            self.assertEqual(response.status_code, 401)

    def test_login_returns_a_csrf_token_and_cookie_authenticated_requests_require_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            service = ResearchService(store, SuccessfulConnector())
            # Secure cookies are only ever sent by the test transport over
            # https — matches real production, where both apps run behind
            # Fly.io's forced HTTPS.
            client = TestClient(create_app(service), base_url="https://testserver")
            client.post("/v1/auth/signup", json={"email": "csrf@b.com", "password": "Testpass123!"})
            login = client.post("/v1/auth/login", json={"email": "csrf@b.com", "password": "Testpass123!"})
            self.assertEqual(login.status_code, 200)
            # The CSRF token travels in the response body, not a cookie — a
            # cookie set by the backend's origin would be invisible to
            # frontend JS on a different origin (the real production setup),
            # so a real double-submit cookie can't work here. See
            # auth.generate_csrf_token for the stateless HMAC design.
            csrf_token = login.json()["data"]["csrf_token"]
            self.assertTrue(csrf_token)

            # Cookie-authenticated (no Authorization header) POST with no CSRF header is rejected.
            missing_header = client.post("/v1/auth/logout")
            self.assertEqual(missing_header.status_code, 403)

            # Wrong token is rejected too.
            wrong_header = client.post("/v1/auth/logout", headers={"X-CSRF-Token": "not-the-real-token"})
            self.assertEqual(wrong_header.status_code, 403)

            # The real token succeeds.
            ok = client.post("/v1/auth/logout", headers={"X-CSRF-Token": csrf_token})
            self.assertEqual(ok.status_code, 200)

    def test_cookie_authenticated_research_run_creation_requires_csrf_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            service = ResearchService(store, SuccessfulConnector())
            client = TestClient(create_app(service), base_url="https://testserver")
            client.post("/v1/auth/signup", json={"email": "csrf-run@b.com", "password": "Testpass123!"})
            token = self._last_verification_token()
            client.post("/v1/auth/verify", json={"token": token})
            login = client.post("/v1/auth/login", json={"email": "csrf-run@b.com", "password": "Testpass123!"})
            self.assertEqual(login.status_code, 200)
            csrf_token = login.json()["data"]["csrf_token"]

            # Cookie-authenticated (no Authorization header, relying purely on
            # the ambient pit_session cookie) with no CSRF header is rejected —
            # this is the actual attack this dependency defends against.
            no_csrf = client.post("/v1/research-runs", json={"query": "cocoa", "limit": 5})
            self.assertEqual(no_csrf.status_code, 403)

            with_csrf = client.post(
                "/v1/research-runs", json={"query": "cocoa", "limit": 5}, headers={"X-CSRF-Token": csrf_token}
            )
            self.assertEqual(with_csrf.status_code, 201)

    def test_logout_revokes_the_token_that_was_used_to_log_out(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "revoke@b.com", "password": "Testpass123!"})
            login = client.post("/v1/auth/login", json={"email": "revoke@b.com", "password": "Testpass123!"})
            token = login.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}

            still_good = client.get("/v1/auth/me", headers=headers)
            self.assertEqual(still_good.status_code, 200)

            logout = client.post("/v1/auth/logout", headers=headers)
            self.assertEqual(logout.status_code, 200)

            # The exact token that was valid a moment ago must now be dead —
            # logout has to actually kill the session server-side, not just
            # tell the browser to forget its cookie.
            after_logout = client.get("/v1/auth/me", headers=headers)
            self.assertEqual(after_logout.status_code, 401)

    def test_logout_clears_cookies_even_when_the_session_is_already_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            service = ResearchService(store, SuccessfulConnector())
            client = TestClient(create_app(service), base_url="https://testserver")
            client.post("/v1/auth/signup", json={"email": "stale@b.com", "password": "Testpass123!"})
            client.post("/v1/auth/login", json={"email": "stale@b.com", "password": "Testpass123!"})
            self.assertIn("pit_session", client.cookies)

            # Simulate a stale tab: the session token is no longer valid
            # (corrupted here; in practice this would be natural 7-day expiry
            # or a revoked token_version). With no resolvable user, logout
            # skips the CSRF check entirely (there's no user to derive the
            # expected token from) and goes straight to clearing cookies —
            # no X-CSRF-Token header needed for this case at all.
            client.cookies.set("pit_session", "not-a-real-token")

            response = client.post("/v1/auth/logout")
            self.assertEqual(response.status_code, 200)
            # Cookies must still be cleared — a user clicking "log out" on a
            # dead session should never be left with stale cookies. Checked
            # via the raw Set-Cookie header rather than the client-side
            # cookie jar, since httpx's jar reconciliation for a manually
            # injected cookie value isn't representative of real deletion.
            set_cookie_headers = response.headers.get_list("set-cookie")
            self.assertTrue(any("pit_session=" in h and "Max-Age=0" in h for h in set_cookie_headers))

    def test_logout_revokes_every_other_active_session_for_the_account(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "multi-device@b.com", "password": "Testpass123!"})

            # Two independent logins = two independent tokens, as if the same
            # account were signed in on two devices.
            login_a = client.post("/v1/auth/login", json={"email": "multi-device@b.com", "password": "Testpass123!"})
            login_b = client.post("/v1/auth/login", json={"email": "multi-device@b.com", "password": "Testpass123!"})
            token_a = login_a.json()["data"]["token"]
            token_b = login_b.json()["data"]["token"]

            # Logging out with device A's token must also kill device B's
            # session — "log out" means the account is logged out everywhere,
            # not just on the device that clicked it.
            logout = client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
            self.assertEqual(logout.status_code, 200)

            device_b_after = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
            self.assertEqual(device_b_after.status_code, 401)

    def test_me_requires_valid_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            response = client.get("/v1/auth/me")
            self.assertEqual(response.status_code, 401)
            response = client.get("/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
            self.assertEqual(response.status_code, 401)

    def test_me_returns_tier_and_usage_with_valid_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["email"], "a@b.com")
            self.assertEqual(data["tier"], "free")
            self.assertEqual(data["usage"]["used"], 0)
            self.assertEqual(data["usage"]["limit"], 5)

    def test_signup_rate_limited_after_five_attempts_from_same_ip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            for i in range(5):
                response = client.post(
                    "/v1/auth/signup", json={"email": f"user{i}@b.com", "password": "Testpass123!"}
                )
                self.assertEqual(response.status_code, 201)
            response = client.post(
                "/v1/auth/signup", json={"email": "user5@b.com", "password": "Testpass123!"}
            )
            self.assertEqual(response.status_code, 429)

    def test_set_tier_requires_admin_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            response = client.post("/v1/admin/set-tier", json={"email": "a@b.com", "tier": "pro"})
            self.assertEqual(response.status_code, 401)
            response = client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "pro"},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["tier"], "pro")

    def test_signup_sends_verification_email_and_starts_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            self.mock_send_verification_email.assert_called_once()
            _, kwargs = self.mock_send_verification_email.call_args
            self.assertEqual(kwargs["to"], "a@b.com")
            self.assertTrue(kwargs["token"])
            user = store.get_user_by_email("a@b.com")
            self.assertFalse(user["email_verified"])

    def test_verify_email_marks_verified_and_token_cannot_be_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = self._last_verification_token()
            response = client.post("/v1/auth/verify", json={"token": token})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["data"]["email_verified"])
            replay = client.post("/v1/auth/verify", json={"token": token})
            self.assertEqual(replay.status_code, 400)

    def test_verify_email_rejects_unknown_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            response = client.post("/v1/auth/verify", json={"token": "not-a-real-token"})
            self.assertEqual(response.status_code, 400)

    def test_verify_email_rejects_expired_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = self._last_verification_token()
            user = store.get_user_by_email("a@b.com")
            store.set_verification_token(user_id=user["id"], token=token, expires_at="2000-01-01T00:00:00+00:00")
            response = client.post("/v1/auth/verify", json={"token": token})
            self.assertEqual(response.status_code, 400)

    def test_require_quota_blocks_unverified_user_even_with_quota_remaining(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            response = client.post(
                "/v1/research-runs",
                json={"query": "cocoa", "limit": 5},
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["detail"]["code"], "email_not_verified")

    def test_resend_verification_is_noop_when_already_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            verification_token = self._last_verification_token()
            client.post("/v1/auth/verify", json={"token": verification_token})
            response = client.post("/v1/auth/resend-verification", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["data"]["already_verified"])
            self.mock_send_verification_email.assert_called_once()  # not called a second time

    def test_resend_verification_regenerates_token_when_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            first_verification_token = self._last_verification_token()
            response = client.post("/v1/auth/resend-verification", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.mock_send_verification_email.call_count, 2)
            second_verification_token = self._last_verification_token()
            self.assertNotEqual(first_verification_token, second_verification_token)
            # the old token is invalidated once a new one is issued
            self.assertEqual(client.post("/v1/auth/verify", json={"token": first_verification_token}).status_code, 400)
            self.assertEqual(client.post("/v1/auth/verify", json={"token": second_verification_token}).status_code, 200)

    def test_resend_verification_rate_limited_after_three_attempts_per_hour(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            for _ in range(3):
                response = client.post("/v1/auth/resend-verification", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(response.status_code, 200)
            fourth = client.post("/v1/auth/resend-verification", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(fourth.status_code, 429)

    def test_new_signup_is_not_falsely_grandfathered_by_reinitialize(self) -> None:
        # Regression test: verification_token is now set in the SAME insert as
        # user creation (create_user), so a fresh signup can never be observed
        # with a NULL token — re-running initialize() (as happens on every
        # process boot) must not flip it to verified.
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            store.initialize()
            user = store.get_user_by_email("a@b.com")
            self.assertFalse(user["email_verified"])
            self.assertIsNotNone(user["verification_token"])

    def test_set_tier_applies_default_and_custom_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            default_expiry = client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "pro"},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            self.assertIsNotNone(default_expiry.json()["data"]["tier_expires_at"])

            custom_expiry = client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "pro", "expires_in_days": 7},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            self.assertIsNotNone(custom_expiry.json()["data"]["tier_expires_at"])

            back_to_free = client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "free"},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            self.assertIsNone(back_to_free.json()["data"]["tier_expires_at"])

    def test_expired_pro_tier_auto_downgrades_to_free_on_next_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            user = store.get_user_by_email("a@b.com")
            store.set_user_tier(user["id"], "pro", expires_at="2000-01-01T00:00:00+00:00")
            response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["tier"], "free")
            self.assertIsNone(data["tier_expires_at"])

    def test_active_pro_tier_is_not_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, store = self._client_and_store(directory)
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "Testpass123!"})
            token = signup.json()["data"]["token"]
            user = store.get_user_by_email("a@b.com")
            store.set_user_tier(user["id"], "pro", expires_at="2999-01-01T00:00:00+00:00")
            response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.json()["data"]["tier"], "pro")


if __name__ == "__main__":
    unittest.main()
