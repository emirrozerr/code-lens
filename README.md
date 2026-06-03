# CodeLens

**Code Intelligence Infrastructure for AI Agents**

CodeLens indexes Java and Python codebases into a Neo4j knowledge graph and exposes that graph through an MCP (Model Context Protocol) server and a REST API. AI agents (Claude Desktop, Claude Code, Cursor) can query structural context — callers, callees, business domains — instead of relying on plain text search.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      User Layer                         │
│  Claude Desktop / Claude Code / Cursor  (MCP clients)   │
│  Next.js Frontend  (demo chat + admin panel)            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        ▼                          ▼
┌───────────────┐        ┌──────────────────┐
│  MCP Server   │        │   FastAPI REST   │
│  (stdio/SSE)  │        │     port 8000    │
│   7 tools     │        │   JWT auth       │
└───────┬───────┘        └────────┬─────────┘
        └──────────┬──────────────┘
                   ▼
        ┌──────────────────┐
        │      Neo4j       │
        │  Graph Database  │
        │    port 7687     │
        └──────────────────┘
                   ▲
        ┌──────────────────┐
        │  AST Pipeline    │
        │  Java + Python   │
        │  (Tree-sitter)   │
        └──────────────────┘
```

**Three tiers:**
1. **Presentation** — Next.js 15 frontend: streaming chat (`/ask`), force-directed graph (`/graph`), admin panel (`/admin/*`)
2. **Application** — FastAPI REST API + MCP server + Groq LLM integration + community detection
3. **Data** — Neo4j graph database (code graph + admin data under separate labels)

---

## Tech Stack

| Layer | Technology |
|---|---|
| AST Parsing | Tree-sitter (`tree-sitter-java`, `tree-sitter-python`) |
| Graph Database | Neo4j (Docker) |
| Community Detection | python-louvain (Louvain algorithm) + NetworkX |
| LLM — domain naming | Groq `llama-3.3-70b-versatile` |
| LLM — chat | Groq `llama-3.1-8b-instant` (SSE streaming) |
| MCP Framework | FastMCP |
| REST API | FastAPI + Uvicorn |
| Authentication | JWT (python-jose) + bcrypt (passlib) |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind v4, shadcn/ui |
| Data Fetching | TanStack Query |
| Graph Visualization | react-force-graph-2d |

---

## Prerequisites

- Python 3.11+
- Node.js 20+ and pnpm
- Docker (for Neo4j)
- Groq API key — free at [console.groq.com](https://console.groq.com)

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/emirrozerr/code-lens.git
cd code-lens

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set:
#   GROQ_API_KEY=<your_key>
#   JWT_SECRET_KEY=<random_string>
```

### 3. Start Neo4j

```bash
docker compose up -d neo4j
```

### 4. Start the REST API

```bash
codelens api
# Listening on http://localhost:8000
```

### 5. Ingest a repository

```bash
# Spring PetClinic fixture is already included
codelens ingest tests/fixtures/spring-petclinic --clear --cluster
```

`--cluster` runs Louvain community detection and calls Groq to name each domain.

### 6. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev
# Open http://localhost:3000
```

---

## MCP Server Integration

### Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codelens": {
      "command": "C:\\path\\to\\code-lens\\.venv\\Scripts\\codelens.exe",
      "args": ["mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add codelens -- codelens mcp
```

### SSE mode (Docker / remote)

```bash
codelens mcp --transport sse --port 8000
# Endpoint: http://localhost:8000/sse
```

---

## MCP Tools

| Tool | Parameter | Description |
|---|---|---|
| `search_nodes` | `keyword` | Lucene fulltext search on names, signatures, file paths |
| `get_code_context` | `symbol_name` | Returns callers, callees, and branches for a symbol |
| `get_callers` | `symbol_name` | Everything that calls this symbol (impact analysis) |
| `get_callees` | `symbol_name` | Everything this symbol calls |
| `get_domains` | — | Lists all business domains with summaries |
| `get_domain` | `symbol_name` | Domain a symbol belongs to, plus all members |
| `get_domain_content` | `domain_name` | All members of a specific domain |

---

## REST API

| Endpoint | Method | Description | Auth |
|---|---|---|---|
| `/auth/login` | POST | Login, returns JWT cookie | Public |
| `/auth/logout` | POST | Clear JWT cookie | — |
| `/auth/me` | GET | Current user info | User |
| `/api/repos` | GET / POST | List / add repositories | Admin |
| `/api/repos/{id}/reindex` | POST | Trigger re-indexing | Admin |
| `/api/repos/{id}` | DELETE | Delete repository | Admin |
| `/api/jobs` | GET | Indexing job history | Admin |
| `/api/domains` | GET | List domains | Admin |
| `/api/graph` | GET | Graph nodes/edges for visualization | User |
| `/api/stats` | GET | Aggregate statistics | Admin |
| `/api/users` | GET / POST | User management | Admin |
| `/chat` | POST | SSE streaming chat | User |

Full OpenAPI docs available at `http://localhost:8000/docs` when the API is running.

---

## CLI Reference

```
codelens index   <REPO_PATH> [--stats] [--output FILE]   Parse only (no Neo4j)
codelens ingest  <REPO_PATH> [--clear] [--cluster]       Parse + store in Neo4j
codelens mcp     [--transport stdio|sse] [--port PORT]   Start MCP server
codelens api     [--host HOST] [--port PORT]             Start REST API
codelens watch   <REPO_PATH>                             Incremental re-indexer
```

---

## Tests

```bash
pytest                        # all tests
pytest tests/unit/            # unit tests (no Neo4j required)
pytest tests/integration/     # integration tests (Neo4j required)
pytest tests/unit/ -v --cov   # with coverage report
```

Unit tests do not require Neo4j or any external service. Integration tests require a running Neo4j instance (`docker compose up -d neo4j`).

---

## Project Structure

```
code-lens/
├── src/codelens/
│   ├── settings.py            Single config source (Pydantic, reads .env)
│   ├── cli.py                 Click CLI
│   ├── indexer/
│   │   ├── models.py          CodeNode, CodeEdge, ParseResult
│   │   ├── java_parser.py     Tree-sitter Java parser
│   │   ├── python_parser.py   Tree-sitter Python parser
│   │   └── indexer.py         Repo walker
│   ├── graph/
│   │   ├── neo4j_client.py    Driver wrapper, schema, ingestion
│   │   └── clustering.py      Louvain + Groq → Domain nodes
│   ├── mcp_server/
│   │   └── server.py          FastMCP — 7 tool definitions
│   ├── api/
│   │   ├── __init__.py        FastAPI app, CORS, router registration
│   │   ├── auth.py            Login / logout / me
│   │   ├── chat.py            SSE streaming chat + Groq
│   │   ├── repos.py           Repository CRUD + background indexing
│   │   ├── domains.py         Domain endpoints
│   │   ├── graph.py           Visualization data
│   │   ├── users.py           User management
│   │   ├── jobs.py            Job history
│   │   ├── stats.py           Statistics
│   │   ├── store.py           Neo4j-backed admin data layer
│   │   └── deps.py            JWT dependency injection
│   └── watcher.py             watchdog incremental re-indexer
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/      Login page
│   │   ├── (demo)/ask/        Streaming chat UI
│   │   ├── (demo)/graph/      Force-directed graph
│   │   └── (admin)/admin/     Dashboard, repos, domains, users
│   ├── components/
│   │   ├── chat/              MessageBubble, DomainSidebar, PersonaToggle
│   │   ├── graph/             DomainGraph (react-force-graph-2d)
│   │   └── admin/             Tables and cards
│   └── lib/
│       ├── api/               client.ts, sse.ts, endpoints.ts
│       └── auth.tsx           useAuth hook
├── tests/
│   ├── unit/                  Parser and model tests
│   ├── integration/           Neo4j and CLI smoke tests
│   └── fixtures/spring-petclinic/   Demo Java repo
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── PROJECT_REPORT.md          Full technical report
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Use `bolt://neo4j:7687` inside Docker |
| `NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `codelens_dev` | Must match Docker Compose config |
| `GROQ_API_KEY` | — | Required for domain clustering and chat |
| `GROQ_MODEL_FAST` | `llama-3.1-8b-instant` | Chat streaming model |
| `GROQ_MODEL_QUALITY` | `llama-3.3-70b-versatile` | Domain naming model |
| `JWT_SECRET_KEY` | `change_me` | Change before any shared deployment |
| `JWT_EXPIRY_MINUTES` | `1440` | Token lifetime (24 hours) |

Frontend (`frontend/.env.local`):

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | FastAPI backend URL |
| `NEXT_PUBLIC_MOCK_MODE` | — | Set to `true` to bypass backend |
