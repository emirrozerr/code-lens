"""Stats endpoint — dashboard summary."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from codelens.api import store
from codelens.api.deps import current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stats")


def _neo4j_node_count() -> int:
    try:
        from codelens.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        with client.session() as session:
            row = session.run(
                "MATCH (n) WHERE NOT n:Domain AND NOT n:User "
                "AND NOT n:Repository AND NOT n:IndexingJob "
                "RETURN count(n) AS c"
            ).single()
            return row["c"] if row else 0
    except Exception:
        return 0
    finally:
        try:
            client.close()
        except Exception:
            pass


def _neo4j_status() -> str:
    try:
        from codelens.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        with client.session() as session:
            session.run("RETURN 1")
        client.close()
        return "ok"
    except Exception:
        return "down"


def _domain_count() -> int:
    try:
        from codelens.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        with client.session() as session:
            row = session.run("MATCH (d:Domain) RETURN count(d) AS c").single()
            return row["c"] if row else 0
    except Exception:
        return 0
    finally:
        try:
            client.close()
        except Exception:
            pass


def _last_successful_index() -> str | None:
    jobs = store.list_jobs(limit=100)
    for job in jobs:
        if job["status"] == "succeeded" and job["finished_at"]:
            return job["finished_at"]
    return None


@router.get("")
def get_stats(_=Depends(current_user)):
    repos = store.list_repos()
    users = store.list_users()

    return {
        "reposCount": len(repos),
        "totalNodes": _neo4j_node_count(),
        "domainsCount": _domain_count(),
        "activeUsers": len(users),
        "neo4jStatus": _neo4j_status(),
        "mcpUptime": 0,
        "lastSuccessfulIndex": _last_successful_index(),
    }
