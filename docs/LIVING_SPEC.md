# CodeLens — Living Specification

> **Status:** Active — this document supersedes `CodeLens_Project_Specification.md` for implementation decisions. 
> **Last updated:** April 2026 
> **Version:** 0.2

---

## What CodeLens Is

CodeLens is a **code intelligence infrastructure layer** — not a chatbot, not a code assistant.

It indexes a codebase into a structured knowledge graph (Neo4j), extracts business rules from that graph using LLM preprocessing, and exposes the result through a **Model Context Protocol (MCP) server** so that any AI agent (Claude Code, Codex, Cursor, etc.) can query it with graph-accuracy.

The product is the **MCP server + the indexed knowledge graph**. The AI client is not our concern.

> "We don't ask people to switch their AI tool. We make their existing AI tool dramatically smarter about their codebase."

---

## Core Architecture

```
[ Git Repository ]
 ↓
 [ Ingestion Layer ]
 Tree-sitter (AST parsing)
 GitPython (git history)
 ↓
 [ Neo4j Graph DB ]
 Code nodes: File, Module, Class, Function, ConditionalBranch
 Rule nodes: extracted business rules (3 persona variants)
 Vector index: semantic search over all nodes
 ↓
 [ Rule Extractor ] ← background job, runs at index time
 Python + LLM API (Gemini Flash / GPT-4o-mini)
 Produces: Rule nodes with developer/product/legal variants
 ↓
 [ MCP Server ] ← THE PRODUCT
 Exposes graph as tools to any MCP-compatible agent
 ↓
 [ Client AI ] ← not our product
 Claude Code / Codex / Cursor / any MCP-compatible agent
```

---

## The Three Layers Explained

### Layer 1 — Ingestion and Indexing

Tree-sitter parses the codebase into an AST. The indexer extracts:

**Nodes:** `File`, `Class`, `Function`, `ConditionalBranch`, `ReturnStatement` 
**Edges:** `calls`, `imports`, `defines`, `contains`, `returns`

Each node is stored in Neo4j with:
- File path and line number
- A vector embedding (for semantic search)
- A `stale` flag (for incremental re-indexing)

CLI: `codelens index --repo ./path`

---

### Layer 2 — Business Rule Extraction (The Intelligence Layer)

This is what separates CodeLens from a plain code indexer.

After indexing, a background Python job traverses `ConditionalBranch` nodes, aggregates the surrounding code subgraph, and sends it to an LLM with a structured extraction prompt.

The output is a `Rule` node stored in Neo4j with **three pre-rendered persona fields**:

| Field | Description | Example |
|---|---|---|
| `developer_text` | Technical explanation, code references, types |"The `apply_discount()` function in `pricing.py:L142` applies a capped discount (max 20%) only when `user.is_premium == True` AND `cart.total > 500`" |
| `product_text` | Plain English, scenario-based, zero code | "Premium users qualify for a discount of up to 20% on orders over $500." |
| `legal_text` | Policy-clause format, audit-ready | "4.2 — A discount not exceeding 20% shall be applied to orders exceeding $500.00 placed by accounts holding Premium status." |

Every Rule node also stores:
- `domain` tag (e.g., "Checkout", "Payments", "Auth") — assigned via semantic clustering
- `confidence_score` — LLM confidence in the extraction
- `source_nodes[]` — edges back to the exact code nodes this rule was derived from
- `last_extracted_at` — for staleness tracking

**Persona is a database concern, not a client AI concern.** The MCP tool accepts `persona` as a query parameter and returns the pre-rendered field. No LLM call at query time.

---

### Layer 3 — MCP Server (The Product Surface)

The MCP server exposes the graph as tools. Any MCP-compatible client (Claude Desktop, Claude Code, Cursor, Codex) calls these tools.

**Core Tools:**

```python
search_rules(query: str, persona: str = "developer") -> list[Rule]
# Semantic search over Rule nodes. Returns pre-rendered persona variant.

get_domain_rules(domain: str, persona: str = "developer") -> list[Rule]
# Returns all rules tagged to a specific domain.

get_rule_detail(rule_id: str, persona: str = "developer") -> Rule
# Returns a single rule with full source traceability.

get_domains() -> list[Domain]
# Returns all discovered domain clusters with rule counts.

get_code_context(function_name: str) -> SubGraph
# Returns the raw code subgraph around a function (for developers who want the raw graph).

search_code(query: str) -> list[CodeNode]
# Semantic search over raw code nodes (not rules). Full structural context.
```

