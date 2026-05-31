# Contributor Setup Guide

This guide helps new contributors set up a local CodeLens development environment.

## Prerequisites

- Git
- Python 3.11+
- Docker Desktop

## Configure Environment

```bash
cp .env.example .env
```
Windows users can create a .env file manually by copying the contents of .env.example.

Review the Neo4j credentials and related environment variables before starting the services.

## Clone Repository

```bash
git clone https://github.com/emirrozerr/code-lens.git
cd code-lens
```

## Create Virtual Environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -e ".[dev]"
```

## Start Neo4j

```bash
docker compose up -d
```
If you use the legacy Docker Compose plugin, docker-compose up -d also works.

The default compose configuration starts both Neo4j and the MCP server.

To start only Neo4j:

```bash
docker compose up -d neo4j
```

Neo4j Browser:

```text
http://localhost:7474
```

Default credentials:

```text
Username: neo4j
Password: codelens_dev
```

## Verify Setup

```bash
pytest
```

If tests pass and Neo4j is reachable, the local environment is ready.

## Verify Installation

```bash
codelens --version
```

If the command returns a version number, the CLI installation is working correctly.