from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .auth import Credentials, current_user, login, register
from .imports import normalize_rows, preview_csv, validate_mapping

app = FastAPI(title="Personal Finance Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "personal-finance-tracker-api"}


@app.post("/api/v1/auth/register", status_code=201)
def create_account(credentials: Credentials):
    return register(credentials)


@app.post("/api/v1/auth/login")
def sign_in(credentials: Credentials):
    return login(credentials)


@app.get("/api/v1/auth/me")
def me(user=Depends(current_user)):
    return user


@app.post("/api/v1/imports/preview")
async def csv_preview(file: UploadFile = File(...), user=Depends(current_user)):
    preview = await preview_csv(file)
    return {"columns": preview.columns, "rows": preview.rows, "user_id": user["id"]}


@app.post("/api/v1/imports/validate-mapping")
def mapping_preview(columns: list[str], mapping: dict[str, str], user=Depends(current_user)):
    return {"mapping": validate_mapping(columns, mapping), "user_id": user["id"]}


@app.post("/api/v1/imports/normalize")
def normalize_import(rows: list[dict[str, str]], mapping: dict[str, str], user=Depends(current_user)):
    validated_mapping = validate_mapping(list(rows[0].keys()) if rows else [], mapping)
    normalized = normalize_rows(rows, validated_mapping)
    return {"transactions": [transaction.__dict__ for transaction in normalized], "user_id": user["id"]}


@app.get("/api/v1/summary")
def summary() -> dict[str, object]:
    """Return an empty summary until transaction persistence is implemented."""
    return {
        "income": 0,
        "expenses": 0,
        "savings": 0,
        "savings_rate": 0,
        "categories": [],
        "recent_transactions": [],
    }
