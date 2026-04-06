"""CodeLens CLI.

Commands:
  codelens index    -- Index a repository into the knowledge graph
  codelens search   -- Search for business rules
  codelens simulate -- Simulate rule changes between two branches
  codelens export   -- Export rules or domain views
"""

import click


@click.group()
def cli() -> None:
    """CodeLens — GraphRAG-powered code intelligence."""


@cli.command()
@click.option("--repo", required=True, type=click.Path(exists=True), help="Path to repository")
def index(repo: str) -> None:
    """Index a repository into the knowledge graph."""
    click.echo(f"Indexing repository: {repo}")
    # TODO: call backend.app.ingestion.indexer.index_repository


@cli.command()
@click.argument("query")
@click.option(
    "--persona",
    type=click.Choice(["developer", "product", "legal"]),
    default="developer",
    show_default=True,
)
def search(query: str, persona: str) -> None:
    """Search for business rules matching QUERY."""
    click.echo(f"Searching for '{query}' (persona: {persona})")
    # TODO: call REST API /api/rules/search


@cli.command()
@click.option("--base", required=True, help="Base branch or commit")
@click.option("--head", required=True, help="Head branch or commit")
@click.option("--repo", default=".", type=click.Path(exists=True), help="Path to repository")
def simulate(base: str, head: str, repo: str) -> None:
    """Simulate business logic changes between BASE and HEAD."""
    click.echo(f"Simulating changes: {base} → {head} in {repo}")
    # TODO: call backend.app.simulator.change_detector.simulate


@cli.command()
@click.option("--domain", help="Domain to export")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["pdf", "json"]),
    default="json",
    show_default=True,
)
@click.option("--output", "-o", default="export", help="Output file path (without extension)")
def export(domain: str | None, fmt: str, output: str) -> None:
    """Export rules or a domain view."""
    click.echo(f"Exporting domain={domain!r} as {fmt} to {output}.{fmt}")
    # TODO: call REST API /api/rules or /api/domains and render output


if __name__ == "__main__":
    cli()
