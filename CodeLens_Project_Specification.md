# CodeLens: GraphRAG-Powered Code Intelligence Platform

**Project Specification Document**  
Version 1.0 — MVP Scope  
March 2026

---

## Executive Summary

CodeLens is a code intelligence platform that indexes codebases into structured knowledge graphs and uses GraphRAG to enable multi-audience business logic exploration, change impact simulation, and persona-based documentation. Unlike traditional code assistants that rely on flat text retrieval, CodeLens provides structural guarantees, cross-file reasoning, and persistent business knowledge extraction.

- **Target Users:** Software engineers, product managers, compliance officers, technical leads
- **Primary Value Proposition:** Transform implicit business logic scattered across code into an explicit, queryable, multi-audience knowledge system that stays synchronized with every code change.

---

## Problem Statement

Modern codebases contain critical business logic buried in conditional branches, validation chains, and service methods across hundreds of files. Current tools fail in three ways:

1. **Flat RAG systems** (Claude Code, GitHub Copilot) retrieve by text similarity, missing structural relationships and multi-hop reasoning.
2. **Documentation goes stale** immediately and contradicts actual code behavior.
3. **Non-technical stakeholders** (PMs, compliance) cannot independently understand what the code actually does.

**The Gap:** No existing tool provides graph-structured, persona-aware, auto-updating business logic intelligence that serves both engineers and business stakeholders.

---

## Solution Overview

CodeLens builds a persistent knowledge graph from source code using AST parsing, extracts business rules via GraphRAG agents, and renders them through persona-specific lenses (Developer, Product Manager, Legal). A change detection pipeline keeps the graph synchronized with every git push, enabling real-time PR impact analysis.

### Core Capabilities

1. **Business Logic Mapper** — Extracts and catalogs every business rule from code with full graph traceability.
2. **Persona-Based Explainer** — Re-renders any rule in Developer (technical), Product (functional), or Legal (compliance) language.
3. **Rule Change Simulator** — Automatically detects business logic changes in pull requests and posts impact summaries.

---

## Use Cases

### UC-1: Engineer Understands Unfamiliar Business Logic

An engineer searches "how does checkout work" and receives:
- Structured map of all governing business rules
- Sequence diagram showing call flow
- Code references with file/line precision
- Related rules and edge cases

**Outcome:** Domain understanding in 20 minutes instead of 2 weeks of code archaeology.

### UC-2: Product Manager Queries Current Behavior Before Writing Spec

A PM queries "discount eligibility rules" in Product persona mode and sees:
- Plain-English rule statements (no code references)
- Example scenarios showing edge cases
- When each rule was introduced and why

**Outcome:** Specs written from actual system behavior, preventing shadow rules and implementation drift.

### UC-3: Engineer's PR Flagged for Business Logic Changes

When a PR touches the pricing module:
- Rule Change Simulator diffs the base vs. head branch subgraphs
- Detects modified, added, or removed rules
- Posts structured PR comment: *"⚠️ Business logic changed: discount cap raised 15% → 20%, grace period rule removed"*

**Outcome:** No business logic changes ship silently; PM reviews before merge.

### UC-4: Compliance Officer Audits Payment Rules

Compliance officer navigates to Payments domain in Legal persona:
- All rules displayed as policy clauses
- Full file-level traceability for each rule
- PDF export for audit package

**Outcome:** Regulatory audit completed in hours instead of weeks.

### UC-5: New Developer Onboards to a Domain

New hire queries "user authentication rules" in Developer mode:
- Component diagram of involved modules
- Sequence diagram of login flow
- Complete rule set with technical context

**Outcome:** Domain fluency achieved in one sitting, zero meetings.

---

## Requirements Overview

### Functional Requirements Summary

