# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

CodeLens is a code intelligence layer for AI agents. It parses Java/Python codebases into a Neo4j knowledge graph and exposes the graph via an MCP server so AI agents (Claude Code, Cursor, etc.) can query structural context (callers, callees, domains) rather than relying on text search alone.

The system has three tiers:
1. **Python backend** (`src/codelens/`) — CLI, AST parsers, Neo4j client, MCP server, FastAPI auth layer
2. **Next.js frontend** (`frontend/`) — admin panel + demo UI (chat at `/ask`, force-directed graph at `/graph`)
3. **Neo4j** — graph database, runs via Docker

## Commands

### Backend (Python)

```bash
# Install in dev mode (from repo root, with venv active)
source .venv/bin/activate
pip install -e ".[dev]"

# Lint
ruff check src/ tests/

# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_java_parser.py -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests (require Neo4j)
pytest tests/integration/
```

### CLI

```bash
# Index a repo (in-memory only, no Neo4j)
codelens index /path/to/java-repo --stats

# Parse + ingest into Neo4j (requires Neo4j running)
codelens ingest /path/to/java-repo --clear --cluster

# Start MCP server over stdio (for AI agent config)
codelens mcp

# Start MCP server over SSE (for Docker/web access)
codelens mcp --transport sse --port 8000

# Watch a repo for incremental re-indexing
codelens watch /path/to/java-repo
```

### Infrastructure

```bash
# Start Neo4j (required for ingest, MCP, and most integration tests)
docker compose up -d neo4j

# Start Neo4j + MCP server together
docker compose up -d
```

### Frontend (Next.js)

```bash
cd frontend

# Dev server (Turbopack)
pnpm dev

# Type check
pnpm typecheck

# Lint
pnpm lint

# Build
pnpm build
```

## Architecture

### Python package (`src/codelens/`)

- `settings.py` — Pydantic `Settings` singleton; reads `.env`. All config flows through here.
- `cli.py` — Click CLI; commands: `index`, `ingest`, `watch`, `mcp`.
- `indexer/` — AST parsing pipeline:
  - `models.py` — `CodeNode`, `CodeEdge`, `ParseResult` (Pydantic); `NodeType` and `EdgeType` enums.
  - `java_parser.py` — Tree-sitter Java parser; emits nodes/edges for classes, methods, constructors, conditionals, calls, imports.
  - `python_parser.py` — Tree-sitter Python parser (same output shape).
  - `indexer.py` — Walks a repo, dispatches files to the right parser, aggregates into `ParseResult`.
- `graph/` — Neo4j layer:
  - `neo4j_client.py` — Driver wrapper; `setup_schema()`, `ingest_parse_result()`, `clear_database()`.
  - `clustering.py` — Leiden community detection via `cdlib`/`networkx`; calls Gemini Flash once per cluster for domain naming.
- `mcp_server/server.py` — FastMCP tools: `search_nodes`, `get_code_context`, `get_callers`, `get_callees`, `get_domains`, `get_domain`.
- `watcher.py` — `watchdog`-based daemon for incremental re-indexing on file changes.
- `api/` — FastAPI app for JWT auth and admin REST endpoints (partially implemented).

### Frontend (`frontend/`)

Next.js 15 App Router with React 19, TypeScript, Tailwind v4, shadcn/ui, TanStack Query.

**Route groups:**
- `(auth)` — `/login` — unauthenticated
- `(demo)` — `/ask` (chat UI), `/graph` (force-directed graph) — requires any valid JWT
- `(admin)` — `/admin/*` (dashboard, repos, domains, users) — requires `role: admin` in JWT

**Auth flow:** `middleware.ts` reads a `codelens_token` JWT cookie and redirects unauthenticated/unauthorized requests. The cookie is set by `/api/auth/login` Next.js route handler, which proxies to the FastAPI backend.

**API client:** `frontend/lib/api/client.ts` — wraps `fetch` with retry on idempotent methods, throws `ApiError`. Base URL from `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`). Set `NEXT_PUBLIC_MOCK_MODE=true` to use `lib/api/mocks.ts` instead of hitting the real backend.

**Key components:**
- `components/graph/DomainGraph.tsx` — `react-force-graph-2d` visualization of the Neo4j graph
- `components/chat/` — streaming SSE chat UI (`lib/api/sse.ts` for the EventSource wrapper)
- `components/admin/` — table/card components for the admin panel

## Environment

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Notes |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Use `bolt://neo4j:7687` inside Docker |
| `NEO4J_PASSWORD` | `codelens_dev` | Must match Docker Compose config |
| `GEMINI_API_KEY` | — | Required for domain clustering/naming |
| `JWT_SECRET_KEY` | `change_me_to_a_random_secret` | Change before any shared deployment |

Frontend-specific (in `frontend/.env.local`):
- `NEXT_PUBLIC_API_BASE_URL` — FastAPI backend URL (default `http://localhost:8000`)
- `NEXT_PUBLIC_MOCK_MODE` — set to `true` to bypass the backend entirely

## Tests

Unit tests (`tests/unit/`) do not require Neo4j or any external service. Integration tests (`tests/integration/`) require a running Neo4j instance. The `test_cli_smoke.py` integration test requires Spring PetClinic at `tests/fixtures/spring-petclinic/` (already present as a shallow clone).

Tests use `pytest-asyncio` with `asyncio_mode = "auto"` — no explicit `@pytest.mark.asyncio` needed.
