# ADR-001 — Rule Interpretation Strategy: Index-Time Extraction vs Query-Time Interpretation

**Status:** Accepted  
**Date:** April 2026  
**Deciders:** Project team  

---

## Context

CodeLens indexes source code into a Neo4j knowledge graph. The core product promise is that business rules embedded in code become queryable, human-readable, and persona-aware — for developers, product managers, and compliance officers.

The central architectural question is: **where does the LLM interpretation of business rules happen?**

Two fundamentally different designs were evaluated.

---

## Options Considered

### Option 1 — Index-Time Extraction (Pre-computed Rules)

A background Python job runs after every indexing cycle. It traverses every `ConditionalBranch` node in the graph, aggregates the surrounding subgraph for context, and sends it to an LLM. The LLM produces three plain-text representations of the rule — one for each persona (Developer, Product, Legal) — and these are stored as fixed fields on a `Rule` node in Neo4j. At query time the MCP tool simply returns the pre-stored string. No LLM call occurs at query time.

**Advantages:**
- Query time is extremely fast — pure database read, milliseconds
- No LLM cost at query time
- Rules are browsable directly in the database without a client AI
- Persona rendering is deterministic and consistent per query

**Disadvantages:**
- Expensive and time-consuming at index time — every `ConditionalBranch` requires an LLM call (potentially hundreds per repository)
- Extracted rules go stale immediately when code changes; re-extraction pipeline must track staleness reliably
- A single `ConditionalBranch` node almost never contains a complete business rule in isolation — the rule spans a subgraph, so extraction without full context is structurally incomplete
- The pre-rendered persona text is fixed: a pre-extracted rule cannot adapt to what the querying user is actually trying to understand (a security auditor and a product manager asking about the same branch have different needs)
- Any LLM extraction error is persisted in the database and silently wrong until manually corrected
- Complex background pipeline to build, monitor, and maintain

### Option 2 — Query-Time Interpretation (On-the-fly)

The graph is indexed deterministically: Tree-sitter parses code into structured nodes (`Function`, `Class`, `ConditionalBranch`, edges for `calls`, `imports`, `defines`, etc.). No LLM runs at index time. When an agent queries the MCP server, it receives a structured subgraph — the relevant nodes and edges near the query entry point. The client LLM (Claude, GPT-4o, or whichever AI the user has) reads the subgraph and interprets the business rules in the context of the specific question being asked.

**Advantages:**
- Indexing is fast, cheap, and deterministic — no LLM calls, no extraction errors to persist
- Rules are always interpreted from the current state of the code — never stale
- The client LLM adapts the interpretation to the context of the query: a compliance audit query and a developer debugging session produce different, appropriate answers from the same subgraph
- No background pipeline complexity — indexing is a straightforward parsing step
- No stored extraction noise — the database contains only structural truth
- Persona handling is done by the client AI via a system prompt or user instruction, not pre-rendered into fixed strings

**Disadvantages:**
- Query time is slower — the client LLM must interpret the subgraph, adding latency
- Higher per-query cost — LLM tokens are consumed each time a rule interpretation is requested
- Without a client AI, the raw subgraph data is not human-readable in a standalone UI
- No pre-browsable rule list in the database for non-technical users without an AI in the loop

---

## Evaluation

The following table summarises the trade-off assessed during design:

| Dimension | Index-Time Extraction | Query-Time Interpretation |
|---|---|---|
| Query speed | Fast (DB read) | Slower (LLM call) |
| Index cost | High (LLM per node) | Low (parse only) |
| Accuracy | Static, potentially stale | Always current |
| Context quality | Fixed at extraction time | Adapts to query context |
| Pipeline complexity | High | Low |
| Persona flexibility | Pre-rendered, rigid | Dynamic via system prompt |
| Error risk | Extraction errors persist silently | No stored errors |

A third option — **hybrid (index-time cluster summaries + query-time detail)** — was also considered. In this model the LLM runs once per domain cluster (10–20 clusters per repository rather than hundreds of `ConditionalBranch` nodes) to produce a high-level domain summary. Individual rule detail is still interpreted at query time. This reduces index-time LLM cost while preserving some pre-computed structure for domain browsing. This variant is preserved as a Phase 2 upgrade path and is not excluded by this decision.

---

## Decision

**Query-Time Interpretation is adopted for the MVP.**

The graph indexes code deterministically. The MCP server returns structured subgraphs. The client LLM interprets rules in context. Persona rendering is handled by the client AI via a system prompt or user instruction.

**Primary reasons:**

1. The structural completeness problem is fundamental to Index-Time Extraction and cannot be easily fixed. A `ConditionalBranch` in isolation is almost never a complete business rule — it is a node in a subgraph. Sending it to an LLM without the full multi-hop context produces incomplete or misleading rule statements.

2. The staleness problem is ongoing and expensive to solve. Every code change requires identifying affected `ConditionalBranch` nodes, invalidating their Rule nodes, re-extracting, and verifying accuracy. This is a continuous maintenance burden disproportionate to the MVP stage.

3. The client AI already has an LLM. The interpretation cost is not zero under either option — under Index-Time Extraction the cost is paid at index time and stored; under Query-Time Interpretation it is paid at query time. The difference is that query-time interpretation keeps the interpretation accurate and context-appropriate.

4. Simplicity at the MVP stage is a priority. A deterministic parsing pipeline with no LLM dependency is easier to build, test, debug, and demonstrate.

---

## Consequences

**We accept:**
- Query responses require a client LLM in the loop — CodeLens does not stand alone as a rule browser without an AI client
- Latency per query is higher than a pure database read
- Per-query LLM cost is borne by the user's existing AI client (Claude, GPT-4o, etc.) — not by CodeLens infrastructure

**We gain:**
- Indexing is fast, predictable, and LLM-free
- Rules are always interpreted from the current code — no staleness
- Persona flexibility is unlimited — any framing the user asks for is handled by the client AI
- Background pipeline complexity is eliminated from the MVP scope

**Future upgrade path:**
Domain-level cluster summaries (Option C hybrid) can be added in Phase 2 without changing the core architecture. This would add pre-computed domain context for non-technical user browsing while keeping individual rule interpretation at query time.