| ID  | Requirement              | Key Features |
|-----|--------------------------|--------------|
| FR1 | Ingestion & Indexing     | Tree-sitter AST parsing (Python/TypeScript), Neo4j storage, vector embeddings, incremental re-indexing via webhooks |
| FR2 | Rule Extraction          | LangGraph agent traversal, LLM-synthesized rule statements, domain entity clustering, source traceability |
| FR3 | Business Logic Mapper    | Searchable rule registry, domain browsing, auto-generated sequence/component diagrams (Mermaid) |
| FR4 | Persona Explainer        | Three modes (Developer/Product/Legal), switchable per query, graph-grounded rendering |
| FR5 | Rule Change Simulator    | GitHub/GitLab webhooks, branch diff, change classification, automated PR comments, CLI dry-run |
| FR6 | Export & Integration     | PDF export, REST API, CLI tools (index, search, simulate, export) |

### Non-Functional Requirements Summary

| Category    | Requirement                   | Target Metric |
|-------------|-------------------------------|---------------|
| Performance | Indexing speed                | < 5 min for 100k LOC |
| Performance | Query latency                 | < 2 sec for rule search with persona rendering |
| Performance | PR simulation latency         | < 45 sec from push to comment |
| Accuracy    | Rule extraction precision     | > 90% on human-validated samples |
| Scalability | Incremental re-indexing       | Typical PR (5–10 files) processes in 30–45 sec |
| Scalability | Graph capacity (free tier)    | Up to 200k nodes, 400k relationships (Neo4j AuraDB Free) |
| Reliability | Webhook failures              | Retry logic, manual re-index fallback, staleness warning UI |
| Reliability | Cache invalidation            | Deterministic invalidation on rule node staleness |
| Cost        | Demo/MVP cost                 | $0–5/month using free-tier infrastructure |
| Usability   | Persona switching             | Persists per session, switchable per query |
| Usability   | Export formats                | PDF for compliance/audit packages |

---

## Functional Requirements (Detailed)

### FR-1: Ingestion and Indexing

- CLI command: `codelens index --repo ./path`
- Tree-sitter AST parsing for Python and TypeScript (MVP languages)
- Extract nodes: `File`, `Module`, `Class`, `Function`, `ConditionalBranch`, `ReturnStatement`
- Extract edges: `calls`, `imports`, `defines`, `contains`, `returns`
- Store in Neo4j with file path and line number metadata
- Generate vector embeddings per node, store in Neo4j vector index
- Incremental re-index via GitHub/GitLab webhook on push

### FR-2: Rule Extraction

- LangGraph agent traverses `ConditionalBranch` nodes
- Iteratively fetches callee subgraphs until sufficient context gathered
- LLM synthesizes human-readable rule statements
- Store `Rule` nodes in Neo4j with edges to source code nodes
- Group rules by domain entity via semantic clustering
- Every rule statement cites at least one source node

### FR-3: Business Logic Mapper

- Searchable rule registry (full-text and semantic search)
- Rules browsable by domain entity group
- Each rule shows: statement, source file/line, related rules, affected functions
- Auto-generated sequence diagrams per domain flow (Mermaid)
- Component diagrams per module showing import relationships

### FR-4: Persona Explainer

- Three rendering modes: **Developer**, **Product**, **Legal**
  - **Developer:** rule + code references + call chain + types
  - **Product:** plain English + example scenarios + no code
  - **Legal:** policy-clause format + traceability + export-ready
- Mode switchable per query, persists per session
- All modes grounded to same graph nodes (no hallucination)

### FR-5: Rule Change Simulator

- GitHub/GitLab webhook endpoint (fires on PR open/update)
- Checkout base and head branches, diff rule subgraphs
- Classify changes: `RULE_MODIFIED`, `RULE_REMOVED`, `RULE_ADDED`
- Generate business-language impact summary via LLM
- Post structured comment to PR automatically
- Configurable per repo (which paths/domains to monitor)
- CLI dry-run mode: `codelens simulate --base main --head feature/pricing`

### FR-6: Export and Integration

- PDF export of any rule set or domain view
- REST API: rule search, domain listing, rule detail
- CLI: `codelens index`, `codelens search`, `codelens simulate`, `codelens export`

