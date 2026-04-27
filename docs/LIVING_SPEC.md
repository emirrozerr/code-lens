# CodeLens — Living Specification

> **Status:** Active — this document supersedes `CodeLens_Project_Specification.md` for implementation decisions. 
> **Last updated:** April 2026 
> **Version:** 0.3

---

## What CodeLens Is

CodeLens is a **code intelligence infrastructure layer** — not a chatbot, not a code assistant.

It parses a codebase into a structured knowledge graph (Neo4j) and exposes that graph through a **Model Context Protocol (MCP) server**. When an AI agent (Claude Code, Codex, Cursor, etc.) needs to understand how part of a codebase works, it uses its own discovery tools to find the relevant symbol, then calls CodeLens to get the full structural context: call chains, dependencies, callers, domain cluster. The agent's LLM interprets the subgraph and synthesises the answer.

The product is the **graph + the MCP server**. Discovery and interpretation happen in the client AI. CodeLens provides structural truth.

> "We don't ask people to switch their AI tool. We make their existing AI tool dramatically smarter about their codebase."

**Key architectural decisions:**
- ADR-001: Rule interpretation is query-time (client AI reads the subgraph) — no pre-extracted Rule nodes, no index-time LLM pipeline
- ADR-002: Code discovery is agent-led — no semantic or keyword search inside CodeLens for MVP

---

## Core Architecture

```
[ Git Repository ]
        ↓
 [ Ingestion Layer ]
 Tree-sitter (AST parsing)
 GitPython (git history, domain clustering)
        ↓
 [ Neo4j Graph DB ]
 Code nodes: File, Module, Class, Function, ConditionalBranch
 Domain nodes: cluster summaries (community detection)
 Edges: calls, imports, defines, contains, returns
        ↓
 [ MCP Server ] ← THE PRODUCT
 Traversal-oriented tools — no search, no Rule nodes
        ↓
 [ Client AI ] ← not our product, does discovery + interpretation
 Agent finds entry point (grep / file search / AST)
 Agent calls CodeLens for structural context (subgraph)
 Agent's LLM interprets the subgraph and answers the user
```

---

## The Three Layers Explained

### Layer 1 — Ingestion and Indexing

Tree-sitter parses the codebase into an AST. The indexer extracts:

**Nodes:** `File`, `Class`, `Function`, `ConditionalBranch`, `ReturnStatement` 
**Edges:** `calls`, `imports`, `defines`, `contains`, `returns`

Each node is stored in Neo4j with:
- File path and line number
- A `stale` flag (for incremental re-indexing)

No vector embeddings are generated at index time. See ADR-002.

CLI: `codelens index --repo ./path`

---

### Layer 2 — Domain Clustering (The Intelligence Layer)

This is what separates CodeLens from a plain code indexer.

After indexing, community detection (Leiden algorithm) runs on the code graph to identify natural clusters of related code — functions, classes, and branches that form a coherent unit. These clusters become `Domain` nodes (e.g., "Checkout", "Payments", "Auth").

Each `Domain` node stores:
- `name` — human-readable domain label (LLM-assigned from cluster content)
- `summary` — a single plain-English description of what the domain does (one LLM call per cluster)
- `member_nodes[]` — edges to all code nodes in the cluster

This replaces the per-`ConditionalBranch` Rule extraction from the previous spec (see ADR-001). LLM runs only once per domain cluster (typically 10–20 clusters per repository) rather than once per conditional node (potentially hundreds).

**Rule interpretation is not pre-computed.** When an agent queries a domain or a function, it receives the structural subgraph. The client AI derives business rules from the subgraph in the context of the specific question being asked. Persona rendering (developer/product/legal framing) is handled by the client AI via system prompt, not by CodeLens.

---

### Layer 3 — MCP Server (The Product Surface)

The MCP server exposes the graph as traversal tools. There is no search functionality — the agent supplies the entry point symbol name; CodeLens supplies the structural context.

**Core Tools:**

```python
get_code_context(symbol_name: str) -> SubGraph
# Returns the subgraph around a function or class:
# the node itself, its direct callees, its direct callers,
# any ConditionalBranch nodes inside it, and their immediate callees.
# Depth: 2-3 hops. This is the primary tool agents use.

get_callers(symbol_name: str) -> list[CodeNode]
# Returns all nodes that directly call this symbol.
# Used to understand impact: what breaks if I change this?

get_callees(symbol_name: str) -> list[CodeNode]
# Returns all nodes this symbol directly calls.
# Used to understand dependencies.

get_domain(symbol_name: str) -> Domain
# Returns the domain cluster this symbol belongs to,
# including the domain summary and all other member symbols.

get_domains() -> list[Domain]
# Returns all discovered domain clusters with member counts and summaries.
# Primary entry point for non-technical users browsing by business area.

get_domain_content(domain_name: str) -> SubGraph
# Returns the full subgraph of all nodes in a domain cluster.
# Used by non-technical users querying an entire business area.
```

