"""Domain management endpoints — reads/writes Neo4j Domain nodes."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from codelens.api.deps import current_user, admin_user
from codelens.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/domains")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _neo4j_domain_to_dict(record: dict) -> dict:
    return {
        "id": record.get("id") or record.get("name", ""),
        "name": record.get("name", ""),
        "repoId": record.get("repo_id", "default"),
        "repoName": record.get("repo_name", ""),
        "memberCount": record.get("member_count", 0),
        "summary": record.get("summary", ""),
        "humanVerified": bool(record.get("human_verified", False)),
        "lastUpdated": record.get("last_updated") or _now(),
    }


def _list_domains_from_neo4j(repo_id: str | None = None) -> list[dict]:
    client = Neo4jClient()
    try:
        with client.session() as session:
            query = """
            MATCH (d:Domain)
            OPTIONAL MATCH (n)-[:IN_DOMAIN]->(d)
            RETURN
                coalesce(d.uid, d.name) AS id,
                d.name AS name,
                coalesce(d.repo_id, 'default') AS repo_id,
                coalesce(d.repo_name, '') AS repo_name,
                count(n) AS member_count,
                coalesce(d.summary, '') AS summary,
                coalesce(d.human_verified, false) AS human_verified,
                coalesce(d.last_updated, '') AS last_updated
            ORDER BY member_count DESC
            """
            result = session.run(query)
            domains = [_neo4j_domain_to_dict(dict(r)) for r in result]
            if repo_id:
                domains = [d for d in domains if d["repoId"] == repo_id or repo_id == "default"]
            return domains
    except Exception as exc:
        logger.error("Error listing domains: %s", exc)
        return []
    finally:
        client.close()


@router.get("")
def list_domains(repoId: str | None = None, _=Depends(current_user)):
    return _list_domains_from_neo4j(repoId)


class UpdateDomainRequest(BaseModel):
    summary: str
    humanVerified: bool


@router.patch("/{domain_id}")
def update_domain(domain_id: str, body: UpdateDomainRequest, _=Depends(admin_user)):
    client = Neo4jClient()
    try:
        with client.session() as session:
            result = session.run(
                """
                MATCH (d:Domain)
                WHERE coalesce(d.uid, d.name) = $id
                SET d.summary = $summary, d.human_verified = $verified, d.last_updated = $now
                RETURN coalesce(d.uid, d.name) AS id, d.name AS name,
                       coalesce(d.repo_id, 'default') AS repo_id,
                       coalesce(d.repo_name, '') AS repo_name,
                       coalesce(d.summary, '') AS summary,
                       coalesce(d.human_verified, false) AS human_verified,
                       coalesce(d.last_updated, '') AS last_updated
                """,
                id=domain_id,
                summary=body.summary,
                verified=body.humanVerified,
                now=_now(),
            ).single()
            if not result:
                raise HTTPException(status_code=404, detail="Domain not found")

            # get member count separately
            count_row = session.run(
                "MATCH (n)-[:IN_DOMAIN]->(d:Domain) WHERE coalesce(d.uid, d.name) = $id RETURN count(n) AS c",
                id=domain_id,
            ).single()
            member_count = count_row["c"] if count_row else 0

            d = dict(result)
            d["member_count"] = member_count
            return _neo4j_domain_to_dict(d)
    finally:
        client.close()


@router.post("/{domain_id}/regenerate")
def regenerate_domain(domain_id: str, _=Depends(admin_user)):
    from codelens.graph.clustering import DomainClusterer
    from codelens.settings import settings as s

    client = Neo4jClient()
    try:
        with client.session() as session:
            row = session.run(
                "MATCH (d:Domain) WHERE coalesce(d.uid, d.name) = $id RETURN d.name AS name",
                id=domain_id,
            ).single()
            if not row:
                raise HTTPException(status_code=404, detail="Domain not found")
            domain_name = row["name"]

            # Build context from member signatures
            members_rows = session.run(
                """
                MATCH (n)-[:IN_DOMAIN]->(d:Domain)
                WHERE coalesce(d.uid, d.name) = $id
                RETURN coalesce(n.signature, n.name, '') AS sig
                LIMIT 50
                """,
                id=domain_id,
            )
            context = "\n".join(f"- {r['sig']}" for r in members_rows if r["sig"])

        clusterer = DomainClusterer(api_key=s.gemini_api_key or None)
        new_summary = clusterer._generate_domain_summary(domain_name, context)

        with client.session() as session:
            session.run(
                "MATCH (d:Domain) WHERE coalesce(d.uid, d.name) = $id "
                "SET d.summary = $summary, d.human_verified = false, d.last_updated = $now",
                id=domain_id,
                summary=new_summary,
                now=_now(),
            )

        domains = _list_domains_from_neo4j()
        match = next((d for d in domains if d["id"] == domain_id), None)
        if not match:
            raise HTTPException(status_code=404, detail="Domain not found after update")
        return match
    finally:
        client.close()