**Persona parameter behavior:**
- `"developer"` → returns `rule.developer_text` + source code references
- `"product"` → returns `rule.product_text` only, no code references
- `"legal"` → returns `rule.legal_text` + source file citations (for traceability)

---

## Incremental Re-Indexing

When code changes, the system re-indexes only what changed:

| Step | Action |
|---|---|
| Webhook / CLI trigger | Push event or `codelens index --update` |
| File diff | Identify changed files |
| Stale marking | Mark affected code nodes + dependent Rule nodes as stale |
| Selective re-parse | Tree-sitter re-parses only changed files |
| Rule re-extraction | LLM re-extracts only stale Rule nodes |
| Cache invalidation | Affected MCP tool cache entries invalidated |

CLI: `codelens index --update --repo ./path`

---

## PR Change Simulator

When a PR is opened/updated:

1. Check out base and head branches
2. Run incremental indexing on head
3. Diff Rule nodes: base vs head
4. Classify changes: `RULE_ADDED`, `RULE_MODIFIED`, `RULE_REMOVED`
5. Generate a plain-English impact summary (one small LLM call)
6. Post structured comment to PR

Example PR comment:
> **Business logic changed in this PR:**
> - **MODIFIED:** Premium discount cap raised from 15% → 20% (`pricing.py:L142`)
> - **REMOVED:** New user grace period rule (was 30 days, now absent)
> - **ADDED:** Bulk order rule: orders > 100 units bypass standard discount logic

CLI dry-run: `codelens simulate --base main --head feature/pricing`

---

## Demo Layer (Not the Product)

A lightweight demo interface for showing the system to non-technical stakeholders. 
**This is throwaway scaffolding — not intended for production use.**

```
Streamlit UI (simple chat interface + persona dropdown)
 ↓
FastAPI backend (auth-protected)
 ↓
OpenAI Agents SDK with CodeLens MCP tools registered
 ↓
Same Neo4j / MCP server underneath
```

The persona dropdown in Streamlit passes the `persona` parameter to the MCP tool calls. No extra LLM calls — it just changes which pre-rendered field comes back.

---

## Authentication and Authorization

### Key Design Decision: Roles and Personas Are Separate Concerns

**Personas** (`developer`, `product`, `legal`) are purely a **UX / presentation preference**. Any authenticated user can freely select any persona. Personas carry no security enforcement — they are just a parameter that selects which pre-rendered field to return from Neo4j.

**Roles** (`user`, `admin`) are **security roles** that control access to system management functions. They are independent of persona.

> Conflating roles with personas would be wrong. A PM might occasionally need to see a code reference. A developer might want a plain-English summary. Locking personas to security roles creates unnecessary friction.

---

### Security Roles

| Role | Access |
|---|---|
| `user` (default) | All MCP tools, demo UI chat, any persona parameter freely |
| `admin` | Everything `user` has + Admin Panel (CRUD for repos, rules, users) |

### Auth Mechanism

- FastAPI issues a **signed JWT** on login containing `{ user_id, role, email }`
- All MCP tool calls require `Authorization: Bearer <token>` header
- Demo UI stores token in session on login
- Admin routes return `403 Forbidden` to non-admin tokens
- Token issuance via `/auth/login` (username + password for MVP; GitHub OAuth as upgrade path)

### Auth Endpoints (FastAPI)

```
POST /auth/register → Create new user account (admin-only)
POST /auth/login → Returns signed JWT
POST /auth/logout → Invalidates session
GET /auth/me → Returns current user info
```

---

## Admin Panel

A separate admin-only UI for managing the CodeLens system. Satisfies CRUD and RBAC course requirements.

### Access
- Protected: requires `role == admin` on JWT
- Implemented as a Streamlit admin page or minimal FastAPI + HTML

### CRUD Operations

| Operation | Action |
|---|---|
| **Create** | Register a new repository (GitHub URL + paths to monitor) |
| **Read** | Browse indexed repos, Rule nodes with confidence scores, job history |
| **Update** | Trigger full or incremental re-index, manually edit a Rule node's text, mark as `human_verified` |
| **Delete** | Remove a repository from the index, delete an incorrectly extracted Rule node |

### User Management (Admin)
- List all users and their roles
- Promote a user to admin
- Revoke access / delete user

