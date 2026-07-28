from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from pit.api import create_app
from pit.openalex import OpenAlexResponse
from pit.research import ResearchService
from pit.storage import ResearchStore


class SuccessfulConnector:
    source = "openalex"
    license_name = "CC0"
    base_url = "https://api.openalex.org"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> OpenAlexResponse:
        return OpenAlexResponse(
            request_url="https://api.openalex.org/works",
            request_params={"search": query, "per-page": str(limit)},
            http_status=200,
            raw_content=b'{"results":[{"id":"W1"}]}',
            works=[{"id": "W1", "title": "T", "doi": None, "publication_date": "2022-01-01"}],
        )


class UsageLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["PIT_JWT_SECRET"] = "test-jwt-secret-for-unit-tests-only-32b"
        os.environ["PIT_ADMIN_SECRET"] = "test-admin-secret"
        self._email_patcher = mock.patch("pit.api.email_service.send_verification_email")
        self.mock_send_verification_email = self._email_patcher.start()

    def tearDown(self) -> None:
        self._email_patcher.stop()
        os.environ.pop("PIT_JWT_SECRET", None)
        os.environ.pop("PIT_ADMIN_SECRET", None)

    def _client_and_token(self, directory: str, email: str = "a@b.com") -> tuple[TestClient, str]:
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        service = ResearchService(store, SuccessfulConnector())
        client = TestClient(create_app(service))
        signup = client.post("/v1/auth/signup", json={"email": email, "password": "Testpass123!"})
        _, kwargs = self.mock_send_verification_email.call_args
        client.get(f"/v1/auth/verify?token={kwargs['token']}")
        return client, signup.json()["data"]["token"]

    def _run(self, client: TestClient, token: str):
        return client.post(
            "/v1/research-runs",
            json={"query": "cocoa", "limit": 5},
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_free_tier_blocks_after_five_runs_in_same_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, token = self._client_and_token(directory)
            for i in range(5):
                response = self._run(client, token)
                self.assertEqual(response.status_code, 201, f"run {i} should succeed")
            sixth = self._run(client, token)
            self.assertEqual(sixth.status_code, 402)
            detail = sixth.json()["detail"]
            self.assertEqual(detail["tier"], "free")
            self.assertEqual(detail["limit"], 5)
            self.assertEqual(detail["upgrade_url"], "/pricing")

    def test_pro_tier_allows_more_than_free_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, token = self._client_and_token(directory)
            client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "pro"},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            for i in range(6):
                response = self._run(client, token)
                self.assertEqual(response.status_code, 201, f"pro run {i} should succeed past the free limit")

    def test_enterprise_tier_is_unlimited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, token = self._client_and_token(directory)
            client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "enterprise"},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            for i in range(10):
                response = self._run(client, token)
                self.assertEqual(response.status_code, 201, f"enterprise run {i} should always succeed")

    def test_two_users_have_independent_quotas(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client, token_a = self._client_and_token(directory, email="a@b.com")
            signup_b = client.post("/v1/auth/signup", json={"email": "b@b.com", "password": "Testpass123!"})
            token_b = signup_b.json()["data"]["token"]
            _, kwargs_b = self.mock_send_verification_email.call_args
            client.get(f"/v1/auth/verify?token={kwargs_b['token']}")
            for _ in range(5):
                self.assertEqual(self._run(client, token_a).status_code, 201)
            self.assertEqual(self._run(client, token_a).status_code, 402)
            # user b's quota is untouched by user a's usage
            self.assertEqual(self._run(client, token_b).status_code, 201)


if __name__ == "__main__":
    unittest.main()
