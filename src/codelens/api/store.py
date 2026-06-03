"""Neo4j-backed store for users, repositories, and indexing jobs.

Admin data lives in the same Neo4j instance as the code graph but uses
distinct labels (:User, :Repository, :IndexingJob) that never overlap
with code-graph labels (File, Class, Function, …).
"""

from __future__ import annotations

import json
import secrets
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from passlib.context import CryptContext

from codelens.graph.neo4j_client import Neo4jClient

_lock = threading.Lock()
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Convenience alias — callers use dict-style access (row["id"]) which works
# identically for plain dicts.
Row = dict[str, Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _client() -> Neo4jClient:
    return Neo4jClient()


# ─── Bootstrap ────────────────────────────────────────────────────────────────


def init_db() -> None:
    """Create Neo4j constraints and seed the default admin user."""
    c = _client()
    try:
        with c.session() as s:
            # Uniqueness constraints
            for label, prop in [
                ("User", "id"),
                ("User", "email"),
                ("Repository", "id"),
                ("IndexingJob", "id"),
            ]:
                name = f"codelens_{label.lower()}_{prop}"
                s.run(
                    f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
                )

            # Seed default admin if none exists
            count = s.run("MATCH (u:User) RETURN count(u) AS c").single()["c"]
            if count == 0:
                import os
                admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD", "admin123")
                if admin_password == "admin123":
                    import logging
                    logging.getLogger(__name__).warning(
                        "Using default admin password 'admin123'. "
                        "Set ADMIN_INITIAL_PASSWORD env var before deploying."
                    )
                s.run(
                    """
                    CREATE (:User {
                        id: $id, email: $email, password_hash: $ph,
                        role: 'admin', created_at: $now, last_login: null
                    })
                    """,
                    id=str(uuid.uuid4()),
                    email="admin@codelens.dev",
                    ph=_pwd.hash(admin_password),
                    now=_now(),
                )
    finally:
        c.close()


# ─── Users ────────────────────────────────────────────────────────────────────


def _user_row(node) -> Row:
    return {
        "id": node["id"],
        "email": node["email"],
        "password_hash": node["password_hash"],
        "role": node["role"],
        "created_at": node["created_at"],
        "last_login": node["last_login"],
    }


def get_user_by_email(email: str) -> Row | None:
    c = _client()
    try:
        with c.session() as s:
            r = s.run("MATCH (u:User {email: $e}) RETURN u", e=email).single()
            return _user_row(r["u"]) if r else None
    finally:
        c.close()


def get_user_by_id(user_id: str) -> Row | None:
    c = _client()
    try:
        with c.session() as s:
            r = s.run("MATCH (u:User {id: $id}) RETURN u", id=user_id).single()
            return _user_row(r["u"]) if r else None
    finally:
        c.close()


def list_users() -> list[Row]:
    c = _client()
    try:
        with c.session() as s:
            return [_user_row(r["u"]) for r in s.run("MATCH (u:User) RETURN u ORDER BY u.created_at")]
    finally:
        c.close()


def create_user(email: str, password: str | None = None) -> tuple[Row, str]:
    chosen = password if password else secrets.token_urlsafe(12)
    user_id = str(uuid.uuid4())
    c = _client()
    try:
        with c.session() as s:
            s.run(
                """
                CREATE (:User {
                    id: $id, email: $email, password_hash: $ph,
                    role: 'user', created_at: $now, last_login: null
                })
                """,
                id=user_id, email=email, ph=_pwd.hash(chosen), now=_now(),
            )
    finally:
        c.close()
    return get_user_by_id(user_id), chosen


def delete_user(user_id: str) -> bool:
    c = _client()
    try:
        with c.session() as s:
            exists = s.run("MATCH (u:User {id: $id}) RETURN count(u) AS n", id=user_id).single()["n"] > 0
            if exists:
                s.run("MATCH (u:User {id: $id}) DETACH DELETE u", id=user_id)
            return exists
    finally:
        c.close()


def set_user_role(user_id: str, role: str) -> Row | None:
    c = _client()
    try:
        with c.session() as s:
            s.run("MATCH (u:User {id: $id}) SET u.role = $role", id=user_id, role=role)
    finally:
        c.close()
    return get_user_by_id(user_id)


def reset_user_password(user_id: str) -> str | None:
    temp_password = secrets.token_urlsafe(12)
    c = _client()
    try:
        with c.session() as s:
            result = s.run(
                "MATCH (u:User {id: $id}) SET u.password_hash = $ph RETURN count(u) AS n",
                id=user_id, ph=_pwd.hash(temp_password),
            ).single()
            if not result or result["n"] == 0:
                return None
    finally:
        c.close()
    return temp_password


def update_last_login(user_id: str) -> None:
    c = _client()
    try:
        with c.session() as s:
            s.run("MATCH (u:User {id: $id}) SET u.last_login = $now", id=user_id, now=_now())
    finally:
        c.close()


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ─── Repositories ─────────────────────────────────────────────────────────────


def _repo_row(node) -> Row:
    return {
        "id": node["id"],
        "name": node["name"],
        "url": node["url"],
        "paths": json.loads(node.get("paths", "[]")),
        "last_indexed": node.get("last_indexed"),
        "node_count": node.get("node_count", 0),
        "status": node.get("status", "pending"),
    }


def list_repos() -> list[Row]:
    c = _client()
    try:
        with c.session() as s:
            return [_repo_row(r["r"]) for r in s.run("MATCH (r:Repository) RETURN r ORDER BY r.created_at")]
    finally:
        c.close()


def get_repo(repo_id: str) -> Row | None:
    c = _client()
    try:
        with c.session() as s:
            r = s.run("MATCH (r:Repository {id: $id}) RETURN r", id=repo_id).single()
            return _repo_row(r["r"]) if r else None
    finally:
        c.close()


def create_repo(url: str, paths: list[str] | None = None) -> Row:
    repo_id = str(uuid.uuid4())
    name = url.rstrip("/").split("/")[-1] or url
    c = _client()
    try:
        with c.session() as s:
            s.run(
                """
                CREATE (:Repository {
                    id: $id, name: $name, url: $url,
                    paths: $paths, status: 'pending',
                    node_count: 0, last_indexed: null, created_at: $now
                })
                """,
                id=repo_id, name=name, url=url,
                paths=json.dumps(paths or []), now=_now(),
            )
    finally:
        c.close()
    return get_repo(repo_id)


def update_repo_status(repo_id: str, status: str, node_count: int | None = None) -> None:
    c = _client()
    try:
        with c.session() as s:
            if node_count is not None:
                s.run(
                    "MATCH (r:Repository {id: $id}) SET r.status=$s, r.node_count=$n, r.last_indexed=$now",
                    id=repo_id, s=status, n=node_count, now=_now(),
                )
            else:
                s.run("MATCH (r:Repository {id: $id}) SET r.status=$s", id=repo_id, s=status)
    finally:
        c.close()


def delete_repo(repo_id: str) -> bool:
    c = _client()
    try:
        with c.session() as s:
            exists = s.run("MATCH (r:Repository {id: $id}) RETURN count(r) AS n", id=repo_id).single()["n"] > 0
            if exists:
                s.run("MATCH (r:Repository {id: $id}) DETACH DELETE r", id=repo_id)
            return exists
    finally:
        c.close()


# ─── Jobs ─────────────────────────────────────────────────────────────────────


def _job_row(node) -> Row:
    return {
        "id": node["id"],
        "repo_id": node["repo_id"],
        "repo_name": node["repo_name"],
        "status": node["status"],
        "started_at": node["started_at"],
        "finished_at": node.get("finished_at"),
        "duration_ms": node.get("duration_ms"),
        "node_count": node.get("node_count"),
        "error": node.get("error"),
    }


def create_job(repo_id: str, repo_name: str) -> Row:
    job_id = str(uuid.uuid4())
    c = _client()
    try:
        with c.session() as s:
            s.run(
                """
                CREATE (:IndexingJob {
                    id: $id, repo_id: $repo_id, repo_name: $repo_name,
                    status: 'running', started_at: $now,
                    finished_at: null, duration_ms: null,
                    node_count: null, error: null
                })
                """,
                id=job_id, repo_id=repo_id, repo_name=repo_name, now=_now(),
            )
    finally:
        c.close()
    return get_job(job_id)


def get_job(job_id: str) -> Row | None:
    c = _client()
    try:
        with c.session() as s:
            r = s.run("MATCH (j:IndexingJob {id: $id}) RETURN j", id=job_id).single()
            return _job_row(r["j"]) if r else None
    finally:
        c.close()


def list_jobs(limit: int = 50) -> list[Row]:
    c = _client()
    try:
        with c.session() as s:
            return [
                _job_row(r["j"])
                for r in s.run(
                    "MATCH (j:IndexingJob) RETURN j ORDER BY j.started_at DESC LIMIT $limit",
                    limit=limit,
                )
            ]
    finally:
        c.close()


def finish_job(
    job_id: str,
    status: str,
    duration_ms: int,
    node_count: int | None = None,
    error: str | None = None,
) -> None:
    c = _client()
    try:
        with c.session() as s:
            s.run(
                """
                MATCH (j:IndexingJob {id: $id})
                SET j.status=$status, j.finished_at=$now,
                    j.duration_ms=$ms, j.node_count=$nc, j.error=$err
                """,
                id=job_id, status=status, now=_now(),
                ms=duration_ms, nc=node_count, err=error,
            )
    finally:
        c.close()
