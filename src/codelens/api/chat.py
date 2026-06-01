"""Chat endpoint — SSE streaming with multi-keyword graph search and multi-turn history."""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from codelens.api.deps import current_user
from codelens.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request model ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    persona: str = "developer"
    history: list[dict] = []
    domainId: str | None = None


# ─── SSE helpers ──────────────────────────────────────────────────────────────

def _emit(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


# ─── MCP tool callers ─────────────────────────────────────────────────────────

def _search(keyword: str) -> str:
    try:
        from codelens.mcp_server.server import search_nodes
        return search_nodes(keyword)
    except Exception as exc:
        return f"Search error: {exc}"


def _context(symbol: str) -> str:
    try:
        from codelens.mcp_server.server import get_code_context
        return get_code_context(symbol)
    except Exception as exc:
        return f"Context error: {exc}"


def _fetch_domain_context(domain_id: str) -> tuple[str, str]:
    """Return (domain_name, context_text) for a domain by its Neo4j uid."""
    try:
        from codelens.graph.neo4j_client import Neo4jClient
        client = Neo4jClient()
        with client.session() as s:
            row = s.run(
                "MATCH (d:Domain) WHERE coalesce(d.uid, d.name) = $id "
                "RETURN d.name AS name, coalesce(d.summary, '') AS summary",
                id=domain_id,
            ).single()
            if not row:
                return "", ""
            domain_name = row["name"]
            summary = row["summary"]

            members = s.run(
                """
                MATCH (n)-[:IN_DOMAIN]->(d:Domain)
                WHERE coalesce(d.uid, d.name) = $id
                RETURN labels(n)[0] AS type,
                       coalesce(n.name, '') AS name,
                       coalesce(n.signature, '') AS signature,
                       coalesce(n.filepath, '') AS filepath
                LIMIT 60
                """,
                id=domain_id,
            )
            lines = [f"Domain: {domain_name}", f"Summary: {summary}", "", "Members:"]
            for m in members:
                sig = m["signature"] or m["name"]
                lines.append(f"  [{m['type']}] {sig}  ({m['filepath']})")
        client.close()
        return domain_name, "\n".join(lines)
    except Exception as exc:
        logger.error("Domain context fetch error: %s", exc)
        return "", ""


# ─── Keyword extraction ───────────────────────────────────────────────────────

_STOP = {
    "what", "which", "where", "when", "why", "how", "does", "that", "this",
    "these", "those", "with", "from", "about", "into", "then", "than", "them",
    "they", "their", "there", "here", "have", "been", "were", "will", "would",
    "could", "should", "shall", "make", "made", "some", "okay", "please", "tell",
    "show", "give", "find", "look", "also", "just", "your", "improve", "codebase",
    "code", "function", "functions", "class", "classes", "file", "files", "using",
    "explain", "describe", "list", "return", "returns", "call", "calls", "used",
    "works", "work", "does", "need", "needs", "want", "wants", "help", "like",
}


def _extract_keywords(message: str, max_k: int = 3) -> list[str]:
    """Extract up to max_k meaningful keywords from the message, longest first."""
    words = [w.strip("?.!,;:'\"()[]{}") for w in message.split()]
    candidates = [w for w in words if len(w) > 3 and w.lower() not in _STOP]
    # Deduplicate case-insensitively, prefer longer/more specific
    seen: set[str] = set()
    result: list[str] = []
    for w in sorted(candidates, key=len, reverse=True):
        if w.lower() not in seen:
            seen.add(w.lower())
            result.append(w)
        if len(result) >= max_k:
            break
    return result or [message.split()[0]]


def _parse_symbol(result_line: str) -> str | None:
    """Extract symbol name from a search result line: '[Class] Name (File: ...)'"""
    if "] " in result_line and " (File:" in result_line:
        return result_line.split("] ")[1].split(" (File:")[0].strip()
    return None


# ─── Groq streaming ───────────────────────────────────────────────────────────

_PERSONAS = {
    "developer": "You are a senior software engineer analyzing a codebase. Focus on architecture, implementation details, and code quality.",
    "product": "You are a product manager. Explain technical concepts in business terms. Focus on features and user impact.",
    "legal": "You are a legal analyst reviewing code. Focus on compliance, data handling, and potential legal risks.",
}


async def _stream_groq(
    message: str,
    persona: str,
    context: str,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    from groq import Groq

    system_msg = _PERSONAS.get(persona, _PERSONAS["developer"])

    # Build message list: system + conversation history + current user turn
    messages: list[dict] = [{"role": "system", "content": system_msg}]
    for h in history[-10:]:  # last 10 turns to stay within token budget
        role = h.get("role", "user")
        content = h.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({
        "role": "user",
        "content": (
            f"Relevant code graph context:\n\n{context}\n\n"
            f"Question: {message}"
        ),
    })

    q: queue.Queue = queue.Queue()
    _DONE = object()

    def _run() -> None:
        try:
            client = Groq(api_key=settings.groq_api_key)
            stream = client.chat.completions.create(
                model=settings.groq_model_fast,
                messages=messages,
                stream=True,
                max_tokens=1024,
                temperature=0.4,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    q.put(delta)
        except Exception as exc:
            q.put(exc)
        finally:
            q.put(_DONE)

    threading.Thread(target=_run, daemon=True).start()
    loop = asyncio.get_event_loop()
    while True:
        item = await loop.run_in_executor(None, q.get)
        if item is _DONE:
            break
        if isinstance(item, Exception):
            raise item
        yield _emit({"type": "token", "content": item})


async def _stream_fallback(context: str) -> AsyncGenerator[str, None]:
    for char in context:
        yield _emit({"type": "token", "content": char})
        await asyncio.sleep(0.002)


# ─── Main generator ───────────────────────────────────────────────────────────

async def _generate(req: ChatRequest) -> AsyncGenerator[str, None]:
    aggregated_context: list[str] = []
    already_fetched_symbols: set[str] = set()

    # ── Domain context (primary) ──────────────────────────────────────────────
    if req.domainId:
        tool_id = str(uuid.uuid4())[:8]
        yield _emit({"type": "tool_call_start", "tool": "get_domain", "args": {"domain_id": req.domainId}, "id": tool_id})
        t0 = time.monotonic()
        domain_name, domain_ctx = _fetch_domain_context(req.domainId)
        ms = int((time.monotonic() - t0) * 1000)
        yield _emit({"type": "tool_call_end", "id": tool_id, "result": domain_ctx or "Domain not found", "durationMs": ms})
        if domain_ctx:
            aggregated_context.append(domain_ctx)

    # ── Keyword search (supplemental) ─────────────────────────────────────────
    keywords = _extract_keywords(req.message)
    for kw in keywords:
        tool_id = str(uuid.uuid4())[:8]
        yield _emit({"type": "tool_call_start", "tool": "search_nodes", "args": {"keyword": kw}, "id": tool_id})

        t0 = time.monotonic()
        result = _search(kw)
        ms = int((time.monotonic() - t0) * 1000)
        yield _emit({"type": "tool_call_end", "id": tool_id, "result": result, "durationMs": ms})

        if "No nodes found" not in result:
            aggregated_context.append(result)

            # Get deep context for the top symbol from this search
            first_line = result.split("\n")[0]
            symbol = _parse_symbol(first_line)
            if symbol and symbol not in already_fetched_symbols:
                already_fetched_symbols.add(symbol)
                ctx_id = str(uuid.uuid4())[:8]
                yield _emit({"type": "tool_call_start", "tool": "get_code_context", "args": {"symbol_name": symbol}, "id": ctx_id})
                t1 = time.monotonic()
                ctx_result = _context(symbol)
                ctx_ms = int((time.monotonic() - t1) * 1000)
                yield _emit({"type": "tool_call_end", "id": ctx_id, "result": ctx_result, "durationMs": ctx_ms})
                if "not found" not in ctx_result.lower():
                    aggregated_context.append(ctx_result)

    full_context = "\n\n---\n\n".join(aggregated_context) if aggregated_context else ""

    if settings.groq_api_key:
        try:
            async for chunk in _stream_groq(req.message, req.persona, full_context, req.history):
                yield chunk
        except Exception as exc:
            logger.error("Groq error: %s", exc)
            async for chunk in _stream_fallback(full_context or "No relevant code found."):
                yield chunk
    else:
        async for chunk in _stream_fallback(full_context or "No relevant code found. Set GROQ_API_KEY for LLM answers."):
            yield chunk

    yield _emit({"type": "done"})
    yield "data: [DONE]\n\n"


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest, _=Depends(current_user)):
    return StreamingResponse(
        _generate(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