---

## System Architecture

### High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├──────────────────────────────────────┬───────────────────────────┤
│          Web UI (Next.js)            │        CLI (Python)        │
│  • Rule Explorer                     │  • codelens index          │
│  • Persona Switcher                  │  • codelens search         │
│  • React Flow Graph Viz              │  • codelens simulate       │
│  • PR Impact Feed                    │  • codelens export         │
└──────────────────────────────────────┴───────────────────────────┘
                          ▲
                   REST API / GraphQL
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                          FEATURE LAYER                           │
├──────────────────┬──────────────────────┬────────────────────────┤
│  Business Logic  │   Persona Explainer  │  Rule Change Simulator │
│  Mapper          │                      │                        │
│  • Rule Search   │  • Dev Mode          │  • Branch Diff         │
│  • Domain Browse │  • Product Mode      │  • Change Classification│
│  • Diagram Gen   │  • Legal Mode        │  • PR Comment Bot      │
└──────────────────┴──────────────────────┴────────────────────────┘
                          ▲
              Cypher Queries / Vector Search
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                       INTELLIGENCE LAYER                         │
├──────────────────────────────────────┬───────────────────────────┤
│         GraphRAG Indexer             │      LangGraph Agent       │
│  • Community Detection (Leiden)      │  • Rule Extraction         │
│  • Domain Clustering                 │  • Multi-hop Traversal     │
│  • Semantic Embeddings               │  • LLM Synthesis           │
└──────────────────────────────────────┴───────────────────────────┘
                          ▲
              Read/Write Graph Operations
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                            │
├──────────────────────────────────────┬───────────────────────────┤
│          Neo4j Graph DB              │  Redis Cache + PostgreSQL  │
│  • Code Graph (nodes/edges)          │  • Query Response Cache    │
│  • Rule Nodes                        │  • User Sessions           │
│  • Vector Index                      │  • Job Metadata            │
└──────────────────────────────────────┴───────────────────────────┘
                          ▲
                    Parsed AST Data
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                           │
├──────────────────────────────────────┬───────────────────────────┤
│       Tree-sitter AST Parser         │  GitHub/GitLab Webhook     │
│  • Python/TypeScript Support         │  • Push Events             │
│  • Entity/Edge Extraction            │  • PR Events               │
│  • Incremental Re-parse              │  • Stale Node Marking      │
└──────────────────────────────────────┴───────────────────────────┘
                          ▲
                    Git Repository
                          ▼
                  [ Source Code Repo ]
