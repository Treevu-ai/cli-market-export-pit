from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

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

    def tearDown(self) -> None:
        os.environ.pop("PIT_JWT_SECRET", None)
        os.environ.pop("PIT_ADMIN_SECRET", None)

    def _client(self, directory: str) -> TestClient:
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        service = ResearchService(store, SuccessfulConnector())
        return TestClient(create_app(service))

    def test_signup_creates_free_tier_user_and_returns_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            response = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "testpass123"})
            self.assertEqual(response.status_code, 201)
            data = response.json()["data"]
            self.assertEqual(data["tier"], "free")
            self.assertTrue(data["token"])

    def test_signup_rejects_duplicate_email(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "testpass123"})
            response = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "otherpass123"})
            self.assertEqual(response.status_code, 409)

    def test_login_succeeds_with_correct_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "testpass123"})
            response = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "testpass123"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["data"]["token"])

    def test_login_rejects_wrong_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "testpass123"})
            response = client.post("/v1/auth/login", json={"email": "a@b.com", "password": "wrongpass123"})
            self.assertEqual(response.status_code, 401)

    def test_login_rejects_unknown_email(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            response = client.post("/v1/auth/login", json={"email": "nobody@b.com", "password": "testpass123"})
            self.assertEqual(response.status_code, 401)

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
            signup = client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "testpass123"})
            token = signup.json()["data"]["token"]
            response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["email"], "a@b.com")
            self.assertEqual(data["tier"], "free")
            self.assertEqual(data["usage"]["used"], 0)
            self.assertEqual(data["usage"]["limit"], 5)

    def test_set_tier_requires_admin_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = self._client(directory)
            client.post("/v1/auth/signup", json={"email": "a@b.com", "password": "testpass123"})
            response = client.post("/v1/admin/set-tier", json={"email": "a@b.com", "tier": "pro"})
            self.assertEqual(response.status_code, 401)
            response = client.post(
                "/v1/admin/set-tier",
                json={"email": "a@b.com", "tier": "pro"},
                headers={"X-Admin-Secret": "test-admin-secret"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["data"]["tier"], "pro")


if __name__ == "__main__":
    unittest.main()
