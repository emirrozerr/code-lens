# CodeLens

**Code Intelligence Infrastructure for AI Agents**

> Status: In development -- project skeleton and architecture complete, Phase 1 implementation starting.

CodeLens indexes your codebase into a structured knowledge graph and exposes it through a **Model Context Protocol (MCP) server** -- so your existing AI agents (Claude Code, Cursor, Copilot) can query your codebase with graph-level structural accuracy.

**The product is the MCP server + the knowledge graph.** Not a chatbot. Not another AI tool. An intelligence layer that makes your existing AI tools dramatically smarter about your codebase.

---

## How It Works

1. **Indexes your codebase as a structured graph** -- functions, classes, call chains, conditional branches, all linked with precise relationships in Neo4j.
2. **Identifies business domains automatically** -- a community detection algorithm clusters related code into domains. A single LLM call per domain generates a human-readable name, summary, and observed business rules.
3. **Serves structural context through MCP** -- any MCP-compatible agent can call `get_code_context("apply_discount")` and get back a multi-hop subgraph of callers, callees, conditionals, and the domain it belongs to.
4. **Agent-led discovery** -- the AI agent uses its own tools (grep, file search, etc.) to find entry points, then calls CodeLens for structural context. CodeLens does not do search -- it provides the graph intelligence layer (see [ADR-002](docs/decisions/ADR-002-code-discovery-strategy.md)).
5. **Query-time interpretation** -- business rule synthesis is performed by the client AI at query time, not pre-computed at index time (see [ADR-001](docs/decisions/ADR-001-rule-interpretation-strategy.md)).

---

## Prerequisites

- Python 3.11+
- Docker (for local Neo4j)
- A Gemini API key (free tier sufficient -- [get one here](https://aistudio.google.com/apikey))
- Git

---

## Getting Started

```bash
# Clone the repository
git clone https://github.com/emirrozerr/code-lens.git
cd code-lens

# Set up environment
cp .env.example .env
# Edit .env with your Gemini API key

# Start Neo4j
docker compose up -d

# Install in development mode
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# (Coming in Phase 1) Index a repository
python -m codelens.indexer ./path/to/your/repo
```

---

## Project Structure

```
src/codelens/
  indexer/        Tree-sitter parsing, AST walking, node and edge extraction
  graph/          Neo4j connection, schema management, Cypher queries
  mcp_server/     MCP tool handlers for code graph traversal
  api/            FastAPI app (auth endpoints, admin routes, index triggers)
  settings.py     Central configuration loaded from .env
tests/
  unit/           Unit tests
  integration/    Integration tests (requires Neo4j)
docs/             Living spec, ADRs, requirements, data model
```

---

## MCP Tools

Once the MCP server is running and configured in your AI client, these tools become available:

| Tool | Description |
|---|---|
| `get_code_context(symbol)` | Multi-hop subgraph around a function or class -- callers, callees, conditionals, domain |
| `get_callers(symbol)` | All functions that call the given symbol |
| `get_callees(symbol)` | All functions called by the given symbol |
| `get_domain(symbol)` | The business domain a symbol belongs to, with summary |
| `get_domains()` | All discovered business domains with names and summaries |
| `get_domain_content(domain)` | All functions and classes in a domain cluster |

---

## Tech Stack

| Component | Technology |
|---|---|
| AST Parsing | Tree-sitter (Python + TypeScript) |
| Graph Database | Neo4j (local via Docker, production via AuraDB) |
| Community Detection | Leiden algorithm (Neo4j GDS or graspologic) |
| Domain Summaries | Google Gemini Flash (one call per domain cluster) |
| MCP Server | Python MCP SDK |
| API Backend | FastAPI + JWT auth |

---

## Documentation

| Document | Description |
|---|---|
| [LIVING_SPEC.md](docs/LIVING_SPEC.md) | Full living specification -- architecture, data model, auth, phases |
| [ADR-001](docs/decisions/ADR-001-rule-interpretation-strategy.md) | Rule interpretation is query-time, not index-time |
| [ADR-002](docs/decisions/ADR-002-code-discovery-strategy.md) | Code discovery is agent-led, no internal search |
| [ADR-003](docs/decisions/ADR-003-presentation-tier-strategy.md) | Presentation tier strategy (proposed, not yet decided) |
| [Requirements Alignment](docs/requirements-alignment.md) | Course requirements mapped to project design |

---

## Development Phases

| Phase | Scope | Priority |
|---|---|---|
| 1 -- Core Graph | Tree-sitter parsing, Neo4j schema, full re-index | P0 |
| 2 -- Intelligence | Domain clustering (Leiden), LLM domain summaries | P0 |
| 3 -- MCP Server | All six traversal tools, end-to-end testing | P0 |
| 4 -- Auth + UI | JWT auth, admin panel, demo interface | P1 |
| 5 -- Testing + Docs | pytest suite, CI, documentation, final report | P1 |