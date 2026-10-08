import sqlite3
from decimal import Decimal

from .auth import _connect


def _init_transactions(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, transaction_date TEXT NOT NULL, description TEXT NOT NULL, amount_cents INTEGER NOT NULL, transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')), import_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))")
    connection.commit()


def save_transactions(user_id: int, transactions: list[dict[str, str]], import_id: str) -> int:
    connection = _connect()
    _init_transactions(connection)
    connection.executemany("INSERT INTO transactions (user_id, transaction_date, description, amount_cents, transaction_type, import_id) VALUES (?, ?, ?, ?, ?, ?)", [(user_id, item["date"], item["description"], round(Decimal(item["amount"]) * 100), item["type"], import_id) for item in transactions])
    connection.commit()
    count = len(transactions)
    connection.close()
    return count


def list_imports(user_id: int) -> list[dict[str, object]]:
    connection = _connect()
    _init_transactions(connection)
    rows = connection.execute("SELECT import_id, MIN(transaction_date) AS start_date, MAX(transaction_date) AS end_date, COUNT(*) AS transaction_count FROM transactions WHERE user_id = ? GROUP BY import_id ORDER BY end_date DESC", (user_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def summary(user_id: int) -> dict[str, object]:
    connection = _connect()
    _init_transactions(connection)
    rows = connection.execute("SELECT transaction_type, SUM(amount_cents) AS total FROM transactions WHERE user_id = ? GROUP BY transaction_type", (user_id,)).fetchall()
    connection.close()
    income = next((row["total"] or 0 for row in rows if row["transaction_type"] == "income"), 0)
    expenses = next((-(row["total"] or 0) for row in rows if row["transaction_type"] == "expense"), 0)
    savings = income - expenses
    return {"income": income / 100, "expenses": expenses / 100, "savings": savings / 100, "savings_rate": round(savings / income * 100, 2) if income else 0, "categories": [], "recent_transactions": []}
