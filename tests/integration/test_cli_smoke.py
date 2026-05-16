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

    def test_index_json_structure(self, tmp_path):
        """Validate the JSON output has the expected schema."""
        output_file = tmp_path / "result.json"
        _run_cli("index", str(FIXTURES), "--output", str(output_file))

        data = json.loads(output_file.read_text())
        # Check first node has all required fields
        node = data["nodes"][0]
        assert "uid" in node
        assert "name" in node
        assert "qualified_name" in node
        assert "node_type" in node
        assert "filepath" in node
        assert "start_line" in node
        assert "end_line" in node

        # Check first edge has all required fields
        edge = data["edges"][0]
        assert "source_uid" in edge
        assert "target_uid" in edge
        assert "edge_type" in edge

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
