"""Smoke tests for the CLI — validates the codelens command works end-to-end.

These tests invoke the CLI as a subprocess (just like a real user would)
and validate the output and exit codes.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"
CODELENS = ["codelens"]


def _run_cli(*args: str, expect_fail: bool = False) -> subprocess.CompletedProcess:
    """Helper to run the codelens CLI as a subprocess."""
    result = subprocess.run(
        [*CODELENS, *args],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    if not expect_fail:
        assert result.returncode == 0, f"CLI failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    return result


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


class TestCLISmoke:
    """Basic smoke tests — does the CLI start, run, and exit cleanly?"""

    def test_help_command(self):
        result = _run_cli("--help")
        assert "CodeLens" in result.stdout
        assert "index" in result.stdout

    def test_index_help(self):
        result = _run_cli("index", "--help")
        assert "REPO_PATH" in result.stdout
        assert "--verbose" in result.stdout
        assert "--stats" in result.stdout
        assert "--output" in result.stdout

    def test_version(self):
        result = _run_cli("--version")
        assert "0.1.0" in result.stdout


class TestCLIIndex:
    """Tests the `codelens index` command against the sample fixture repo."""

    def test_index_basic(self):
        result = _run_cli("index", str(FIXTURES))
        assert "Done" in result.stdout
        assert "Nodes" in result.stdout
        assert "Edges" in result.stdout

    def test_index_with_stats(self):
        result = _run_cli("index", str(FIXTURES), "--stats")
        assert "Detailed Statistics" in result.stdout
        assert "Files indexed" in result.stdout
        assert "Classes found" in result.stdout
        assert "ShoppingCart" in result.stdout

    def test_index_json_output(self, tmp_path):
        output_file = tmp_path / "result.json"
        _run_cli("index", str(FIXTURES), "--output", str(output_file))

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0
    def test_index_verbose(self):
        result = _run_cli("index", str(FIXTURES), "--verbose")
        assert "Done" in result.stdout

    def test_index_nonexistent_path(self):
        """Should fail with a clear error for a nonexistent path."""
        result = subprocess.run(
            [*CODELENS, "index", "/nonexistent/path"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


class TestCLIPythonIndex:
    """Tests the `codelens index` command against Python files."""

    def test_index_python_file(self, tmp_path):
        py_file = tmp_path / "service.py"
        py_file.write_text("class MyService:\n    def run(self):\n        pass\n")
        result = _run_cli("index", str(tmp_path))
        assert "Done" in result.stdout
        assert "Nodes" in result.stdout

    def test_index_python_json_output(self, tmp_path):
        py_file = tmp_path / "service.py"
        py_file.write_text("class MyService:\n    def run(self):\n        pass\n")
        output_file = tmp_path / "result.json"
        _run_cli("index", str(tmp_path), "--output", str(output_file))

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        classes = [n for n in data["nodes"] if n["node_type"] == "Class"]
        funcs = [n for n in data["nodes"] if n["node_type"] == "Function"]
        assert len(classes) == 1
        assert classes[0]["name"] == "MyService"
        assert len(funcs) == 1
        assert funcs[0]["name"] == "run"

    def test_index_mixed_java_python(self, tmp_path):
        """Indexing a directory with both Java and Python files works."""
        (tmp_path / "Main.java").write_text("public class Main {}")
        (tmp_path / "app.py").write_text("class App:\n    pass\n")
        output_file = tmp_path / "result.json"
        _run_cli("index", str(tmp_path), "--output", str(output_file))

        data = json.loads(output_file.read_text())
        files = [n for n in data["nodes"] if n["node_type"] == "File"]
        assert len(files) == 2
        file_names = {f["name"] for f in files}
        assert file_names == {"Main.java", "app.py"}


class TestCLIEndToEnd:
    """Full end-to-end pipeline test: index -> ingest -> query MCP tools."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_neo4j(self):
        """Skip if Neo4j is not running."""
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "codelens_dev"))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
        except Exception:
            pytest.skip("Neo4j not available for end-to-end test")

    def test_full_pipeline(self):
        """Index the sample-java-repo, ingest it, and verify MCP tools return correct data."""
        # Step 1: Ingest via CLI
        _run_cli("ingest", str(FIXTURES))

        # Step 2: Verify MCP tools work against ingested data
        from codelens.mcp_server.server import search_nodes, get_code_context

        result = search_nodes("ShoppingCart")
        assert "ShoppingCart" in result
        assert "No nodes found" not in result

        context = get_code_context("calculateTotal")
        assert "Context for [Function] calculateTotal" in context
        assert "Callers" in context


class TestCLISpringPetClinic:
    """Smoke tests against the Spring PetClinic repo (real-world validation).

    These tests are skipped if the PetClinic repo hasn't been cloned.
    """

    PETCLINIC = Path(__file__).resolve().parent.parent / "fixtures" / "spring-petclinic"

    @pytest.fixture(autouse=True)
    def _skip_if_not_cloned(self):
        if not self.PETCLINIC.exists():
            pytest.skip("spring-petclinic not cloned — run: git clone --depth 1 https://github.com/spring-projects/spring-petclinic.git tests/fixtures/spring-petclinic")

    def test_petclinic_indexes_successfully(self):
        result = _run_cli("index", str(self.PETCLINIC))
        assert "Done" in result.stdout

    def test_petclinic_finds_all_main_classes(self, tmp_path):
        output_file = tmp_path / "petclinic.json"
        _run_cli("index", str(self.PETCLINIC), "--output", str(output_file))

        data = json.loads(output_file.read_text())
        classes = [n for n in data["nodes"] if n["node_type"] == "Class"]

        class_names = {c["name"] for c in classes}
        # Core PetClinic domain classes
        assert "Pet" in class_names
        assert "Owner" in class_names
        assert "Vet" in class_names
        assert "Visit" in class_names

    def test_petclinic_no_errors(self, tmp_path):
        output_file = tmp_path / "petclinic.json"
        _run_cli("index", str(self.PETCLINIC), "--output", str(output_file))

        data = json.loads(output_file.read_text())
        # There may be some syntax error warnings from test files,
        # but there should be no fatal errors
        assert len(data.get("errors", [])) < 5
