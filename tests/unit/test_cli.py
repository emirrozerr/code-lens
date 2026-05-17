"""Unit tests for the Click command-line interface.

These tests use click's CliRunner to run commands in-process, allowing 
full code coverage of codelens/cli.py.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from codelens.cli import cli

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_cli_index_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--help"])
    assert result.exit_code == 0
    assert "Index a Java repository" in result.output


def test_cli_index_basic(tmp_path):
    # Copy sample repo contents to temp path so we don't write output inside original fixtures
    temp_repo = tmp_path / "repo"
    temp_repo.mkdir()
    for f in FIXTURES.rglob("*.java"):
        dest = temp_repo / f.relative_to(FIXTURES)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f.read_text())

    output_json = tmp_path / "result.json"

    runner = CliRunner()
    result = runner.invoke(cli, [
        "index",
        str(temp_repo),
        "--stats",
        "--verbose",
        "--output", str(output_json)
    ])

    assert result.exit_code == 0
    assert "CodeLens Indexer" in result.output
    assert "Done" in result.output
    assert output_json.exists()

    # Verify JSON structure
    data = json.loads(output_json.read_text())
    assert "nodes" in data
    assert "edges" in data


def test_cli_ingest_basic():
    with patch("codelens.graph.neo4j_client.Neo4jClient") as MockClient:
        mock_instance = MockClient.return_value
        
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", str(FIXTURES), "--clear", "--verbose"])
        
        assert result.exit_code == 0
        assert "Connecting to Neo4j..." in result.output
        assert "Clearing database..." in result.output
        assert "Ingestion complete!" in result.output
        
        mock_instance.clear_database.assert_called_once()
        mock_instance.setup_schema.assert_called_once()
        mock_instance.ingest_parse_result.assert_called_once()


def test_cli_ingest_failure():
    with patch("codelens.graph.neo4j_client.Neo4jClient", side_effect=Exception("Connection refused")):
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", str(FIXTURES)])
        
        assert result.exit_code == 0  # CLI catches and prints, exits gracefully
        assert "Ingestion failed: Connection refused" in result.output


def test_cli_ingest_empty_repo(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", str(tmp_path)])
    
    assert result.exit_code == 0
    assert "No parseable files found" in result.output


def test_cli_ingest_cluster():
    with patch("codelens.graph.neo4j_client.Neo4jClient"), \
         patch("codelens.graph.clustering.DomainClusterer") as MockClusterer:
        
        mock_clusterer_inst = MockClusterer.return_value
        mock_clusterer_inst.run_clustering.return_value = ["Domain 1", "Domain 2"]
        
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", str(FIXTURES), "--cluster"])
        
        assert result.exit_code == 0
        assert "Running community detection" in result.output
        assert "Discovered and summarized 2 domains" in result.output


def test_cli_watch():
    with patch("codelens.watcher.WatcherDaemon") as MockDaemon:
        mock_daemon_inst = MockDaemon.return_value
        
        # Make start() return instantly instead of blocking in a loop
        mock_daemon_inst.start.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["watch", str(FIXTURES)])
        
        assert result.exit_code == 0
        assert "CodeLens Watcher" in result.output
        assert "Watching:" in result.output
        mock_daemon_inst.start.assert_called_once()


def test_cli_mcp_stdio():
    with patch("codelens.mcp_server.server.mcp") as mock_mcp:
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "--transport", "stdio"])
        
        assert result.exit_code == 0
        assert "Starting FastMCP on stdio..." in result.output
        mock_mcp.run.assert_called_once_with()


def test_cli_mcp_sse():
    with patch("codelens.mcp_server.server.mcp") as mock_mcp:
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "--transport", "sse", "--host", "0.0.0.0", "--port", "9000"])
        
        assert result.exit_code == 0
        assert "Starting FastMCP on SSE (0.0.0.0:9000)..." in result.output
        mock_mcp.run.assert_called_once_with(transport="sse")


def test_cli_ingest_failure_verbose():
    with patch("codelens.graph.neo4j_client.Neo4jClient", side_effect=Exception("DB Failure")):
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", str(FIXTURES), "--verbose"])
        
        assert result.exit_code == 0
        assert "Ingestion failed: DB Failure" in result.output


def test_cli_mcp_failure_verbose():
    with patch("codelens.mcp_server.server.mcp") as mock_mcp:
        mock_mcp.run.side_effect = Exception("Port in use")
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "--verbose"])
        
        assert result.exit_code == 0
        assert "Server failed: Port in use" in result.output


def test_cli_index_with_warnings(tmp_path):
    # Mock indexer to return warnings/errors
    from codelens.indexer.models import ParseResult
    mock_result = ParseResult(filepath=str(tmp_path), nodes=[], edges=[], errors=["Unparseable file Foo.java", "Error on line 12"])
    
    with patch("codelens.cli.Indexer") as MockIndexer:
        MockIndexer.return_value.index_repository.return_value = mock_result
        
        runner = CliRunner()
        result = runner.invoke(cli, ["index", str(tmp_path)])
        
        assert result.exit_code == 0
        assert "2 warning(s)" in result.output
        assert "Unparseable file Foo.java" in result.output