### Rule Correction Flow
When the LLM extracts a rule incorrectly, an admin can:
1. Open the rule in the admin panel
2. Edit any of the three persona text fields directly
3. Save with `human_verified: true` flag

This builds trust in the knowledge base over time and provides a feedback loop for improving extraction prompts.

---

## Definitive Tech Stack

### Core (The Product)
| Component | Technology |
|---|---|
| AST Parsing | Tree-sitter (Python, TypeScript — MVP languages) |
| Graph Database | Neo4j AuraDB Free |
| Vector Search | Neo4j built-in vector index |
| Rule Extractor | Python + Gemini 2.0 Flash (free tier) |
| Background Jobs | Python `BackgroundTasks` (FastAPI) or simple Celery (if needed) |
| MCP Server | Python MCP SDK (`mcp` package) |
| API Backend | FastAPI |
| CLI | Python Click |

### Demo Only (Not the Product)
| Component | Technology |
|---|---|
| Demo UI | Streamlit |
| Demo Agent | OpenAI Agents SDK or simple LLM API call |

### Infrastructure
| Component | Technology |
|---|---|
| Graph DB (cloud) | Neo4j AuraDB Free |
| Backend hosting | Railway / Render (free tier) |
| GitHub integration | GitHub Webhooks + GitHub App |

---

## What Is Out of Scope

- Custom chatbot UI (not our product)
- Persona rendering logic at query time (pre-rendered at index time)
- LangGraph for query orchestration (dropped, no runtime agent needed)
- Separate vector database (Neo4j handles this natively)
- Full Next.js production dashboard (Streamlit demo is sufficient for MVP)
- Redis / Celery for MVP (use FastAPI BackgroundTasks first)
- Role-based persona enforcement (personas are free UX parameters, not security gates)

---

## Development Phases (Revised)

### Phase 1 — Core Graph (Weeks 1–2)
- Tree-sitter parsing pipeline for Python and TypeScript
- Neo4j schema implementation
- Entity and edge extraction working
- CLI indexer running on a real repository

**Gate:** A real codebase indexed into Neo4j with queryable graph structure.

### Phase 2 — Rule Extraction (Weeks 3–4)
- LLM extraction pipeline for `ConditionalBranch` traversal
- Rule node creation with all three persona fields
- Domain clustering via semantic similarity
- Confidence scoring

**Gate:** Rule nodes visible in Neo4j with developer/product/legal variants populated.

### Phase 3 — MCP Server (Weeks 5–6)
- All core MCP tools implemented
- Tested end-to-end with Claude Desktop and Claude Code
- Incremental re-indexing pipeline working
- CLI search and simulate commands

**Gate:** Claude Code can query the indexed codebase and receive persona-appropriate rule explanations.

### Phase 4 — Auth, Admin Panel + Demo (Weeks 7–8)
- FastAPI auth endpoints (register, login, logout, JWT issuance)
- MCP server JWT validation middleware
- Admin panel: repo CRUD, rule editing, user management
- Streamlit demo UI with login + persona dropdown
- GitHub webhook integration
- PR diff logic and automated comment posting
- End-to-end demo on a live pull request

**Gate:** Full authenticated demo ready for stakeholder presentation. Admin can manage repos and correct rules. Users can query via MCP and demo UI.

---

## Success Metrics

| Metric | Target |
|---|---|
| Indexing speed | < 5 min for 100k LOC |
| Rule extraction accuracy | > 90% precision on human-validated sample |
| MCP query latency | < 2 sec for rule search |
| PR simulation latency | < 45 sec from push to posted comment |
| Demo cost | $0–5/month (free-tier infrastructure) |

---

## Open Questions

1. **Rule extraction granularity:** Do we extract one Rule per `ConditionalBranch`, or group related branches into a single Rule? (Significant impact on rule count and quality.)
2. **Language priority:** Python + TypeScript for MVP confirmed. Java or Go next?
3. **Webhook vs polling:** GitHub webhook requires a public server. For local dev, do we support `codelens index --watch` polling as fallback?
4. **Multi-repo:** Does a single CodeLens instance index one repo or many? MVP scope should be single-repo.
5. **Auth upgrade path:** MVP uses username/password + JWT. Is GitHub OAuth the right upgrade for v2 given the developer-first audience?
6. **Admin UI technology:** Streamlit admin page vs minimal FastAPI + HTML — which is faster to build and maintain?
