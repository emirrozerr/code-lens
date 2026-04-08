# CodeLens

**GraphRAG-Powered Code Intelligence Infrastructure**

> Status: Pre-development — specification complete, implementation not yet started.

CodeLens indexes your codebase into a structured knowledge graph, extracts business rules using LLM preprocessing, and exposes everything through a **Model Context Protocol (MCP) server** — so your existing AI agents (Claude Code, Codex, Cursor) can query your codebase with graph-level accuracy.

**The product is the MCP server + the knowledge graph.** Not a chatbot. Not another AI tool. An intelligence layer that makes your existing AI tools dramatically smarter about your codebase.

---

## What It Does

1. **Indexes your codebase as a structured graph** — functions, classes, call chains, conditional branches, all linked with precise relationships in Neo4j.
2. **Extracts business rules automatically** — a background LLM pipeline reads the graph and produces plain-English rule statements, stored back in the database with full code traceability.
3. **Serves those rules through MCP** — any MCP-compatible agent can call `search_rules("discount logic")` and get back accurate, graph-grounded, pre-rendered rule context.
4. **Supports persona-aware retrieval** — every rule is pre-rendered at index time in three variants: Developer (technical), Product (plain English), Legal (policy clause). The client AI requests which persona it needs.
5. **Detects business logic changes in PRs** — diffs rule subgraphs between branches and posts structured impact summaries directly to the PR.

---

## Who Uses It and How

| Audience | Interface | How they use CodeLens |
|---|---|---|
| Software Engineers | Claude Code / Cursor / any MCP client | Agent queries CodeLens MCP tools for accurate context before writing or changing code |
| Product Managers | Streamlit demo UI (persona: product) | Ask natural language questions, receive business behavior explanations with zero code |
| Compliance / Legal | Streamlit demo UI (persona: legal) | Browse rules as policy clauses, export to PDF for audit packages |
| Admins | Admin Panel | Manage indexed repositories, edit extracted rules, manage user accounts |

---

## Prerequisites

- Python 3.11+
- Neo4j AuraDB account (free tier sufficient for development)
- An LLM API key — Gemini (free tier) or OpenAI
- Git

---

## Getting Started

> Setup instructions are in progress. The project is in the pre-development phase.

```bash
# Clone the repository
git clone https://github.com/emirrozerr/code-lens.git
cd code-lens

# (Coming in Phase 1) Index a repository
codelens index --repo ./path/to/your/repo

# (Coming in Phase 3) Search business rules
codelens search "discount rules"

# (Coming in Phase 4) Dry-run PR diff
codelens simulate --base main --head feature/my-branch
```

---

## Core MCP Tools

Once the MCP server is configured in your AI client, the following tools become available:

```python
search_rules(query, persona="developer")    # Semantic search over extracted Rule nodes
get_domain_rules(domain, persona)           # All rules for a domain (e.g. "Payments")
get_rule_detail(rule_id, persona)           # Single rule with full code traceability
get_domains()                               # All discovered business domains
search_code(query)                          # Semantic search over raw code graph
get_code_context(function_name)             # Structural subgraph around a function
```

---

## Persona Retrieval

Persona is a database concern, not a client AI concern. Rules are pre-rendered into three variants at index time. The MCP tool accepts `persona` as a parameter and returns the pre-stored field — no extra LLM call at query time.

| Persona | Content |
|---|---|
| `developer` | Technical rule + code file/line references + call chain context |
| `product` | Plain English explanation + example scenarios, no code |
| `legal` | Numbered policy clause + source file citations |

---

## Tech Stack

**Core (The Product)**

| Component | Technology |
|---|---|
| AST Parsing | Tree-sitter (Python + TypeScript) |
| Graph Database | Neo4j AuraDB |
| Rule Extractor | Python + Gemini 2.0 Flash (background job) |
| MCP Server | Python MCP SDK |
| API Backend | FastAPI |
| CLI | Python Click |

**Demo and Admin UI (not the core product)**

| Component | Technology |
|---|---|
| Demo Chat UI | Streamlit |
| Admin Panel | Streamlit |
| Demo Agent | OpenAI Agents SDK |

---

## Development Phases

| Phase | Scope | Weeks | Gate |
|---|---|---|---|
| 1 — Core Graph | Tree-sitter parsing, Neo4j schema, CLI indexer | 1–2 | Real codebase queryable in Neo4j |
| 2 — Rule Extraction | LLM extraction pipeline, Rule nodes, persona fields, domain clustering | 3–4 | Rule nodes with all three persona variants in Neo4j |
| 3 — MCP Server | All MCP tools, JWT auth, incremental re-indexing, CLI search | 5–6 | Claude Code querying the graph end-to-end |
| 4 — Auth, Admin + Demo | Auth endpoints, admin panel CRUD, Streamlit demo, PR simulator | 7–8 | Full authenticated demo ready |

---

## Documentation

| Document | Description |
|---|---|
| [docs/LIVING_SPEC.md](docs/LIVING_SPEC.md) | Full living specification — architecture, data model, auth, admin panel, tech stack |
| [docs/requirements-alignment.md](docs/requirements-alignment.md) | All course requirements mapped to the project with alignment status and action plan |
| [docs/multi-tier-project-requirements.md](docs/multi-tier-project-requirements.md) | Multi-Tier Application course requirements |
| [docs/Team-application-project-requirements.md](docs/Team-application-project-requirements.md) | Team Application Project course requirements |
| [docs/CodeLens_Project_Specification.md](docs/CodeLens_Project_Specification.md) | Original project specification (v1.0, superseded) |