"""Indexer stub.

Orchestrates parsing and storing code nodes/edges in Neo4j.
Supports full indexing and incremental re-indexing of changed files.
"""

from pathlib import Path

from app.ingestion.parser import ParseResult, parse_repository


def index_repository(repo_path: Path) -> None:
    """Full index: parse repo and store all nodes/edges in Neo4j.

    TODO: Call parse_repository, write nodes/edges to Neo4j, generate embeddings.
    """
    result: ParseResult = parse_repository(repo_path)
    # TODO: persist result to Neo4j via graph.neo4j_client


def reindex_files(repo_path: Path, changed_files: list[str]) -> None:
    """Incremental re-index: re-parse only changed files and update Neo4j.

    TODO: Mark stale nodes, re-parse changed files, update graph, invalidate cache.
    """
