from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_summary_shape() -> None:
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    assert set(response.json()) == {
        "income",
        "expenses",
        "savings",
        "savings_rate",
        "categories",
        "recent_transactions",
    }
