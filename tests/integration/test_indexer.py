"""Integration tests for the Indexer — tests the full pipeline across multiple files."""

from pathlib import Path

import pytest

from codelens.indexer.indexer import Indexer
from codelens.indexer.models import EdgeType, NodeType

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"


@pytest.fixture
def indexer():
    return Indexer()


@pytest.fixture
def repo_result(indexer):
    """Run the full indexer on the sample Java repository."""
    return indexer.index_repository(FIXTURES)


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------


class TestFullIndexing:
    """Tests the full indexing pipeline on the sample-java-repo fixture."""

    def test_all_files_indexed(self, repo_result):
        files = [n for n in repo_result.nodes if n.node_type == NodeType.FILE]
        assert len(files) == 3

    def test_all_classes_found(self, repo_result):
        classes = [n for n in repo_result.nodes if n.node_type == NodeType.CLASS]
        class_names = {c.name for c in classes}
        assert class_names == {"ShoppingCart", "CartItem", "CheckoutService"}

    def test_cross_file_calls_resolved(self, repo_result):
        """Call resolution should resolve calls between files in the same repo."""
        resolved_calls = [
            e for e in repo_result.edges
            if e.edge_type == EdgeType.CALLS
            and not e.target_uid.startswith("unresolved:")
        ]
        # We should have at least some resolved calls
        assert len(resolved_calls) > 0

    def test_no_duplicate_nodes(self, repo_result):
        """Every node UID should be unique."""
        uids = [n.uid for n in repo_result.nodes]
        assert len(uids) == len(set(uids)), f"Duplicate UIDs found: {[u for u in uids if uids.count(u) > 1]}"

    def test_deterministic_output(self, indexer):
        """Indexing the same repo twice should produce the same graph."""
        result1 = indexer.index_repository(FIXTURES)
        result2 = indexer.index_repository(FIXTURES)

        assert len(result1.nodes) == len(result2.nodes)
        assert len(result1.edges) == len(result2.edges)

        uids1 = sorted(n.uid for n in result1.nodes)
        uids2 = sorted(n.uid for n in result2.nodes)
        assert uids1 == uids2

    def test_contains_edges_form_tree(self, repo_result):
        """Every structural node (Class, Function, Constructor, Interface) should have
        exactly one incoming CONTAINS edge. ReturnStatement and ConditionalBranch are
        linked via RETURNS and HAS_BRANCH edges instead."""
        structural_types = {NodeType.CLASS, NodeType.FUNCTION, NodeType.CONSTRUCTOR, NodeType.INTERFACE}
        structural_nodes = [n for n in repo_result.nodes if n.node_type in structural_types]
        contains_targets = [
            e.target_uid for e in repo_result.edges
            if e.edge_type == EdgeType.CONTAINS
        ]
        for node in structural_nodes:
            count = contains_targets.count(node.uid)
            assert count == 1, f"Node {node.uid} has {count} CONTAINS edges (expected 1)"


# ---------------------------------------------------------------------------
# Call resolution tests
# ---------------------------------------------------------------------------


class TestCallResolution:
    """Tests the name-based call resolution strategy."""

    def test_unique_method_calls_resolved(self, repo_result):
        """Methods with unique names should be resolved to their real UIDs."""
        calls = [
            e for e in repo_result.edges
            if e.edge_type == EdgeType.CALLS
        ]
        # calculateTotal is called from CheckoutService and should resolve
        # to ShoppingCart.calculateTotal
        calc_total_calls = [
            e for e in calls
            if "calculateTotal" in e.target_uid
            and not e.target_uid.startswith("unresolved:")
        ]
        assert len(calc_total_calls) >= 1

    def test_ambiguous_calls_stay_unresolved(self, repo_result):
        """Calls that match multiple methods should stay unresolved."""
        # External stdlib calls like getPrice, getQuantity should stay unresolved
        # if there's no unique match (or they're on an object reference)
        unresolved = [
            e for e in repo_result.edges
            if e.target_uid.startswith("unresolved:")
        ]
        assert len(unresolved) > 0  # some calls can't be resolved without type info


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_directory(self, indexer, tmp_path):
        """Indexing an empty directory should return no nodes/edges."""
        result = indexer.index_repository(tmp_path)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_nonexistent_directory_raises(self, indexer):
        """Indexing a nonexistent directory should raise ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            indexer.index_repository(Path("/nonexistent/repo"))

    def test_directory_with_no_java_files(self, indexer, tmp_path):
        """Indexing a directory with no Java files should return no nodes."""
        (tmp_path / "readme.md").write_text("# Hello")
        (tmp_path / "script.py").write_text("print('hello')")
        result = indexer.index_repository(tmp_path)
        assert len(result.nodes) == 0

    def test_skips_hidden_and_build_dirs(self, indexer, tmp_path):
        """Should skip .git, target, build directories."""
        # Create a Java file in a hidden dir — should be skipped
        hidden_dir = tmp_path / ".git" / "objects"
        hidden_dir.mkdir(parents=True)
        (hidden_dir / "Test.java").write_text("public class Test {}")

        # Create one in target/ — should be skipped
        target_dir = tmp_path / "target" / "classes"
        target_dir.mkdir(parents=True)
        (target_dir / "Test.java").write_text("public class Test {}")

        # Create one in src/ — should be indexed
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Main.java").write_text("public class Main {}")

        result = indexer.index_repository(tmp_path)
        files = [n for n in result.nodes if n.node_type == NodeType.FILE]
        assert len(files) == 1
        assert files[0].name == "Main.java"
