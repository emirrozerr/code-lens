# CodeLens — Requirements Alignment Matrix

> **Purpose:** Maps every requirement from both courses to the CodeLens living specification and project plan. Used to identify gaps, verify coverage, and plan closing actions. 
> **Last updated:** April 2026

**Source Key:**
- **MT** — Multi-Tier Project Requirements (`docs/multi-tier-project-requirements.md`)
- **TA** — Team Application Project Requirements (`docs/Team-application-project-requirements.md`)
- **LS** — Living Specification (`docs/LIVING_SPEC.md`)

**Status Key:**
- **FULL** — Fully covered, explicitly defined in the living spec
- **PARTIAL** — Partially addressed, needs small additions
- **MISSING** — Not yet in the spec, action required
- **BONUS** — Optional/extra credit requirement

---

## 1. Architecture Requirements

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| A1 | Minimum three-tier architecture (Presentation, Application, Data) | MT | FULL | LS: Core Architecture | Three clear tiers: **Ingestion + Rule Extractor** (data processing), **FastAPI + MCP Server** (application/logic), **Streamlit Demo + Admin UI** (presentation) |
| A2 | API communication between tiers (REST or GraphQL) | MT | FULL | LS: Layer 3 — MCP Server | FastAPI exposes REST endpoints for auth, admin CRUD, and webhooks. MCP protocol handles agent-to-server communication |
| A3 | Middleware for handling requests | MT | FULL | LS: Auth & Authorization | FastAPI middleware validates JWT tokens on every incoming request before routing. Auth middleware is a standard middleware pattern |
| A4 | Application must be deployable and demonstrable online | MT | FULL | LS: Infrastructure | Backend on Railway/Render (free tier), Neo4j on AuraDB Free (cloud), Streamlit deployable on Streamlit Cloud |
| A5 | Project serves as a portfolio piece | MT | FULL | — | CodeLens is a real, novel product with a GitHub repository and live demo |
| A6 | System architecture diagram | MT TA | FULL | LS: Core Architecture | ASCII architecture diagram in `LIVING_SPEC.md`. Needs a proper visual diagram in `docs/` |
| A7 | Select and document technology stack | TA | FULL | LS: Definitive Tech Stack | Full tech stack table documented in `LIVING_SPEC.md` covering all layers |
| A8 | Use version control with documented team contributions | TA | FULL | — | GitHub repository at `emirrozerr/code-lens`, commit history active |

---

## 2. Authentication & Authorization

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| B1 | User registration | MT | FULL | LS: Auth Endpoints | `POST /auth/register` — admin creates user accounts. Users receive credentials to access the system |
| B2 | User login | MT | FULL | LS: Auth Endpoints | `POST /auth/login` — returns signed JWT containing `{ user_id, role, email }` |
| B3 | User logout | MT | FULL | LS: Auth Endpoints | `POST /auth/logout` — invalidates the user session/token |
| B4 | Password reset | MT | MISSING | — | Not yet in spec. Needs `POST /auth/reset-password` with email token flow. Action: add to Phase 4 |
| B5 | Role-based access control using JWT or OAuth | MT | FULL | LS: Security Roles | Two roles: `user` and `admin`. JWT carries role claim. Admin routes return 403 to non-admin tokens. MCP server validates JWT on every tool call |
| B6 | Secure auth method (JWT or OAuth) | MT | FULL | LS: Auth Mechanism | Signed JWT issued by FastAPI. GitHub OAuth planned as upgrade path for v2 |
| B7 | User authentication implemented in Week 9 | TA | FULL | LS: Phase 4 | Auth, admin panel, and JWT middleware all scoped to Phase 4 (Weeks 7–8 in our plan, TA Week 9) |
| B8 | User roles and permissions | TA | FULL | LS: Security Roles, Admin Panel | `user` vs `admin` roles. Admin has exclusive access to repo management, rule editing, and user management |

---

## 3. Business Logic

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| C1 | Domain-specific business features | MT | FULL | LS: Layer 2 — Rule Extraction | The core domain is code intelligence. Business logic includes: rule extraction pipeline, graph traversal, PR diff classification, incremental re-indexing strategy |
| C2 | CRUD operations | MT | FULL | LS: Admin Panel | Admin panel provides full CRUD on repositories (register/browse/re-index/delete) and Rule nodes (read/edit/delete). User management also CRUD |
| C3 | Input validation | MT | PARTIAL | LS: Tech Stack (FastAPI + Pydantic) | FastAPI with Pydantic enforces schema validation on all request bodies. Needs to be explicitly documented and consistently applied across all endpoints |
| C4 | Error handling | MT | PARTIAL | LS: Incremental Re-indexing | Re-indexing has retry/stale logic mentioned. General API error handling with proper HTTP status codes needs to be explicitly specified |

