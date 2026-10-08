from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .auth import Credentials, current_user, login, register
from .imports import normalize_rows, preview_csv, validate_mapping
from .storage import list_imports, save_transactions, summary as user_summary

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
def summary(user=Depends(current_user)):
    return user_summary(user["id"])


@app.post("/api/v1/imports/commit", status_code=201)
def commit_import(import_id: str, transactions: list[dict[str, str]], user=Depends(current_user)):
    from fastapi import HTTPException
    if not import_id.strip() or not transactions:
        raise HTTPException(status_code=400, detail="import_id and transactions are required")
    return {"import_id": import_id.strip(), "transaction_count": save_transactions(user["id"], transactions, import_id.strip())}


@app.get("/api/v1/imports")
def imports(user=Depends(current_user)):
    return {"imports": list_imports(user["id"])}
