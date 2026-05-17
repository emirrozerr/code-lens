"""Unit tests for the Python Tree-sitter parser."""

from pathlib import Path
import textwrap

import pytest

from codelens.indexer.python_parser import PythonParser
from codelens.indexer.models import EdgeType, NodeType


@pytest.fixture
def parser():
    return PythonParser()


def _parse_source(parser, source: str, filename: str = "test.py"):
    """Helper: write source to a temp file and parse it."""
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        filepath = tmpdir / filename
        filepath.write_text(textwrap.dedent(source))
        return parser.parse_file(filepath, tmpdir)


# ---------------------------------------------------------------------------
# File node tests
# ---------------------------------------------------------------------------


class TestFileNode:
    def test_file_node_exists(self, parser):
        result = _parse_source(parser, "x = 1\n")
        file_nodes = [n for n in result.nodes if n.node_type == NodeType.FILE]
        assert len(file_nodes) == 1
        assert file_nodes[0].name == "test.py"

    def test_file_node_has_hash(self, parser):
        result = _parse_source(parser, "x = 1\n")
        file_node = [n for n in result.nodes if n.node_type == NodeType.FILE][0]
        assert file_node.file_hash is not None
        assert len(file_node.file_hash) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# Class extraction tests
# ---------------------------------------------------------------------------


