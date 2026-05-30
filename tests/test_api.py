"""Phase 6: basic API tests (FastAPI)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "dataset_loaded" in data
    assert "llm_configured" in data


def test_recommendations_endpoint_returns_payload() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/v1/recommendations",
        json={"location": "Bangalore", "budget": "medium", "cuisine": "Italian", "min_rating": 4.0},
    )
    assert res.status_code == 200
    data = res.json()
    # Either empty filter result, or full recommendation result.
    assert ("items" in data) or ("suggestions" in data)