---

## 4. Data Management

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| D1 | Persistent database with related entities | MT | FULL | LS: Neo4j Graph DB | Neo4j stores all data persistently: `File`, `Class`, `Function`, `ConditionalBranch`, `Rule` nodes with typed edges between them |
| D2 | Related entities / relationships | MT | FULL | LS: Layer 1 — Ingestion | Edges: `calls`, `imports`, `defines`, `contains`, `returns`. Rule nodes linked to source code nodes. Domain clusters group related rules |
| D3 | Data seeding | MT | MISSING | — | No seeding script defined. Action: create a seed script that pre-indexes a sample open-source repo so the demo is never empty on first launch |
| D4 | Database migrations | MT | PARTIAL | — | Neo4j is schemaless so traditional migrations don't apply, but schema evolution (adding new node properties) needs a versioned migration strategy. Action: document schema versioning approach |
| D5 | Querying, filtering, sorting | MT | PARTIAL | LS: MCP Tools | MCP tools use Cypher queries for search. `limit`, `offset`, `sort_by`, `domain` filter parameters not yet explicit in tool signatures. Action: add to tool definitions |
| D6 | Pagination | MT | MISSING | — | Pagination not yet defined for any MCP tool or REST endpoint. Action: add `limit` + `offset` (or cursor-based) pagination to `search_rules()`, `get_domain_rules()` |
| D7 | Data model diagram | TA | MISSING | — | No visual Neo4j node/edge schema diagram exists yet. Action: create `docs/data-model.md` with a Mermaid diagram of all node types, properties, and edge types |

---

## 5. User Interface

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| E1 | Responsive user interface with intuitive navigation | MT | PARTIAL | LS: Demo Layer | Streamlit demo UI is functional but not primarily designed for responsiveness. Admin panel is also Streamlit. Acceptable for demo/MVP scope |
| E2 | Real-time elements (e.g., WebSockets) | MT | MISSING | — | Not yet in spec. Action: stream indexing job progress via WebSocket or Server-Sent Events to the demo/admin UI. Small addition with good visual impact |
| E3 | Functional user interface connected to backend | TA | FULL | LS: Demo Layer | Streamlit UI connects to FastAPI backend, which calls MCP tools, which query Neo4j. Full connection established |
| E4 | Admin panel for system management | — | FULL | LS: Admin Panel | Separate admin-only Streamlit page covering repo CRUD, rule editing, user management |

---

## 6. Integration

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| F1 | At least one third-party API integration | MT | FULL | LS: Rule Extractor, PR Simulator | **Two integrations:** (1) LLM API (Gemini Flash / OpenAI) for rule extraction and PR summaries. (2) GitHub API for webhooks and PR commenting |
| F2 | Error handling for third-party integrations | MT | PARTIAL | LS: Incremental Re-indexing | Webhook retry logic mentioned. LLM API error handling (rate limits, timeouts, failed extractions) not yet explicitly specified. Action: add to spec |
| F3 | System integrations (Low-Code track evaluation) | TA | FULL | LS: Tech Stack | LLM API + GitHub API + Neo4j Cloud + MCP protocol — multiple meaningful integrations |
| F4 | AI tool usage (Low-Code track evaluation) | TA | FULL | — | AI is not just a development tool here — it is the product's core intelligence. LLM rule extraction is the primary feature |

---

## 7. Security and Performance

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| G1 | Data encryption | MT | PARTIAL | LS: Auth Mechanism | JWT tokens are signed. HTTPS enforced by hosting providers. Database-level encryption depends on Neo4j AuraDB (cloud-managed). Needs explicit documentation |
| G2 | Logging | MT | MISSING | — | Not yet in spec. Action: add Python `logging` module to all pipeline stages (indexing, rule extraction, auth failures, webhook events) |
| G3 | Monitoring | MT | MISSING | — | Not yet in spec. Action: basic health check endpoint (`GET /health`) + Railway/Render built-in metrics for MVP |
| G4 | Performance optimizations / caching | MT | FULL | LS: Layer 2 | Pre-rendered persona fields eliminate LLM calls at query time. Neo4j vector index ensures fast semantic search. `human_verified` flag prioritizes trusted results |

