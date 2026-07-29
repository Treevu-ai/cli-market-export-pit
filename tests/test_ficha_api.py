from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from test_research import SuccessfulConnector

from pit.api import create_app
from pit.reports import ReportGenerator
from pit.research import ResearchService
from pit.scoring import ScoringService
from pit.storage import ResearchStore


class FichaApiTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["PIT_JWT_SECRET"] = "test-jwt-secret-for-unit-tests-only-32b"

    def tearDown(self) -> None:
        os.environ.pop("PIT_JWT_SECRET", None)

    def _client_with_run(self) -> tuple[TestClient, str, str]:
        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        service = ResearchService(store, SuccessfulConnector())
        scoring = ScoringService(store)
        client = TestClient(create_app(service, scoring, ReportGenerator()))
        with patch("pit.api.email_service.send_verification_email"):
            signup = client.post(
                "/v1/auth/signup", json={"email": "ficha@example.com", "password": "Testpass123!"}
            )
        token = signup.json()["data"]["token"]
        owner = store.get_user_by_email("ficha@example.com")
        client.post("/v1/auth/verify", json={"token": owner['verification_token']})
        run = service.run_science_research(
            user_id=owner["id"],
            query="mango organico",
            target_market="US",
            application="exportacion agroindustrial",
            cutoff_at="2026-07-27T00:00:00+00:00",
            from_publication_date="2021-01-01",
            limit=5,
        )
        scoring.calculate_scores(run["id"])
        return client, run["id"], token


class AgentsStatusTests(FichaApiTests):
    def test_agents_status_returns_payload(self) -> None:
        client, _, _ = self._client_with_run()
        response = client.get("/v1/agents/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("data", body)
        self.assertIn("ficha_available", body["data"])
        self.assertIn("anthropic_configured", body["data"])


class FichaEndpointTests(FichaApiTests):
    def test_ficha_returns_404_for_unknown_run(self) -> None:
        client, _, token = self._client_with_run()
        with patch(
            "pit_agents.product_intelligence.ficha_service.agents_dependencies_ready",
            return_value=(True, None),
        ):
            response = client.post(
                "/v1/research-runs/rr_missing/ficha",
                json={"segment": "retail", "stage": "concepto"},
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 404)

    def test_ficha_returns_503_when_agents_unavailable(self) -> None:
        client, run_id, token = self._client_with_run()
        with patch(
            "pit_agents.product_intelligence.ficha_service.agents_dependencies_ready",
            return_value=(False, "OPENAI_API_KEY no esta configurada en el servidor."),
        ):
            response = client.post(
                f"/v1/research-runs/{run_id}/ficha",
                json={"segment": "retail", "stage": "concepto"},
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_ficha_returns_dossier_when_agents_ready(self) -> None:
        client, run_id, token = self._client_with_run()
        mock_result = {
            "run_id": run_id,
            "dossier_markdown": "# Ficha de oportunidad\n\nContenido de prueba.",
            "pit_recommendation": "Validate",
            "pit_opportunity_score": 55.0,
            "segment": "retail",
            "stage": "concepto",
        }
        with patch(
            "pit_agents.product_intelligence.ficha_service.agents_dependencies_ready",
            return_value=(True, None),
        ), patch(
            "pit_agents.product_intelligence.ficha_service.generate_dossier_for_run",
            new=AsyncMock(return_value=mock_result),
        ):
            response = client.post(
                f"/v1/research-runs/{run_id}/ficha",
                json={"segment": "retail", "stage": "concepto"},
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["dossier_markdown"], mock_result["dossier_markdown"])
        self.assertEqual(body["meta"]["pit_run_id"], run_id)


if __name__ == "__main__":
    unittest.main()
