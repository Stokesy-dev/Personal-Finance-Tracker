from fastapi.testclient import TestClient
import os
import tempfile

from app.main import app
from app import auth


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


def test_register_login_and_current_user() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        credentials = {"email": "person@example.com", "password": "secure-pass-123"}
        registered = client.post("/api/v1/auth/register", json=credentials)
        assert registered.status_code == 201
        token = registered.json()["access_token"]
        assert client.post("/api/v1/auth/login", json=credentials).status_code == 200
        assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["email"] == credentials["email"]
        assert client.post("/api/v1/auth/register", json=credentials).status_code == 409


def test_csv_preview_requires_auth_and_returns_columns() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        credentials = {"email": "csv@example.com", "password": "secure-pass-123"}
        token = client.post("/api/v1/auth/register", json=credentials).json()["access_token"]
        response = client.post(
            "/api/v1/imports/preview",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("statement.csv", "Date,Description,Amount\n2026-01-01,Coffee,-4.50\n", "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["columns"] == ["Date", "Description", "Amount"]
        assert response.json()["rows"][0]["Description"] == "Coffee"


def test_mapping_rejects_missing_amount() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        token = client.post("/api/v1/auth/register", json={"email": "mapping@example.com", "password": "secure-pass-123"}).json()["access_token"]
        response = client.post(
            "/api/v1/imports/validate-mapping",
            headers={"Authorization": f"Bearer {token}"},
            json={"columns": ["Date", "Description"], "mapping": {"Date": "date", "Description": "description"}},
        )
        assert response.status_code == 400
        return


def test_normalize_debit_credit_rows() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        token = client.post("/api/v1/auth/register", json={"email": "normalize@example.com", "password": "secure-pass-123"}).json()["access_token"]
        response = client.post(
            "/api/v1/imports/normalize",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "rows": [{"Booked": "2026-01-01", "Payee": "Salary", "Out": "", "In": "2,000.00"}, {"Booked": "2026-01-02", "Payee": "Coffee", "Out": "4.50", "In": ""}],
                "mapping": {"Booked": "date", "Payee": "description", "Out": "debit", "In": "credit"},
            },
        )
        assert response.status_code == 200
        assert response.json()["transactions"] == [
            {"date": "2026-01-01", "description": "Salary", "amount": "2000.00", "type": "income"},
            {"date": "2026-01-02", "description": "Coffee", "amount": "-4.50", "type": "expense"},
        ]
