# CodeLens - Project Handoff & Status

**Goal:** Provide full context for any AI agent taking over the CodeLens project to resume work from a cold start.

## 1. Project Overview
CodeLens is a code intelligence infrastructure layer that parses local repositories, extracts structural semantics (AST, functions, classes, call chains), writes them to a Neo4j knowledge graph, and makes that graph queryable via a Model Context Protocol (MCP) server. It enables AI tools (Claude, Copilot, Cursor) to retrieve precise structural context about the codebase.

## 2. Technical Stack
- **Language/Environment:** Python 3.11+, Click (CLI), FastAPI (planned)
- **Parser:** Tree-sitter (Java implemented as MVP)
- **Graph Database:** Neo4j (local via Docker Compose `neo4j:5-community` with APOC & GDS)
- **Background Watcher:** `watchdog` library for real-time incremental re-indexing

## 3. Current State (As of May 2026)
We are actively executing **Phase 1 (Core Ingestion)**.

### What is DONE:
- **Project Scaffold:** Monorepo structure, `pyproject.toml`, pytest, `docker-compose.yml` for Neo4j.
- **Java Parser (`src/codelens/indexer/java_parser.py`):** Uses Tree-sitter to parse `.java` files into Pydantic models (`CodeNode`, `CodeEdge`). Extracts Files, Classes, Interfaces, Constructors, Methods, ConditionalBranches, ReturnStatements, and resolves edges (calls, contains, returns, has_branch, imports).
- **Repository Indexer (`src/codelens/indexer/indexer.py`):** Walks a repository, orchestrates file parsing, resolves cross-file method calls via name matching, and handles **incremental updates** (only re-parsing changed files).
- **Watcher Daemon (`src/codelens/watcher.py`):** Background process using `watchdog` to monitor the file system for changes to `.java` files, debounces them, and triggers incremental indexing.
- **CLI (`src/codelens/cli.py`):** `codelens index <repo>` and `codelens watch <repo>` commands. Fully tested and operational.
- **Testing:** Comprehensive test suite (`pytest`) covering unit tests for parsers, event queues, and integration tests with a cloned Spring PetClinic repo. Currently 48/48 passing.

### What is IN PROGRESS:
- **Graph Ingestion Layer:** Taking the `ParseResult` from the Indexer and actually writing it to the Neo4j database.
- Defining the Neo4j schema constraints (Unique UIDs, indexes on node properties).
- Pushing the medium-sized `spring-petclinic` repository into Neo4j via Docker.

### What is PLANNED NEXT:
- **Phase 2 (Graph + MCP):** Building the MCP server surface using the official Python MCP SDK to allow queries against the Neo4j graph.
- **Phase 3 (Intelligence):** Community detection (Leiden) to cluster the code into business domains, then summarizing them using Gemini.

## 4. Key Architectural Decisions (ADRs)
- **ADR-001:** Business rules are synthesized by the client AI at query-time based on the returned code subgraph. We do not statically extract business rules during indexing.
- **ADR-002:** Hybrid code discovery. CodeLens does not embed vector search. The agent discovers entry points using standard tools (grep, ls) or a native Neo4j Lucene text index (`search_nodes`), then calls CodeLens for deep structural context.

## 5. GitHub Projects Board Tracking
All tasks must strictly map to issues in the GitHub repository.
- Epic: #6 (Code Parsing and Graph Indexing)
- Current Active Story: #22 (Neo4j Graph Schema & Ingestion)

## 6. How to Resume Work
1. Source the virtual environment: `source .venv/bin/activate`
2. Spin up Neo4j: `docker compose up -d`
3. Run tests to verify state: `pytest`
4. The Spring PetClinic repository is used for integration testing and is checked out at `tests/fixtures/spring-petclinic`.
