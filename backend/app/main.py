from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