```

### Data Flow

1. **Ingestion:** Git repository → Tree-sitter AST parser → Entity and edge extractor → Git log annotator
2. **Storage:** Neo4j graph database stores all nodes, relationships, and vector embeddings
3. **Intelligence:** GraphRAG indexer applies community detection; LangGraph agent extracts Rule nodes
4. **Features:** Business Logic Mapper, Persona Explainer, Rule Change Simulator query the graph
5. **Presentation:** Web UI (Next.js + React Flow) and CLI expose functionality to end users

### Change Detection and Incremental Re-indexing

| Step | Action |
|------|--------|
| Webhook received | GitHub push event fires FastAPI endpoint |
| File diff extraction | Parse payload for changed file paths |
| Stale marking | Neo4j query marks affected nodes and dependent Rule nodes stale |
| Selective re-parse | Tree-sitter re-parses only changed files |
| Graph update | Update Neo4j nodes (add, modify, delete) |
| Rule re-extraction | LangGraph agent re-extracts stale Rule nodes only |
| Cache invalidation | Redis invalidates entries containing affected rule IDs |
| PR simulation | If PR event, Rule Change Simulator posts comment |

**Performance:** Typical PR (5–10 files changed) processes in 30–45 seconds end-to-end.

---

## Technical Stack

### Parsing and Ingestion
- **Tree-sitter** — Multi-language AST parsing (Python, TypeScript, Java, Go, Rust support)
- **GitPython** — Git diff computation and commit history traversal
- **Celery + Redis** — Async background job queue for indexing tasks

### Graph and Intelligence Layer
- **Neo4j** — Primary graph database with native vector index (no separate vector DB needed)
- **Microsoft GraphRAG** — Open-source implementation, Leiden algorithm for community detection
- **LangGraph** — Stateful multi-step agent orchestration for rule extraction and simulation
- **LangChain + langchain_neo4j** — Text-to-Cypher retriever, LLM chain orchestration
- **OpenAI text-embedding-3-large** — Node embeddings (or nomic-embed-code for local/free alternative)
- **GPT-4o / Gemini 2.0 Flash** — Rule extraction, persona rendering, PR impact summaries

### Backend Services
- **FastAPI** — REST API endpoints and webhook receiver
- **PostgreSQL (Supabase)** — User accounts, job metadata, export history
- **Upstash Redis** — Query response cache (key-value store)
- **Docker Compose** — Local development environment

### Frontend and Visualization
- **Next.js** — Web application framework
- **React Flow** — Interactive graph visualization (subgraph explorer)
- **Mermaid.js** — Sequence, component, and state diagram rendering
- **shadcn/ui** — UI component library

### Infrastructure and DevOps
- **Vercel** — Frontend hosting (free tier)
- **Railway / Render** — Backend hosting (free tier with sleep on inactivity)
- **Neo4j AuraDB Free** — Cloud graph database (up to 200k nodes, 400k relationships)
- **GitHub App / Webhooks** — Repository integration and change notifications
- **Clerk / NextAuth** — GitHub OAuth and user session management

---

## Caching Strategy

### Three-Layer Caching

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| Rule Node Cache | Neo4j graph nodes | Extracted rules persist until source code changes |
| Query Response Cache | Redis key-value | Cache Persona Explainer responses by rule IDs + persona mode |
| LLM Prompt Cache | Anthropic/OpenAI API | Server-side caching of repeated prompt prefixes |

**Invalidation Strategy:** Redis cache entries invalidated when any of their constituent rule node IDs are marked stale during re-indexing. Clean, deterministic invalidation boundaries.

---

## Cost Analysis

### Demo/MVP Cost Estimate

| Component | Tool/Service | Cost |
|-----------|-------------|------|
| LLM (indexing) | Gemini 2.0 Flash free tier | $0 |
| LLM (query time) | Gemini 2.0 Flash free tier | $0 |
| Embeddings | text-embedding-3-small | ≈$0.02 one-time |
| Neo4j | AuraDB Free tier | $0/month |
| Redis | Upstash free tier | $0/month |
| Backend hosting | Railway free tier | $0/month |
| Frontend hosting | Vercel free tier | $0/month |
| PostgreSQL | Supabase free tier | $0/month |
| **Total (1–2 repos)** | | **≈$0–3 setup, ≈$0–5/month** |

**Production Scaling:** Swap to GPT-4o-mini or GPT-4o selectively once paying customers justify higher LLM costs. Infrastructure scales on-demand with Neo4j AuraDB Professional and Railway/Render paid tiers.

---

## Development Phases

### Phase 1: Core Graph (Weeks 1–2)
- Tree-sitter parsing pipeline
- Neo4j schema implementation
- Basic entity and edge extraction
- CLI indexer working on real repository

**Deliverable:** A real codebase indexed into Neo4j with queryable graph structure.

### Phase 2: Rule Extraction (Weeks 3–4)
- LangGraph agent implementation
- Conditional branch traversal logic
- Rule node creation and storage
- Domain clustering via GraphRAG communities

**Deliverable:** Extracted Rule nodes visible in Neo4j, manually queryable.

### Phase 3: Persona Explainer and Basic UI (Weeks 5–6)
- Three persona rendering modes functional
- Basic Next.js web UI with rule browser
- Persona mode switcher
- Sequence and component diagram generation

**Deliverable:** Usable web interface where users can search and explore rules in all three personas.

### Phase 4: Rule Change Simulator (Weeks 7–8)
- GitHub webhook integration
- Branch diff logic
- PR comment bot
- Incremental re-indexing pipeline
- End-to-end demo on live pull request

**Deliverable:** Fully functional MVP demonstrating all three core features on real repositories with real PRs.

---

## Competitive Differentiation

### vs. Claude Code / GitHub Copilot Chat

| Feature | Claude Code (Flat RAG) | CodeLens (GraphRAG) |
|---------|------------------------|---------------------|
| Retrieval | Text chunk retrieval (semantic only) | Graph traversal (structural + semantic) |
| Cross-file reasoning | Weak cross-file reasoning | Native multi-hop relationship traversal |
| Audience | Developer-only | Multi-audience (Dev, PM, Legal) |
| Change awareness | Reactive Q&A only | Proactive PR impact detection |
| Knowledge persistence | No persistent business knowledge | Accumulated rule registry |
| Accuracy | High hallucination risk on structure | Graph-grounded, verifiable answers |
| Re-indexing | No change awareness | Real-time incremental re-indexing |

**Value Proposition:** CodeLens is not a better code assistant — it is a persistent structural intelligence layer that serves the entire organization and proactively surfaces what changed, what it means, and why it matters.

---

## Success Metrics

### Technical Metrics
- Indexing speed: < 5 minutes for 100k lines of code
- Query latency: < 2 seconds for rule search with persona rendering
- PR simulation latency: < 45 seconds from push to comment
- Rule extraction accuracy: > 90% precision on human-validated sample

### Product Metrics
- Time to domain understanding: 80% reduction (from weeks to hours)
- Silent business logic changes: 100% detection rate in monitored paths
- Cross-team rule queries: PM and compliance usage > 30% of total queries
- Compliance audit preparation time: < 2 hours for full domain export

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM extraction quality varies across codebases | Validate on diverse repos during alpha, tune prompts iteratively |
| Large monorepos exceed free-tier limits | Implement incremental indexing, domain-scoped indexing for MVP |
| Developers ignore PR comments | Integrate with CI gates (optional rule for breaking changes) |
| Graph schema doesn't capture critical patterns | Design schema collaboratively with pilot users, iterate based on feedback |
| Webhook failures cause stale index | Implement webhook retry logic, manual re-index fallback, staleness warning UI |

---

## Conclusion

CodeLens transforms code from a black box into a queryable, multi-audience knowledge system. By combining AST parsing, graph structure, and LLM intelligence, it provides capabilities no flat RAG system can match: structural guarantees, persistent business knowledge, proactive change detection, and persona-aware rendering.

The MVP scope is tightly focused on three features that form a complete value loop, built using 60% reusable open-source tools and 40% custom integration logic. Total development time: 8 weeks with a 2–3 engineer team. Total demo cost: effectively $0–5/month using free-tier infrastructure.

---

## Next Steps

1. Validate with 3–5 pilot teams on real codebases
2. Gather feedback on rule extraction quality and UI workflows
3. Iterate schema and prompts based on edge cases discovered
4. Build IDE extension (Phase 2) for developer adoption
5. Expand to Java, Go, Rust language support

---

## Project Flexibility Disclaimer

This specification represents the intended scope and technical approach for the CodeLens MVP. However, specific technology choices, tool selections, implementation details, and use case priorities may be adjusted during development based on:

- Availability and licensing of third-party tools and services
- Specific skillsets and expertise of the development team
- Technical feasibility discoveries during prototyping
- Feedback from pilot users and early adopters
- Infrastructure cost considerations and free-tier limitations
- Emerging best practices in GraphRAG and LLM orchestration

While the core vision — graph-structured code intelligence with persona-aware explanations and change detection — remains fixed, the path to achieving it may evolve iteratively. This document serves as a north star rather than a rigid contract, enabling the team to make pragmatic engineering decisions while maintaining alignment on product outcomes.
