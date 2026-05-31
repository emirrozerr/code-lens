"""SQLite-backed store for users, repositories, and indexing jobs."""

from __future__ import annotations

import json
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from passlib.context import CryptContext

_DB_PATH = Path(__file__).parent.parent.parent.parent / "codelens.db"
_lock = threading.Lock()
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    """Create tables if they don't exist and seed the default admin user."""
    with _lock, _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                email       TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'user',
                created_at  TEXT NOT NULL,
                last_login  TEXT
            );

            CREATE TABLE IF NOT EXISTS repos (
                id           TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                url          TEXT NOT NULL,
                paths        TEXT NOT NULL DEFAULT '[]',
                last_indexed TEXT,
                node_count   INTEGER NOT NULL DEFAULT 0,
                status       TEXT NOT NULL DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                repo_id     TEXT NOT NULL,
                repo_name   TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                started_at  TEXT NOT NULL,
                finished_at TEXT,
                duration_ms INTEGER,
                node_count  INTEGER,
                error       TEXT
            );
        """)

        # Seed default admin if no users exist
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        if row[0] == 0:
            admin_id = str(uuid.uuid4())
            admin_password = "admin123"
            conn.execute(
                "INSERT INTO users (id, email, password_hash, role, created_at) VALUES (?,?,?,?,?)",
                (admin_id, "admin@codelens.dev", _pwd.hash(admin_password), "admin", _now()),
            )


# ─── Users ────────────────────────────────────────────────────────────────────


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def list_users() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("SELECT * FROM users ORDER BY created_at").fetchall()


def create_user(email: str) -> tuple[sqlite3.Row, str]:
    temp_password = secrets.token_urlsafe(12)
    user_id = str(uuid.uuid4())
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, role, created_at) VALUES (?,?,?,?,?)",
            (user_id, email, _pwd.hash(temp_password), "user", _now()),
        )
    return get_user_by_id(user_id), temp_password


def delete_user(user_id: str) -> bool:
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cur.rowcount > 0


def set_user_role(user_id: str, role: str) -> sqlite3.Row | None:
    with _lock, _connect() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    return get_user_by_id(user_id)


def reset_user_password(user_id: str) -> str | None:
    temp_password = secrets.token_urlsafe(12)
    with _lock, _connect() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_pwd.hash(temp_password), user_id),
        )
        if cur.rowcount == 0:
            return None
    return temp_password


def update_last_login(user_id: str) -> None:
    with _lock, _connect() as conn:
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (_now(), user_id))


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ─── Repos ────────────────────────────────────────────────────────────────────


def list_repos() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("SELECT * FROM repos ORDER BY rowid").fetchall()


def get_repo(repo_id: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute("SELECT * FROM repos WHERE id = ?", (repo_id,)).fetchone()


def create_repo(url: str, paths: list[str] | None = None) -> sqlite3.Row:
    repo_id = str(uuid.uuid4())
    name = url.rstrip("/").split("/")[-1] or url
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO repos (id, name, url, paths, status) VALUES (?,?,?,?,?)",
            (repo_id, name, url, json.dumps(paths or []), "pending"),
        )
    return get_repo(repo_id)


def update_repo_status(repo_id: str, status: str, node_count: int | None = None) -> None:
    with _lock, _connect() as conn:
        if node_count is not None:
            conn.execute(
                "UPDATE repos SET status=?, node_count=?, last_indexed=? WHERE id=?",
                (status, node_count, _now(), repo_id),
            )
        else:
            conn.execute("UPDATE repos SET status=? WHERE id=?", (status, repo_id))


def delete_repo(repo_id: str) -> bool:
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM repos WHERE id = ?", (repo_id,))
        return cur.rowcount > 0


# ─── Jobs ─────────────────────────────────────────────────────────────────────


def create_job(repo_id: str, repo_name: str) -> sqlite3.Row:
    job_id = str(uuid.uuid4())
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO jobs (id, repo_id, repo_name, status, started_at) VALUES (?,?,?,?,?)",
            (job_id, repo_id, repo_name, "running", _now()),
        )
    return get_job(job_id)


def get_job(job_id: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def list_jobs(limit: int = 50) -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()


def finish_job(
    job_id: str,
    status: str,
    duration_ms: int,
    node_count: int | None = None,
    error: str | None = None,
) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status=?, finished_at=?, duration_ms=?, node_count=?, error=? WHERE id=?",
            (status, _now(), duration_ms, node_count, error, job_id),
        )