class TestClassExtraction:
    def test_class_extracted(self, parser):
        result = _parse_source(parser, '''
            class MyService:
                """A service class."""
                pass
        ''')
        classes = [n for n in result.nodes if n.node_type == NodeType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "MyService"

    def test_class_has_docstring(self, parser):
        result = _parse_source(parser, '''
            class MyService:
                """A service class."""
                pass
        ''')
        cls = [n for n in result.nodes if n.node_type == NodeType.CLASS][0]
        assert cls.docstring is not None
        assert "service" in cls.docstring.lower()

    def test_class_contained_by_file(self, parser):
        result = _parse_source(parser, '''
            class MyService:
                pass
        ''')
        contains = [
            e for e in result.edges
            if e.edge_type == EdgeType.CONTAINS
            and "MyService" in e.target_uid
            and e.source_uid.endswith(".py")
        ]
        assert len(contains) == 1

    def test_class_inheritance_extends(self, parser):
        result = _parse_source(parser, '''
            class Dog(Animal):
                pass
        ''')
        extends = [e for e in result.edges if e.edge_type == EdgeType.EXTENDS]
        assert len(extends) == 1
        assert "Animal" in extends[0].target_uid

    def test_class_multiple_inheritance(self, parser):
        result = _parse_source(parser, '''
            class Hybrid(Base, Mixin):
                pass
        ''')
        extends = [e for e in result.edges if e.edge_type == EdgeType.EXTENDS]
        assert len(extends) == 2
        targets = {e.target_uid for e in extends}
        assert any("Base" in t for t in targets)
        assert any("Mixin" in t for t in targets)

    def test_inner_class(self, parser):
        result = _parse_source(parser, '''
            class Outer:
                class Inner:
                    pass
        ''')
        classes = [n for n in result.nodes if n.node_type == NodeType.CLASS]
        assert len(classes) == 2
        class_names = {c.name for c in classes}
        assert class_names == {"Outer", "Inner"}


# ---------------------------------------------------------------------------
# Function extraction tests
# ---------------------------------------------------------------------------


class TestFunctionExtraction:
    def test_top_level_function(self, parser):
        result = _parse_source(parser, '''
            def greet(name):
                """Say hello."""
                return f"Hello, {name}"
        ''')
        funcs = [n for n in result.nodes if n.node_type == NodeType.FUNCTION]
        assert len(funcs) == 1
        assert funcs[0].name == "greet"

    def test_function_has_signature(self, parser):
        result = _parse_source(parser, '''
            def greet(name: str, age: int = 0):
                pass
        ''')
        func = [n for n in result.nodes if n.node_type == NodeType.FUNCTION][0]
        assert func.signature is not None
        assert "name" in func.signature
        assert "age" in func.signature

    def test_function_has_docstring(self, parser):
        result = _parse_source(parser, '''
            def greet(name):
                """Say hello to someone."""
                pass
        ''')
        func = [n for n in result.nodes if n.node_type == NodeType.FUNCTION][0]
        assert func.docstring is not None
        assert "hello" in func.docstring.lower()

    def test_function_has_line_numbers(self, parser):
        result = _parse_source(parser, '''
            def greet(name):
                pass
        ''')
        func = [n for n in result.nodes if n.node_type == NodeType.FUNCTION][0]
        assert func.start_line > 0
        assert func.end_line >= func.start_line

    def test_class_methods(self, parser):
        result = _parse_source(parser, '''
            class Foo:
                def bar(self):
                    pass
                def baz(self, x):
                    pass
        ''')
        funcs = [n for n in result.nodes if n.node_type == NodeType.FUNCTION]
        func_names = {f.name for f in funcs}
        assert func_names == {"bar", "baz"}

    def test_init_is_constructor(self, parser):
        result = _parse_source(parser, '''
            class Foo:
                def __init__(self):
                    pass
        ''')
        ctors = [n for n in result.nodes if n.node_type == NodeType.CONSTRUCTOR]
        assert len(ctors) == 1
        assert ctors[0].name == "__init__"


# ---------------------------------------------------------------------------
# Edge extraction tests
# ---------------------------------------------------------------------------


class TestEdgeExtraction:
    def test_import_edges(self, parser):
        result = _parse_source(parser, '''
            import os
            import sys
        ''')
        imports = [e for e in result.edges if e.edge_type == EdgeType.IMPORTS]
        targets = {e.target_uid for e in imports}
        assert any("os" in t for t in targets)
        assert any("sys" in t for t in targets)

    def test_from_import_edges(self, parser):
        result = _parse_source(parser, '''
            from pathlib import Path
        ''')
        imports = [e for e in result.edges if e.edge_type == EdgeType.IMPORTS]
        assert len(imports) >= 1
        assert any("pathlib" in e.target_uid for e in imports)

    def test_method_call_edges(self, parser):
        result = _parse_source(parser, '''
            def foo():
                bar()
                obj.baz()
        ''')
        calls = [e for e in result.edges if e.edge_type == EdgeType.CALLS]
        call_targets = {e.target_uid for e in calls}
        assert any("bar" in t for t in call_targets)
        assert any("obj.baz" in t for t in call_targets)

    def test_contains_edges(self, parser):
        result = _parse_source(parser, '''
            class Foo:
                def bar(self):
                    pass
        ''')
        contains = [e for e in result.edges if e.edge_type == EdgeType.CONTAINS]
        # file -> class, class -> method
        assert len(contains) >= 2


# ---------------------------------------------------------------------------
# Conditional branch tests
# ---------------------------------------------------------------------------


class TestConditionalBranches:
    def test_if_branches_extracted(self, parser):
        result = _parse_source(parser, '''
            def foo(x):
                if x > 0:
                    return 1
                else:
                    return 0
        ''')
        branches = [n for n in result.nodes if n.node_type == NodeType.CONDITIONAL_BRANCH]
        assert len(branches) >= 1

    def test_for_loop_extracted(self, parser):
        result = _parse_source(parser, '''
            def process(items):
                for item in items:
                    print(item)
        ''')
        branches = [n for n in result.nodes if n.node_type == NodeType.CONDITIONAL_BRANCH]
        assert len(branches) >= 1
        assert any("for_statement" in b.name for b in branches)


# ---------------------------------------------------------------------------
# Return statement tests
# ---------------------------------------------------------------------------


class TestReturnStatements:
    def test_return_extracted(self, parser):
        result = _parse_source(parser, '''
            def add(a, b):
                return a + b
        ''')
        returns = [n for n in result.nodes if n.node_type == NodeType.RETURN_STATEMENT]
        assert len(returns) == 1

    def test_return_edges(self, parser):
        result = _parse_source(parser, '''
            def add(a, b):
                return a + b
        ''')
        ret_edges = [e for e in result.edges if e.edge_type == EdgeType.RETURNS]
        assert len(ret_edges) == 1


# ---------------------------------------------------------------------------
# No-duplicate / deterministic tests
# ---------------------------------------------------------------------------


class TestGraphIntegrity:
    def test_no_duplicate_nodes(self, parser):
        result = _parse_source(parser, '''
            class Svc:
                def run(self):
                    pass
                def stop(self):
                    pass
        ''')
        uids = [n.uid for n in result.nodes]
        assert len(uids) == len(set(uids)), f"Duplicate UIDs: {[u for u in uids if uids.count(u) > 1]}"

    def test_deterministic_output(self, parser):
        source = '''
            class Svc:
                def run(self):
                    pass
        '''
        r1 = _parse_source(parser, source)
        r2 = _parse_source(parser, source)
        assert len(r1.nodes) == len(r2.nodes)
        assert len(r1.edges) == len(r2.edges)
        assert sorted(n.uid for n in r1.nodes) == sorted(n.uid for n in r2.nodes)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_nonexistent_file_raises(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent.py"), Path("/"))

    def test_syntax_error_file_still_parses(self, parser):
        """Tree-sitter should produce a partial parse even with syntax errors."""
        result = _parse_source(parser, '''
            def broken(:
                pass
        ''')
        # Should not crash, and should report an error
        assert len(result.errors) > 0 or len(result.nodes) >= 1