---

## 8. Testing

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| H1 | Unit tests with >70% code coverage | MT | MISSING | — | No testing plan in the spec. Action: add `pytest` suite covering indexer, rule extractor, auth, and MCP tool logic. Target 70%+ coverage with `coverage.py` |
| H2 | Integration tests | MT | MISSING | — | Action: integration tests for the full pipeline — index a sample repo end-to-end and assert rule nodes are created correctly in Neo4j |
| H3 | End-to-end tests | MT | MISSING | — | Action: E2E test — authenticate → call MCP tool → assert response matches expected rule node content |
| H4 | Testing phase (Week 10) | TA | MISSING | — | Not mapped to a phase in the living spec. Action: add explicit testing tasks to Phase 3 and Phase 4 |
| H5 | Code review as part of sprint cycle | TA | PARTIAL | — | Implied by GitHub workflow but not formally defined. Action: define branch protection rules requiring PR review before merge to main |

---

## 9. Documentation

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| I1 | `README.md` with setup instructions | MT | PARTIAL | `README.md` | README exists with architecture and stack overview. Missing: step-by-step local setup instructions, environment variable list, Docker Compose instructions |
| I2 | Architecture diagram (visual) | MT TA | PARTIAL | LS: Core Architecture | ASCII diagram in `LIVING_SPEC.md`. Needs a proper Mermaid or image diagram added to `docs/` |
| I3 | API documentation | MT | MISSING | — | FastAPI produces auto-generated Swagger docs at `/docs`. Action: ensure all endpoints have docstrings and OpenAPI descriptions. Export as `docs/api.md` |
| I4 | User guide | MT | MISSING | — | Action: add `docs/user-guide.md` covering: how to index a repo, how to configure MCP in Claude, how to use the demo UI, how to use the admin panel |
| I5 | Final report (5–10 pages) | MT | PARTIAL | LS: `LIVING_SPEC.md` | Living spec is a strong foundation but not formatted as a formal academic report. Action: derive `docs/final-report.md` from it with abstract, problem statement, solution, architecture, results |
| I6 | Technical documentation | TA | PARTIAL | LS: `LIVING_SPEC.md` | Living spec covers architecture and tech decisions well. Needs data model diagram and API docs to be complete |
| I7 | Installation and usage instructions | TA | MISSING | — | Not yet written. Action: `docs/setup.md` with step-by-step local dev setup — Python env, Neo4j connection, environment variables, running indexer and MCP server |
| I8 | One-page proposal submitted by Week 2 | MT | FULL | `CodeLens_Project_Specification.md` | The original specification document serves as the project proposal |

---

## 10. Project Management & Process

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| J1 | Project repository with commit history | TA | FULL | — | `emirrozerr/code-lens` on GitHub with active commit history |
| J2 | Project management plan (GitHub Projects / Jira / Trello) | TA | MISSING | — | Action: create GitHub Projects board with issues mapped to Phase 1–4 milestones |
| J3 | Team activity visible in commit history | TA | PARTIAL | — | Commits exist. Action: ensure all team members commit under their own accounts — no single-author history |
| J4 | Agile / Scrum methodology | TA | PARTIAL | — | Mentioned as recommended in TA requirements. Action: define sprint cadence (2-week sprints), sprint planning sessions, and sprint demo format |
| J5 | Role assignment within team | TA | MISSING | — | Action: document team roles in `README.md` or a `CONTRIBUTING.md` file (PM, Backend Dev, Frontend Dev, QA/Docs) |
| J6 | MVP-first development approach | MT TA | FULL | LS: Development Phases | Explicit 4-phase MVP approach with gates defined in `LIVING_SPEC.md` |
| J7 | Milestone: Design Document by Week 4 | MT | FULL | LS, README | `LIVING_SPEC.md` and `README.md` constitute the design document. Can be submitted immediately |
| J8 | Milestone: Prototype by Week 8 | MT | PARTIAL | LS: Phase 1–2 | Phase 1 (Core Graph) and Phase 2 (Rule Extraction) together form the prototype. On track if started now |
| J9 | Milestone: Beta by Week 12 | MT | PARTIAL | LS: Phase 3–4 | Phase 3 (MCP Server) and Phase 4 (Auth + Demo) complete the beta. Tight but achievable |
| J10 | Final Presentation (10–15 min demo) | MT TA | MISSING | — | Action: plan demo script as part of Phase 4. Sequence: index a real repo live, query via Claude Code MCP, demo admin panel, demo Streamlit UI |
| J11 | Ethical collaboration practices | MT TA | FULL | — | All tools used are open-source or properly licensed. No plagiarism. |

