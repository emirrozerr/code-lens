# CodeLens

GraphRAG-powered code intelligence platform that indexes codebases into structured knowledge graphs and enables multi-audience business logic exploration, change impact simulation, and persona-based documentation.

## Architecture

```
code-lens/
├── backend/      # FastAPI REST API + intelligence layer
├── frontend/     # Next.js web UI
├── cli/          # Python CLI (codelens index/search/simulate/export)
└── docker-compose.yml
```

## Quick Start

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Neo4j Browser: http://localhost:7474
```

## CLI

```bash
pip install -e ./cli

codelens index --repo ./path/to/repo
codelens search "discount eligibility rules" --persona product
codelens simulate --base main --head feature/pricing
codelens export --domain payments --format pdf
```

## Development

See `backend/README.md` and `frontend/README.md` for service-specific setup.

## Stack

- **Backend:** FastAPI, Neo4j, LangGraph, Tree-sitter
- **Frontend:** Next.js, React Flow, Mermaid.js, shadcn/ui
- **Infrastructure:** Docker Compose, Neo4j AuraDB, Redis, PostgreSQL
