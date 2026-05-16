## Seed Example Data

Run the following Cypher in Neo4j Browser (http://localhost:7474):

```cypher
CREATE (a:File {name: "app.py"});
CREATE (b:File {name: "db.py"});
CREATE (c:File {name: "auth.py"});
> Status: In development -- Phase 1 (CLI + Java parser) implemented and tested.

CREATE (a)-[:IMPORTS]->(b);
CREATE (a)-[:IMPORTS]->(c);
### Connection

- Neo4j HTTP: http://localhost:7474
- Neo4j Bolt: bolt://localhost:7687
- Default credentials: neo4j / codelens_dev
**The product is the MCP server + the knowledge graph.** Not a chatbot. Not another AI tool. An intelligence layer that makes your existing AI tools dramatically smarter about your codebase.

---

## How It Works

1. **Indexes your codebase as a structured graph** -- functions, classes, call chains, conditional branches, all linked with precise relationships in Neo4j.
2. **Identifies business domains automatically** -- a community detection algorithm clusters related code into domains. A single LLM call per domain generates a human-readable name, summary, and observed business rules.
3. **Serves structural context through MCP** -- any MCP-compatible agent can call `get_code_context("apply_discount")` and get back a multi-hop subgraph of callers, callees, conditionals, and the domain it belongs to.
4. **Hybrid discovery** -- the AI agent primarily uses its own tools (grep, etc.) or our lightweight native Lucene search (`search_nodes`) to find entry points, then calls CodeLens for structural context (see [ADR-002](docs/decisions/ADR-002-code-discovery-strategy.md)).
5. **Query-time interpretation** -- business rule synthesis is performed by the client AI at query time, not pre-computed at index time (see [ADR-001](docs/decisions/ADR-001-rule-interpretation-strategy.md)).

---

## Prerequisites

- Python 3.11+
- Git

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/emirrozerr/code-lens.git
cd code-lens

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install CodeLens in development mode
pip install -e ".[dev]"

# Verify the installation
codelens --version
```

### Index a Java Repository

```bash
# Index any Java project (e.g. Spring PetClinic)
git clone --depth 1 https://github.com/spring-projects/spring-petclinic.git /tmp/spring-petclinic
codelens index /tmp/spring-petclinic --stats

# Export the parse result as JSON for inspection
codelens index /tmp/spring-petclinic --output result.json
```

### Run Tests

```bash
# Run the full test suite (unit + integration + smoke)
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests (includes CLI smoke tests)
pytest tests/integration/
```

### Testing Against Spring PetClinic

Some integration tests validate against the [Spring PetClinic](https://github.com/spring-projects/spring-petclinic) repo. To enable these:

```bash
git clone --depth 1 https://github.com/spring-projects/spring-petclinic.git tests/fixtures/spring-petclinic
pytest tests/integration/test_cli_smoke.py -v
```

These tests are automatically skipped if the PetClinic repo is not present.

---

## CLI Reference

```
codelens index <REPO_PATH> [OPTIONS]

Options:
  -v, --verbose    Enable debug logging
  -s, --stats      Print detailed statistics (classes, methods, branches)
  -o, --output     Write parse result as JSON to a file
  --help           Show help message
```

**Example output:**

```
  CodeLens Indexer
  ────────────────────────────────────────
  Repository:  /tmp/spring-petclinic

  Nodes (379 total)
  ──────────────────────────────
    Class                       44
    ConditionalBranch           40
    Constructor                  6
    File                        47
    Function                   164
    Interface                    3
    ReturnStatement             75

  Edges (1339 total)
  ──────────────────────────────
    calls                      572
    contains                   217
    extends                      8
    has_branch                  40
    imports                    427
    returns                     75

  ✓ Done
```

---

## Project Structure

```
src/codelens/
  cli.py            CLI entry point (Click-based)
  settings.py       Central configuration loaded from .env
  indexer/
    models.py       Pydantic data models (CodeNode, CodeEdge, ParseResult)
    java_parser.py  Tree-sitter Java AST parser
    indexer.py      Repository walker and file orchestrator
  graph/            Neo4j connection, schema management (coming soon)
  mcp_server/       MCP tool handlers (coming soon)
  api/              FastAPI app (coming soon)
tests/
  unit/             Unit tests for parser
  integration/      Integration tests for indexer + CLI smoke tests
  fixtures/         Sample Java repos for testing
docs/               Living spec, ADRs, requirements
```

---

## MCP Tools (Coming in Phase 2)

Once the MCP server is running and configured in your AI client, these tools become available:

| Tool | Description |
|---|---|
| `search_nodes(keyword)` | Native Lucene full-text search on node names, docstrings, and file paths |
| `get_code_context(symbol)` | Multi-hop subgraph around a function or class |
| `get_callers(symbol)` | All functions that call the given symbol |
| `get_callees(symbol)` | All functions called by the given symbol |
| `get_domain(symbol)` | The business domain a symbol belongs to, with summary |
| `get_domains()` | All discovered business domains with names and summaries |
| `get_domain_content(domain)` | All functions and classes in a domain cluster |

---

## Tech Stack

| Component | Technology |
|---|---|
| AST Parsing | Tree-sitter (Java -- MVP language) |
| Graph Database | Neo4j (local via Docker, production via AuraDB) |
| Community Detection | Leiden algorithm (Neo4j GDS or graspologic) |
| Domain Summaries | Google Gemini Flash (one call per domain cluster) |
| MCP Server | Python MCP SDK |
| API Backend | FastAPI + JWT auth |
| CLI | Python Click |

---

## Documentation

| Document | Description |
|---|---|
| [LIVING_SPEC.md](docs/LIVING_SPEC.md) | Full living specification -- architecture, data model, auth, phases |
| [ADR-001](docs/decisions/ADR-001-rule-interpretation-strategy.md) | Rule interpretation is query-time, not index-time |
| [ADR-002](docs/decisions/ADR-002-code-discovery-strategy.md) | Hybrid discovery: agent-led + Lucene keyword search |
| [ADR-003](docs/decisions/ADR-003-presentation-tier-strategy.md) | Presentation tier strategy (proposed, not yet decided) |
| [Requirements Alignment](docs/requirements-alignment.md) | Course requirements mapped to project design |

---

## Development Phases

| Phase | Scope | Status |
|---|---|---|
| 1 -- Core Ingestion | Tree-sitter Java parser, CLI indexer, file watcher | 🟡 In progress |
| 2 -- Graph + MCP | Neo4j schema, Lucene index, MCP server | ⬜ Planned |
| 3 -- Intelligence | Domain clustering (Leiden), LLM domain summaries | ⬜ Planned |
| 4 -- Auth + UI | JWT auth, admin panel, demo interface | ⬜ Planned |
| 5 -- Testing + Docs | Full pytest suite, CI, documentation, final report | ⬜ Planned |
