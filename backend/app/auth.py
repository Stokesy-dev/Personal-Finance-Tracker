import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

DATABASE_PATH = os.getenv("DATABASE_PATH", "finance.db")
JWT_SECRET = os.getenv("JWT_SECRET", "development-secret-change-me")
security = HTTPBearer()


class Credentials(BaseModel):
    email: EmailStr
    password: str


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)")
    return connection


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$", 1)
    candidate = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest_hex)


def _token(user_id: int, email: str) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"sub": str(user_id), "email": email, "exp": expiry}, JWT_SECRET, algorithm="HS256")


def register(credentials: Credentials) -> dict[str, str | int]:
    if len(credentials.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    connection = _connect()
    try:
        cursor = connection.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (credentials.email.lower(), _hash_password(credentials.password)))
        connection.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with that email already exists") from exc
    finally:
        connection.close()
    return {"access_token": _token(cursor.lastrowid, credentials.email.lower()), "token_type": "bearer", "user_id": cursor.lastrowid}


def login(credentials: Credentials) -> dict[str, str | int]:
    connection = _connect()
    row = connection.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (credentials.email.lower(),)).fetchone()
    connection.close()
    if not row or not _verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": _token(row["id"], row["email"]), "token_type": "bearer", "user_id": row["id"]}


def current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, str | int]:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return {"id": int(payload["sub"]), "email": payload["email"]}
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}) from exc
