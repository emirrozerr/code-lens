"""CodeLens CLI — command-line interface for repository indexing.

Usage:
    codelens index ./path/to/repo          Full re-index of a repository
    codelens index ./path/to/repo --stats  Show statistics after indexing
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from codelens.indexer.indexer import Indexer
from codelens.indexer.models import ParseResult


def _setup_logging(verbose: bool) -> None:
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(package_name="codelens")
def cli():
    """CodeLens — Code intelligence infrastructure for AI agents."""
    pass


# ---------------------------------------------------------------------------
# index command
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@click.option("--stats", "-s", is_flag=True, help="Print detailed statistics after indexing.")
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write the parse result as JSON to this file.",
)
def index(repo_path: str, verbose: bool, stats: bool, output: str | None):
    """Index a Java repository into code graph nodes and edges.

    REPO_PATH is the path to the repository root to index.
    """
    _setup_logging(verbose)
    logger = logging.getLogger("codelens.cli")

    repo = Path(repo_path)
    click.echo(f"\n  CodeLens Indexer")
    click.echo(f"  {'─' * 40}")
    click.echo(f"  Repository:  {repo}")
    click.echo()

    indexer = Indexer()

    with click.progressbar(length=1, label="  Indexing") as bar:
        result = indexer.index_repository(repo)
        bar.update(1)

    click.echo()

    # Print errors if any
    if result.errors:
        click.secho(f"  ⚠  {len(result.errors)} warning(s):", fg="yellow")
        for err in result.errors[:10]:
            click.echo(f"     • {err}")
        if len(result.errors) > 10:
            click.echo(f"     ... and {len(result.errors) - 10} more")
        click.echo()

    # Print summary
    _print_summary(result)

    if stats:
        _print_stats(result)

    # Write JSON output
    if output:
        output_path = Path(output)
        data = result.model_dump(mode="json")
        output_path.write_text(json.dumps(data, indent=2))
        click.echo(f"  📄 Results written to {output_path}")
        click.echo()

    click.secho("  ✓ Done\n", fg="green", bold=True)


# ---------------------------------------------------------------------------
# watch command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def watch(repo_path: str, verbose: bool):
    """Start a background daemon to incrementally index a repository.

    REPO_PATH is the path to the repository root to watch.
    """
    _setup_logging(verbose)
    from codelens.watcher import WatcherDaemon

    repo = Path(repo_path)
    click.echo(f"\n  CodeLens Watcher")
    click.echo(f"  {'─' * 40}")
    click.echo(f"  Watching:  {repo}")
    click.echo("  Press Ctrl+C to stop.\n")

    daemon = WatcherDaemon(repo)
    daemon.start()


# ---------------------------------------------------------------------------
# ingest command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@click.option("--clear", is_flag=True, help="Clear the Neo4j database before ingesting.")
def ingest(repo_path: str, verbose: bool, clear: bool):
    """Parse a repository and ingest it into the Neo4j graph database.

    REPO_PATH is the path to the repository root.
    """
    _setup_logging(verbose)
    from codelens.indexer.indexer import Indexer
    from codelens.graph.neo4j_client import Neo4jClient

    repo = Path(repo_path)
    click.echo(f"\n  CodeLens Ingestion")
    click.echo(f"  {'─' * 40}")
    click.echo(f"  Repository:  {repo}")

    # 1. Parse
    click.echo("\n  1. Parsing repository...")
    indexer = Indexer()
    result = indexer.index_repository(repo)

    if not result.nodes:
        click.echo("  ℹ  No parseable files found. Aborting ingestion.")
        return

    # 2. Ingest
    click.echo("\n  2. Connecting to Neo4j...")
    try:
        client = Neo4jClient()
        if clear:
            click.echo("  [!] Clearing database...")
            client.clear_database()
            
        client.setup_schema()
        
        click.echo(f"  [+] Ingesting {len(result.nodes)} nodes and {len(result.edges)} edges...")
        client.ingest_parse_result(result)
        client.close()
        
        click.echo("\n  ✓ Ingestion complete!")
    except Exception as e:
        click.secho(f"\n  ✖ Ingestion failed: {e}", fg="red")
        if verbose:
            import traceback
            traceback.print_exc()

# ---------------------------------------------------------------------------
# mcp command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def mcp(verbose: bool):
    """Start the Model Context Protocol (MCP) server for CodeLens.
    
    This exposes the Neo4j graph database to AI agents using standard tools.
    """
    _setup_logging(verbose)
    from codelens.mcp_server.server import mcp as mcp_server
    
    click.echo("\n  CodeLens MCP Server")
    click.echo(f"  {'─' * 40}")
    click.echo("  Starting FastMCP on stdio...\n")
    
    try:
        mcp_server.run()
    except Exception as e:
        click.secho(f"\n  ✖ Server failed: {e}", fg="red")
        if verbose:
            import traceback
            traceback.print_exc()

# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------


def _print_summary(result: ParseResult) -> None:
    """Print a compact summary table."""
    from collections import Counter

    node_counts = Counter(n.node_type.value for n in result.nodes)
    edge_counts = Counter(e.edge_type.value for e in result.edges)
    unresolved = sum(1 for e in result.edges if e.target_uid.startswith("unresolved:"))

    click.echo(f"  Nodes ({len(result.nodes)} total)")
    click.echo(f"  {'─' * 30}")
    for ntype, count in sorted(node_counts.items()):
        click.echo(f"    {ntype:<24} {count:>5}")

    click.echo()
    click.echo(f"  Edges ({len(result.edges)} total)")
    click.echo(f"  {'─' * 30}")
    for etype, count in sorted(edge_counts.items()):
        click.echo(f"    {etype:<24} {count:>5}")

    click.echo()
    if unresolved:
        click.secho(
            f"  ℹ  {unresolved} unresolved call target(s) — will be resolved when graph is built",
            fg="cyan",
        )
        click.echo()


def _print_stats(result: ParseResult) -> None:
    """Print detailed statistics about the parse result."""
    click.echo(f"  Detailed Statistics")
    click.echo(f"  {'─' * 40}")

    # Files
    files = [n for n in result.nodes if n.node_type.value == "File"]
    click.echo(f"    Files indexed:        {len(files)}")

    # Classes
    classes = [n for n in result.nodes if n.node_type.value == "Class"]
    click.echo(f"    Classes found:        {len(classes)}")
    for cls in classes[:10]:
        click.echo(f"      • {cls.qualified_name} ({cls.filepath}:{cls.start_line})")

    # Methods
    methods = [n for n in result.nodes if n.node_type.value == "Function"]
    click.echo(f"    Methods found:        {len(methods)}")

    # Constructors
    ctors = [n for n in result.nodes if n.node_type.value == "Constructor"]
    click.echo(f"    Constructors found:   {len(ctors)}")

    # Conditionals
    branches = [n for n in result.nodes if n.node_type.value == "ConditionalBranch"]
    click.echo(f"    Conditional branches: {len(branches)}")

    click.echo()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