**There is no `persona` parameter on MCP tools.** Persona rendering is handled by the client AI's system prompt. The agent decides how to frame the response based on who it is talking to.

**There is no `search_rules` or `search_code` tool.** The agent uses its own file search, grep, or AST tools to find entry points, then calls `get_code_context` to get the structural picture.

---

## Incremental Re-Indexing

When code changes, the system re-indexes only what changed:

| Step | Action |
|---|---|
| Webhook / CLI trigger | Push event or `codelens index --update` |
| File diff | Identify changed files |
| Stale marking | Mark affected code nodes as stale |
| Selective re-parse | Tree-sitter re-parses only changed files |
| Graph update | Add, modify, or remove affected nodes and edges |
| Domain re-cluster | Re-run community detection if structural changes are significant |
| Domain summary refresh | Re-run LLM summary only on clusters whose membership changed |

No Rule node re-extraction step exists — Rule nodes do not exist in this architecture (ADR-001).

CLI: `codelens index --update --repo ./path`

---

## PR Change Simulator

When a PR is opened/updated:

1. Check out base and head branches
2. Run incremental indexing on head branch
3. Diff the structural graph: base vs head
4. Identify changed nodes: new functions, removed functions, modified `ConditionalBranch` nodes
5. For changed `ConditionalBranch` nodes, retrieve the surrounding subgraph from both base and head
6. Send both subgraphs to an LLM with a diff prompt: "describe what business logic changed between these two versions"
7. Post the LLM-generated plain-English summary as a structured PR comment

Example PR comment:
> **Business logic changed in this PR:**
> - **MODIFIED:** `apply_discount()` — discount cap condition changed (`pricing.py:L142`)
> - **REMOVED:** `check_grace_period()` — new user grace period logic no longer present
> - **ADDED:** `check_bulk_order()` — new branch handling orders over 100 units

This replaces the previous Rule node diff approach. The diff now operates on structural graph changes, not on pre-extracted Rule node text.

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

The persona dropdown in Streamlit sets the system prompt for the demo agent: "You are answering in Product Manager mode. Explain in plain English, avoid code references." The agent then calls the appropriate MCP traversal tools, receives the subgraph, and formats its answer accordingly. This is handled entirely by the client-side agent — not by MCP tool parameters.

---

## Authentication and Authorization

### Key Design Decision: Roles and Personas Are Separate Concerns

**Personas** (`developer`, `product`, `legal`) are purely a **UX / presentation preference** handled by the client AI's system prompt. They are not parameters on MCP tools and are not stored in the database. Any authenticated user can request any persona framing.

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
| **Read** | Browse indexed repos, domain clusters with summaries, indexing job history |
| **Update** | Trigger full or incremental re-index, manually edit a domain summary, re-run community detection |
| **Delete** | Remove a repository from the index |

### User Management (Admin)
- List all users and their roles
- Promote a user to admin
- Revoke access / delete user

### Domain Summary Correction Flow
If the LLM generates an inaccurate domain summary, an admin can:
1. Open the domain in the admin panel
2. Edit the summary text directly
3. Save with a `human_verified: true` flag

Individual function-level rule correction is not applicable — function-level rules are not pre-stored; they are interpreted at query time by the client AI.

---

## Definitive Tech Stack

### Core (The Product)
| Component | Technology |
|---|---|
| AST Parsing | Tree-sitter (Python, TypeScript — MVP languages) |
| Graph Database | Neo4j AuraDB Free |
| Community Detection | graspologic (Leiden algorithm) — Python library, no external service |
| Domain Summarisation | Python + Gemini 2.0 Flash (free tier) — runs once per cluster at index time |
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
- Pre-extracted Rule nodes with index-time LLM extraction (see ADR-001)
- Vector embeddings and vector index (see ADR-002)
- Semantic or keyword search inside CodeLens (see ADR-002)
- Persona parameter on MCP tools (persona is a client AI system prompt concern)
- LangGraph for query orchestration (dropped, no runtime agent needed)
- Separate vector database
- Full Next.js production dashboard (Streamlit demo is sufficient for MVP)
- Redis / Celery for MVP (use FastAPI BackgroundTasks first)
- Role-based persona enforcement (personas are free UX parameters, not security gates)

