import sqlite3
from decimal import Decimal

from .auth import _connect


def _init_transactions(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, transaction_date TEXT NOT NULL, description TEXT NOT NULL, amount_cents INTEGER NOT NULL, transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')), import_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))")
    connection.commit()


def _init_categories(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT NOT NULL, color TEXT NOT NULL DEFAULT '#7a9186', UNIQUE(user_id, name), FOREIGN KEY(user_id) REFERENCES users(id))")
    connection.execute("CREATE TABLE IF NOT EXISTS merchant_rules (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, keyword TEXT NOT NULL, category_id INTEGER NOT NULL, UNIQUE(user_id, keyword), FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(category_id) REFERENCES categories(id))")
    connection.commit()


def create_category(user_id: int, name: str, color: str) -> dict[str, object]:
    connection = _connect(); _init_categories(connection)
    try:
        cursor = connection.execute("INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)", (user_id, name.strip(), color))
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.close()
        raise ValueError("Category already exists") from exc
    category = {"id": cursor.lastrowid, "name": name.strip(), "color": color}
    connection.close(); return category


def list_categories(user_id: int) -> list[dict[str, object]]:
    connection = _connect(); _init_categories(connection)
    rows = connection.execute("SELECT id, name, color FROM categories WHERE user_id = ? ORDER BY name", (user_id,)).fetchall(); connection.close()
    return [dict(row) for row in rows]


def create_rule(user_id: int, keyword: str, category_id: int) -> dict[str, object]:
    connection = _connect(); _init_categories(connection)
    category = connection.execute("SELECT id, name FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id)).fetchone()
    if not category: connection.close(); raise ValueError("Category not found")
    try:
        cursor = connection.execute("INSERT INTO merchant_rules (user_id, keyword, category_id) VALUES (?, ?, ?)", (user_id, keyword.strip().lower(), category_id)); connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.close(); raise ValueError("Rule already exists") from exc
    rule = {"id": cursor.lastrowid, "keyword": keyword.strip().lower(), "category_id": category_id, "category_name": category["name"]}; connection.close(); return rule


def list_rules(user_id: int) -> list[dict[str, object]]:
    connection = _connect(); _init_categories(connection)
    rows = connection.execute("SELECT merchant_rules.id, keyword, category_id, categories.name AS category_name FROM merchant_rules JOIN categories ON categories.id = merchant_rules.category_id WHERE merchant_rules.user_id = ? ORDER BY keyword", (user_id,)).fetchall(); connection.close()
    return [dict(row) for row in rows]


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


def unusual_expenses(user_id: int) -> list[dict[str, object]]:
    connection = _connect(); _init_transactions(connection)
    rows = connection.execute("SELECT id, transaction_date, description, amount_cents FROM transactions WHERE user_id = ? AND transaction_type = 'expense' ORDER BY transaction_date DESC", (user_id,)).fetchall(); connection.close()
    amounts = sorted(abs(row["amount_cents"]) for row in rows)
    if len(amounts) < 3: return []
    median = amounts[len(amounts) // 2]
    threshold = max(5000, median * 3)
    return [{"id": row["id"], "date": row["transaction_date"], "description": row["description"], "amount": abs(row["amount_cents"]) / 100, "threshold": threshold / 100, "reason": "More than three times your typical expense"} for row in rows if abs(row["amount_cents"]) >= threshold]
