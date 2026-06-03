"""Indexing job status endpoints."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from codelens.api import store
from codelens.api.deps import admin_user

router = APIRouter(prefix="/api/jobs")


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


@router.get("")
def list_jobs(limit: int = 50, _=Depends(admin_user)):
    return [_job_dict(j) for j in store.list_jobs(limit)]


@router.get("/{job_id}/stream")
async def stream_job(job_id: str, _=Depends(admin_user)):
    """SSE stream: emits job status every second until the job is no longer running."""

    async def _generate():
        while True:
            row = store.get_job(job_id)
            if not row:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            payload = _job_dict(row)
            yield f"data: {json.dumps(payload)}\n\n"
            if payload["status"] not in ("running", "pending"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
