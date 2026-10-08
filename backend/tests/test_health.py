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
    assert response.status_code == 403


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


def test_commit_and_summary() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        token = client.post("/api/v1/auth/register", json={"email": "storage@example.com", "password": "secure-pass-123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        rows = [{"date": "2026-01-01", "description": "Salary", "amount": "2000.00", "type": "income"}, {"date": "2026-01-02", "description": "Coffee", "amount": "-4.50", "type": "expense"}]
        committed = client.post("/api/v1/imports/commit?import_id=january", headers=headers, json=rows)
        assert committed.status_code == 201
        assert client.get("/api/v1/summary", headers=headers).json()["income"] == 2000
        assert client.get("/api/v1/summary", headers=headers).json()["expenses"] == 4.5
        assert client.get("/api/v1/imports", headers=headers).json()["imports"][0]["transaction_count"] == 2


def test_categories_and_merchant_rules_are_user_scoped() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        token = client.post("/api/v1/auth/register", json={"email": "rules@example.com", "password": "secure-pass-123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        category = client.post("/api/v1/categories", headers=headers, json={"name": "Coffee", "color": "#aabbcc"})
        assert category.status_code == 201
        rule = client.post("/api/v1/merchant-rules", headers=headers, json={"keyword": "Starbucks", "category_id": category.json()["id"]})
        assert rule.status_code == 201
        assert rule.json()["keyword"] == "starbucks"
        assert client.get("/api/v1/merchant-rules", headers=headers).json()["rules"][0]["category_name"] == "Coffee"


def test_categorization_prefers_rules_then_fallback() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        token = client.post("/api/v1/auth/register", json={"email": "categorize@example.com", "password": "secure-pass-123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        category = client.post("/api/v1/categories", headers=headers, json={"name": "Coffee"}).json()
        client.post("/api/v1/merchant-rules", headers=headers, json={"keyword": "Acme Cafe", "category_id": category["id"]})
        ruled = client.post("/api/v1/categorize?description=Acme%20Cafe%20Downtown", headers=headers).json()
        assert ruled["source"] == "merchant_rule" and ruled["confidence"] == 1.0
        fallback = client.post("/api/v1/categorize?description=Morning%20coffee", headers=headers).json()
        assert fallback["category"] == "Coffee" and fallback["source"] == "keyword_fallback"


def test_unusual_spending_alerts_are_user_scoped() -> None:
    with tempfile.NamedTemporaryFile() as database:
        auth.DATABASE_PATH = database.name
        token = client.post("/api/v1/auth/register", json={"email": "alerts@example.com", "password": "secure-pass-123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        rows = [{"date": "2026-01-01", "description": "Coffee", "amount": "-4.00", "type": "expense"}, {"date": "2026-01-02", "description": "Lunch", "amount": "-5.00", "type": "expense"}, {"date": "2026-01-03", "description": "Laptop", "amount": "-500.00", "type": "expense"}]
        client.post("/api/v1/imports/commit?import_id=jan", headers=headers, json=rows)
        alerts = client.get("/api/v1/alerts/unusual-spending", headers=headers)
        assert alerts.status_code == 200 and alerts.json()["alerts"][0]["description"] == "Laptop"
