"""Graph data endpoint — returns nodes and edges from Neo4j for visualization."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from codelens.api.deps import current_user
from codelens.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph")

_EDGE_TYPE_MAP = {
    "calls": "calls",
    "imports": "imports",
    "extends": "inherits",
    "contains": "uses",
    "IN_DOMAIN": "uses",
    "has_branch": "uses",
    "returns": "uses",
}


@router.get("")
def get_graph(repoId: str | None = None, _=Depends(current_user)):
    client = Neo4jClient()
    try:
        with client.session() as session:
            _SKIP = (
                "NOT n:File AND NOT n:ConditionalBranch AND NOT n:Unresolved "
                "AND NOT n:ReturnStatement AND NOT n:User AND NOT n:Repository "
                "AND NOT n:IndexingJob AND NOT n:Domain"
            )

            node_query = f"""
            MATCH (n)
            WHERE {_SKIP}
            OPTIONAL MATCH (n)-[:IN_DOMAIN]->(d:Domain)
            WITH n, d, size([(n)-[]-() | 1]) AS degree
            RETURN
                coalesce(n.uid, toString(id(n))) AS id,
                labels(n)[0] AS label,
                coalesce(n.filepath, '') AS file,
                coalesce(n.signature, n.name, '') AS signature,
                coalesce(d.name, '') AS domain,
                coalesce(coalesce(d.uid, d.name), '') AS domainId,
                degree
            ORDER BY degree DESC
            """
            node_rows = session.run(node_query)
            nodes = []
            node_ids: set[str] = set()
            for r in node_rows:
                node_id = r["id"]
                node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": r["label"] or "Unknown",
                    "file": r["file"],
                    "signature": r["signature"],
                    "domain": r["domain"],
                    "domainId": r["domainId"],
                    "degree": r["degree"],
                })

            _SKIP_EDGE = (
                "NOT a:File AND NOT a:ConditionalBranch AND NOT a:Unresolved "
                "AND NOT a:ReturnStatement AND NOT a:User AND NOT a:Repository AND NOT a:IndexingJob "
                "AND NOT b:File AND NOT b:ConditionalBranch AND NOT b:Unresolved "
                "AND NOT b:ReturnStatement AND NOT b:User AND NOT b:Repository AND NOT b:IndexingJob"
            )
            edge_query = f"""
            MATCH (a)-[r]->(b)
            WHERE {_SKIP_EDGE} AND type(r) <> 'IN_DOMAIN'
            RETURN
                coalesce(a.uid, toString(id(a))) AS source,
                coalesce(b.uid, toString(id(b))) AS target,
                type(r) AS rel_type
            """
            edge_rows = session.run(edge_query)
            edges = []
            for r in edge_rows:
                src, tgt = r["source"], r["target"]
                if src in node_ids and tgt in node_ids:
                    edges.append({
                        "source": src,
                        "target": tgt,
                        "type": _EDGE_TYPE_MAP.get(r["rel_type"], "uses"),
                    })

        return {"nodes": nodes, "edges": edges}
    except Exception as exc:
        logger.error("Error fetching graph: %s", exc)
        return {"nodes": [], "edges": []}
    finally:
        client.close()
