# CodeLens - Project Handoff & Status

**Goal:** Provide full context for any AI agent taking over the CodeLens project to resume work from a cold start.

## 1. Project Overview
CodeLens is a code intelligence infrastructure layer that parses local repositories, extracts structural semantics (AST, functions, classes, call chains), writes them to a Neo4j knowledge graph, and makes that graph queryable via a Model Context Protocol (MCP) server. It enables AI tools (Claude, Copilot, Cursor) to retrieve precise structural context about the codebase.

## 2. Technical Stack
- **Language/Environment:** Python 3.11+, Click (CLI)
- **Parser:** Tree-sitter (Java implemented as MVP)
- **Graph Database:** Neo4j (local via Docker Compose `neo4j:5-community` with APOC & GDS)
- **Background Watcher:** `watchdog` library for real-time incremental re-indexing
- **MCP Framework:** `mcp` (FastMCP over SSE)
- **Community Detection:** `networkx` and `python-louvain`

## 3. Current State (As of May 2026)
We have successfully implemented **Phase 1 (Core Ingestion)**, **Phase 2 (MCP Server)**, and **Phase 3 (Domain Clustering)**.

### What is DONE:
- **Project Scaffold:** Monorepo structure, `pyproject.toml`, pytest, `docker-compose.yml`.
- **Java Parser:** Extracts Files, Classes, Interfaces, Constructors, Methods, ConditionalBranches, ReturnStatements, and resolves edges (calls, contains, returns, has_branch, imports).
- **Repository Indexer:** Handles incremental updates (only re-parsing changed files).
- **Watcher Daemon:** Background process using `watchdog` to monitor the file system for changes.
- **Graph Ingestion Layer:** Persists the graph structure to Neo4j with optimized batch queries and constraints.
- **MCP Server (FastMCP):** A robust SSE-based server exposing `search_nodes`, `get_code_context`, `get_callers`, `get_callees`, `get_domains`, and `get_domain`.
- **Dockerization:** `docker-compose up -d` runs both Neo4j and the MCP server (exposed on port 8000 via SSE).
- **Domain Clustering (Phase 3):** Analyzes the graph using Louvain community detection to group interconnected nodes into business Domains, passing them to the Gemini API to generate plain-English architectural summaries.

### What is PLANNED NEXT:
- **Phase 4 (Query Integration):** Actually pointing an LLM agent (Claude/Cursor) to the `codelens-mcp` server endpoint to prove it improves the agent's contextual awareness of large codebases.

## 4. Key Architectural Decisions (ADRs)
- **ADR-001:** Business rules are synthesized by the client AI at query-time based on the returned code subgraph. We do not statically extract business rules during indexing.
- **ADR-002:** Hybrid code discovery. CodeLens does not embed vector search. The agent discovers entry points using standard tools (grep, ls) or a native Neo4j Lucene text index (`search_nodes`), then calls CodeLens for deep structural context.
- **Core Philosophy:** "Map vs Content". CodeLens stores structural metadata (signatures, edges, line numbers) but NOT code bodies. Agents use their native `read_file` capabilities to read the actual code once CodeLens gives them the map.

## 5. GitHub Projects Board Tracking
All tasks must strictly map to issues in the GitHub repository.

## 6. How to Resume Work
1. Source the virtual environment: `source .venv/bin/activate`
2. Spin up the backend (Neo4j + MCP): `docker compose up -d`
3. Run tests to verify state: `pytest`
4. Re-index a test repository and build clusters: `export GEMINI_API_KEY="..."; codelens ingest tests/fixtures/spring-petclinic --cluster`
