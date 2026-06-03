"""Repository management endpoints."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from codelens.api import store
from codelens.api.deps import admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repos")


def _repo_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "url": row["url"],
        "paths": row["paths"],  # already a list from store
        "lastIndexed": row["last_indexed"],
        "nodeCount": row["node_count"],
        "status": row["status"],
    }


def _job_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "repoId": row["repo_id"],
        "repoName": row["repo_name"],
        "status": row["status"],
        "startedAt": row["started_at"],
        "finishedAt": row["finished_at"],
        "durationMs": row["duration_ms"],
        "nodeCount": row["node_count"],
        "error": row["error"],
    }


class AddRepoRequest(BaseModel):
    url: str
    paths: list[str] | None = None


def _is_git_url(url: str) -> bool:
    return url.startswith(("https://", "http://", "git@", "git://"))


def _clone_repo(url: str, dest: Path) -> None:
    """Clone a git repository to dest directory."""
    import subprocess
    result = subprocess.run(
        ["git", "clone", "--depth=1", url, str(dest)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")


def _run_indexing(repo_id: str, repo_name: str, url: str, paths: list[str]) -> None:
    """Background task: creates a job then runs indexing (used by add_repo)."""
    job_row = store.create_job(repo_id, repo_name)
    _run_indexing_with_job(repo_id, repo_name, url, paths, job_row["id"])


def _run_indexing_with_job(repo_id: str, repo_name: str, url: str, paths: list[str], job_id: str) -> None:
    """Background task: clone (if URL) then parse repo and ingest into Neo4j."""
    import tempfile
    import shutil

    start = time.monotonic()
    tmp_dir = None

    try:
        store.update_repo_status(repo_id, "indexing")

        if _is_git_url(url):
            tmp_dir = Path(tempfile.mkdtemp(prefix="codelens_"))
            logger.info("Cloning %s → %s", url, tmp_dir)
            _clone_repo(url, tmp_dir)
            repo_path = tmp_dir
        else:
            repo_path = Path(url)
            if not repo_path.exists():
                raise ValueError(f"Path does not exist: {url}")

        from codelens.indexer.indexer import Indexer
        from codelens.graph.neo4j_client import Neo4jClient

        indexer = Indexer()
        result = indexer.index_repository(repo_path)

        client = Neo4jClient()
        try:
            client.setup_schema()
            client.ingest_parse_result(result)
        finally:
            client.close()

        # Run domain clustering after ingestion
        try:
            from codelens.graph.clustering import DomainClusterer
            from codelens.settings import settings as s
            api_key = s.gemini_api_key if s.gemini_api_key != "your_gemini_api_key_here" else None
            clusterer = DomainClusterer(api_key=api_key)
            domains = clusterer.run_clustering(repo_id=repo_id)
            logger.info("Clustering complete: %d domains", len(domains) if domains else 0)
        except Exception as cluster_exc:
            logger.warning("Clustering failed (non-fatal): %s", cluster_exc)

        elapsed = int((time.monotonic() - start) * 1000)
        node_count = len(result.nodes)
        store.finish_job(job_id, "succeeded", elapsed, node_count)
        store.update_repo_status(repo_id, "indexed", node_count)
        logger.info("Indexing complete for repo %s: %d nodes in %dms", repo_id, node_count, elapsed)

    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        store.finish_job(job_id, "failed", elapsed, error=str(exc))
        store.update_repo_status(repo_id, "failed")
        logger.error("Indexing failed for repo %s: %s", repo_id, exc)

    finally:
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("")
def list_repos(_=Depends(admin_user)):
    return [_repo_dict(r) for r in store.list_repos()]


@router.post("", status_code=status.HTTP_201_CREATED)
def add_repo(body: AddRepoRequest, background: BackgroundTasks, _=Depends(admin_user)):
    repo = store.create_repo(body.url, body.paths)
    background.add_task(_run_indexing, repo["id"], repo["name"], body.url, body.paths or [])
    return _repo_dict(repo)


@router.post("/{repo_id}/reindex")
def reindex_repo(repo_id: str, background: BackgroundTasks, _=Depends(admin_user)):
    repo = store.get_repo(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    job = store.create_job(repo["id"], repo["name"])
    background.add_task(_run_indexing_with_job, repo["id"], repo["name"], repo["url"], repo["paths"], job["id"])
    return _job_dict(job)


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repo(repo_id: str, _=Depends(admin_user)):
    # Idempotent: if already deleted, still return 204
    store.delete_repo(repo_id)
    _clear_neo4j_for_repo(repo_id)


def _clear_neo4j_for_repo(repo_id: str) -> None:
    """Remove domains and code nodes that belong to this repo from Neo4j."""
    try:
        from codelens.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        repo = store.get_repo(repo_id)
        repo_url = repo["url"] if repo else None
        with client.session() as session:
            # Delete this repo's domains
            session.run(
                "MATCH (d:Domain) WHERE coalesce(d.repo_id, 'default') = $rid DETACH DELETE d",
                rid=repo_id,
            )
            # Delete code nodes scoped to this repo's URL prefix (filepath match)
            # Falls back to clearing all code nodes only if URL unavailable
            if repo_url:
                repo_name = repo_url.rstrip("/").split("/")[-1]
                session.run(
                    "MATCH (n) WHERE NOT n:User AND NOT n:Repository "
                    "AND NOT n:IndexingJob AND NOT n:Domain "
                    "AND (n.filepath STARTS WITH $name OR n.filepath IS NULL) "
                    "DETACH DELETE n",
                    name=repo_name,
                )
            else:
                session.run(
                    "MATCH (n) WHERE NOT n:User AND NOT n:Repository "
                    "AND NOT n:IndexingJob AND NOT n:Domain DETACH DELETE n"
                )
        client.close()
    except Exception as exc:
        logger.warning("Neo4j cleanup failed (non-fatal): %s", exc)
