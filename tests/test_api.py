"""
Integration test for the FastAPI /screen endpoint.

Uses httpx TestClient. The actual LLM calls are NOT mocked here —
this test is only runnable with a valid GEMINI_API_KEY and is
intended for manual validation, not CI.

Run with:
    pytest tests/test_api.py -v -s
"""

import pytest

from tests.conftest import SAMPLE_JD, STRONG_RESUME, PARTIAL_RESUME, WEAK_RESUME

# Only import TestClient if httpx is available (not required for unit tests)
try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI not installed")
class TestScreenEndpoint:
    """
    End-to-end API tests.

    These hit the real Gemini API and take 30-60 seconds each.
    Mark with @pytest.mark.slow if you set up a custom marker.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_empty_resume_rejected(self, client):
        resp = client.post("/screen", json={
            "job_description": SAMPLE_JD,
            "resume_text": "",
        })
        assert resp.status_code == 422

    def test_empty_jd_rejected(self, client):
        resp = client.post("/screen", json={
            "job_description": "",
            "resume_text": STRONG_RESUME,
        })
        assert resp.status_code == 422

    @pytest.mark.skip(reason="Requires GEMINI_API_KEY — run manually")
    def test_strong_candidate_flow(self, client):
        resp = client.post("/screen", json={
            "job_description": SAMPLE_JD,
            "resume_text": STRONG_RESUME,
        })
        assert resp.status_code == 200
        data = resp.json()

        # Structural checks
        assert "candidate" in data
        assert "job" in data
        assert "matches" in data
        assert "gaps" in data
        assert "score" in data
        assert "report" in data

        # Score sanity
        assert 0 <= data["score"]["total_score"] <= 100

        # NO_EVIDENCE contract: no match should have status "LACKS"
        for m in data["matches"]:
            assert m["status"] in ("MATCH", "PARTIAL_MATCH", "NO_EVIDENCE")
