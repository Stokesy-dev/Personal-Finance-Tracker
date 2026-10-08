from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import Credentials, current_user, login, register

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
