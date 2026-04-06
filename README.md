# CodeLens

**GraphRAG-Powered Code Intelligence Platform**

CodeLens is a code intelligence platform that indexes codebases into structured knowledge graphs and uses GraphRAG to enable multi-audience business logic exploration, change impact simulation, and persona-based documentation. 

Unlike traditional code assistants that rely on flat text retrieval, CodeLens provides structural guarantees, cross-file reasoning, and persistent business knowledge extraction.

## Core Capabilities

1. **Business Logic Mapper**: Extracts and catalogs every business rule from code with full graph traceability.
2. **Persona-Based Explainer**: Re-renders any rule in Developer (technical), Product (functional), or Legal (compliance) language.
3. **Rule Change Simulator**: Automatically detects business logic changes in pull requests and posts impact summaries.

## Target Audience

- **Software Engineers:** Quickly understand complex domains and dependencies.
- **Product Managers:** Query current system behavior to write accurate product specs.
- **Compliance Officers:** Audit actual system rules traced back to code.
- **Technical Leads:** Monitor structural and business logic changes across PRs.

## Tech Stack

- **Parsing & Ingestion:** Tree-sitter, GitPython, Celery + Redis
- **Graph & Intelligence:** Neo4j, Microsoft GraphRAG, LangGraph, LangChain, OpenAI/Gemini
- **Backend Services:** FastAPI, PostgreSQL, Upstash Redis
- **Frontend & Visualization:** Next.js, React Flow, Mermaid.js, shadcn/ui

## Key Use Cases

- **Domain Onboarding:** Understand unfamiliar business logic in minutes instead of weeks.
- **Spec Writing:** Query current behavior before writing new requirements to avoid shadow rules.
- **PR Simulation:** Automatically diff business logic on PRs and post impact summaries.
- **Auditing:** Export policy-clause formatted code rules for legal and compliance.

## Architecture Data Flow

1. **Ingestion:** Git repo → Tree-sitter AST parser → Entity/edge extractor
2. **Storage:** Neo4j stores all code nodes, vectors, and rules.
3. **Intelligence:** GraphRAG community detection + LangGraph Agent for rule extraction.
4. **Presentation:** Web UI and CLI query via Cypher/Vector search.

---

*For detailed specifications, features, and requirements, please refer to the [Project Specification](CodeLens_Project_Specification.md) document.*