---

## Development Phases (Revised)

### Phase 1 — Core Graph (Weeks 1–2)
- Tree-sitter parsing pipeline for Python and TypeScript
- Neo4j schema: File, Module, Class, Function, ConditionalBranch nodes with all edges
- Entity and edge extraction working end-to-end
- CLI indexer running on a real repository
- Leiden community detection producing Domain clusters

**Gate:** A real codebase indexed into Neo4j with queryable graph structure and domain clusters visible.

### Phase 2 — Domain Summaries and MCP Server (Weeks 3–4)
- Domain summary generation: one LLM call per cluster producing plain-English Domain node summaries
- All core MCP traversal tools implemented (`get_code_context`, `get_callers`, `get_callees`, `get_domain`, `get_domains`, `get_domain_content`)
- Tested end-to-end with Claude Desktop and Claude Code
- Incremental re-indexing pipeline working
- CLI simulate command

**Gate:** Claude Code can call `get_code_context("apply_discount")` and receive a subgraph it can interpret accurately.

### Phase 3 — Auth, Admin Panel + Demo (Weeks 5–6)
- FastAPI auth endpoints (register, login, logout, JWT issuance)
- MCP server JWT validation middleware
- Admin panel: repo CRUD, domain summary editing, user management
- Streamlit demo UI with login + persona system prompt toggle
- GitHub webhook integration
- PR diff logic and automated comment posting

**Gate:** Full authenticated demo ready. Admin can manage repos and domain summaries. Users can query via MCP and Streamlit demo UI.

### Phase 4 — Testing, Documentation and Presentation (Weeks 7–8)
- pytest suite targeting 70%+ coverage on indexer and MCP tools
- Integration tests: index sample repo, assert domain clusters and subgraph queries
- `docs/setup.md`, `docs/user-guide.md`, `docs/api.md`
- `docs/data-model.md` with Mermaid Neo4j schema diagram
- Final report derived from living spec
- Demo script and presentation

**Gate:** All course requirements met. Demo rehearsed. Submitted.

---

## Success Metrics

| Metric | Target |
|---|---|
| Indexing speed | < 5 min for 100k LOC |
| Domain clustering accuracy | Clusters are coherent and labelled correctly on manual review |
| MCP subgraph query latency | < 2 sec for `get_code_context` |
| PR simulation latency | < 45 sec from push to posted comment |
| Test coverage | > 70% on indexer and MCP server |
| Demo cost | $0–5/month (free-tier infrastructure) |

---

## Open Questions

1. **Domain clustering quality:** Leiden community detection is unsupervised — cluster boundaries may not align with business domain boundaries. How do we validate and correct poor clusters without manual intervention?
2. **Subgraph depth:** The `get_code_context` tool returns a 2-3 hop subgraph. What is the right depth before the returned context becomes too large to be useful?
3. **Language priority:** Python + TypeScript for MVP confirmed. Java or Go next?
4. **Webhook vs polling:** GitHub webhook requires a public server. For local dev, do we support `codelens index --watch` polling as fallback?
5. **Multi-repo:** Does a single CodeLens instance index one repo or many? MVP scope should be single-repo.
6. **Auth upgrade path:** MVP uses username/password + JWT. Is GitHub OAuth the right upgrade for v2 given the developer-first audience?
7. **Admin UI technology:** Streamlit admin page vs minimal FastAPI + HTML — which is faster to build and maintain?
8. **PR simulator entry point:** Without pre-extracted Rule nodes, the PR diff now compares structural subgraphs. How do we scope which changed nodes to include in the diff prompt to keep it within LLM context limits?

---

## Architectural Decision Records

Key design decisions are documented in `docs/decisions/`:

| ADR | Decision |
|---|---|
| [ADR-001](decisions/ADR-001-rule-interpretation-strategy.md) | Rule interpretation is query-time (client AI reads subgraph) — no index-time LLM rule extraction |
| [ADR-002](decisions/ADR-002-code-discovery-strategy.md) | Code discovery is agent-led — no semantic or keyword search inside CodeLens for MVP |
| [ADR-003](decisions/ADR-003-presentation-tier-strategy.md) | Presentation tier strategy — Streamlit vs separate HTML/JS frontend (PROPOSED, not yet decided) |