---

## 11. Bonus / Advanced Requirements (Optional)

| # | Requirement | Source | Status | CodeLens Coverage | Reasoning / How It Is Covered |
|---|---|---|---|---|---|
| K1 | Advanced data handling with ORM or full-text search | MT | FULL | LS: Neo4j + Vector Index | Neo4j provides both full-text search and vector (semantic) search natively. No separate ORM needed — Cypher is the query language |
| K2 | Real-time collaboration (e.g., live chat) | MT | MISSING | — | Not applicable to CodeLens. Could stretch to: multiple users querying the same indexed repo concurrently — but this is not collaboration in the traditional sense |
| K3 | Analytics with charts and report exports | MT | PARTIAL | LS: Admin Panel | Admin panel could show: rule extraction confidence score distribution, rules per domain chart, indexing job history. PDF export of rule sets is already in scope |
| K4 | Mobile integration or PWA compatibility | MT | MISSING | — | Not in scope. Streamlit is not PWA-ready. Low priority given the developer/enterprise audience |
| K5 | Internationalization (i18n) | MT | MISSING | — | Not applicable to MVP |
| K6 | Emerging tech (AI, blockchain, etc.) | MT | FULL | LS: Layer 2 | LLM-powered rule extraction and GraphRAG are genuinely emerging technologies and are the core product feature |
| K7 | Automation workflows | TA | FULL | LS: PR Change Simulator | Automated PR diffing, rule re-extraction, and GitHub comment posting are fully automated workflows with no manual steps |
| K8 | AI integration | TA | FULL | LS: Rule Extractor | LLM API is not a bolt-on feature — it is the intelligence layer that produces the core product value |

---

## Summary Dashboard

| Status | Count | Requirements |
|---|---|---|
| **FULL** | 27 | A1–A8, B1–B3, B5–B8, C1–C2, D1–D2, F1, F3–F4, G4, I8, J1, J6–J7, J11, K1, K6–K8 |
| **PARTIAL** | 14 | A6, C3–C4, D4–D5, E1, F2, G1, H5, I1–I2, I5–I6, J3–J4, J8–J9, K3 |
| **MISSING** | 16 | B4, D3, D6–D7, E2, G2–G3, H1–H4, I3–I4, I7, J2, J5, J10 |
| **BONUS (covered)** | 3 | K1, K6, K7–K8 |
| **BONUS (not covered)** | 3 | K2, K4–K5 |

---

## Priority Action Plan

### Must Do (Core Requirements)

| Action | Req. IDs | Effort |
|---|---|---|
| Add `POST /auth/reset-password` endpoint | B4 | Low |
| Add logging via Python `logging` module | G2 | Low |
| Add `GET /health` monitoring endpoint | G3 | Very Low |
| Add `limit`, `offset`, `sort_by` to MCP tool signatures | D5, D6 | Low |
| Create seed script pre-indexing a sample repo | D3 | Medium |
| Write `pytest` suite targeting 70%+ coverage | H1–H4 | High |
| Set up GitHub Projects board with Phase 1–4 issues | J2 | Low |
| Plan and write demo script for final presentation | J10 | Medium |

### Should Do (Quality & Completeness)

| Action | Req. IDs | Effort |
|---|---|---|
| Add WebSocket/SSE progress stream for indexing jobs | E2 | Medium |
| Write `docs/user-guide.md` | I4 | Medium |
| Write `docs/setup.md` with local dev instructions | I7 | Low |
| Add complete setup instructions to `README.md` | I1 | Low |
| Create `docs/data-model.md` with Mermaid schema diagram | D7, I2 | Low |
| Export FastAPI Swagger as `docs/api.md` | I3 | Low |
| Write `docs/final-report.md` from living spec | I5 | Medium |
| Define schema versioning approach for Neo4j | D4 | Low |
| Document team role assignments | J5 | Very Low |
| Define sprint cadence and branch protection rules | J4, H5 | Low |
