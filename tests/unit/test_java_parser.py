"""Unit tests for the Java Tree-sitter parser."""

from pathlib import Path

import pytest

from codelens.indexer.java_parser import JavaParser
from codelens.indexer.models import EdgeType, NodeType

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"


@pytest.fixture
def parser():
    return JavaParser()


@pytest.fixture
def cart_result(parser):
    """Parse the ShoppingCart.java fixture."""
    filepath = FIXTURES / "src" / "com" / "example" / "shop" / "ShoppingCart.java"
    return parser.parse_file(filepath, FIXTURES)


@pytest.fixture
def item_result(parser):
    """Parse the CartItem.java fixture."""
    filepath = FIXTURES / "src" / "com" / "example" / "shop" / "CartItem.java"
    return parser.parse_file(filepath, FIXTURES)


@pytest.fixture
def checkout_result(parser):
    """Parse the CheckoutService.java fixture."""
    filepath = FIXTURES / "src" / "com" / "example" / "shop" / "CheckoutService.java"
    return parser.parse_file(filepath, FIXTURES)


# ---------------------------------------------------------------------------
# File node tests
# ---------------------------------------------------------------------------


class TestFileNode:
    def test_file_node_exists(self, cart_result):
        file_nodes = [n for n in cart_result.nodes if n.node_type == NodeType.FILE]
        assert len(file_nodes) == 1
        assert file_nodes[0].name == "ShoppingCart.java"

    def test_file_node_has_hash(self, cart_result):
        file_node = [n for n in cart_result.nodes if n.node_type == NodeType.FILE][0]
        assert file_node.file_hash is not None
        assert len(file_node.file_hash) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# Class extraction tests
# ---------------------------------------------------------------------------


class TestClassExtraction:
    def test_class_extracted(self, cart_result):
        classes = [n for n in cart_result.nodes if n.node_type == NodeType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "ShoppingCart"

    def test_class_has_qualified_name(self, cart_result):
        cls = [n for n in cart_result.nodes if n.node_type == NodeType.CLASS][0]
        assert "com.example.shop.ShoppingCart" == cls.qualified_name

    def test_class_has_docstring(self, cart_result):
        cls = [n for n in cart_result.nodes if n.node_type == NodeType.CLASS][0]
        assert cls.docstring is not None
        assert "shopping cart" in cls.docstring.lower()

    def test_class_contained_by_file(self, cart_result):
        contains = [
            e for e in cart_result.edges
            if e.edge_type == EdgeType.CONTAINS
            and "com.example.shop.ShoppingCart" in e.target_uid
            and e.source_uid.endswith(".java")  # file -> class only
        ]
        assert len(contains) == 1


# ---------------------------------------------------------------------------
# Method extraction tests
# ---------------------------------------------------------------------------


class TestMethodExtraction:
    def test_methods_extracted(self, cart_result):
        methods = [n for n in cart_result.nodes if n.node_type == NodeType.FUNCTION]
        method_names = {m.name for m in methods}
        assert "addItem" in method_names
        assert "removeItem" in method_names
        assert "calculateTotal" in method_names
        assert "applyBulkDiscount" in method_names
        assert "getTotalQuantity" in method_names

    def test_constructor_extracted(self, cart_result):
        ctors = [n for n in cart_result.nodes if n.node_type == NodeType.CONSTRUCTOR]
        assert len(ctors) == 1
        assert ctors[0].name == "ShoppingCart"

    def test_method_has_signature(self, cart_result):
        add_item = [
            n for n in cart_result.nodes
            if n.node_type == NodeType.FUNCTION and n.name == "addItem"
        ][0]
        assert add_item.signature is not None
        assert "CartItem item" in add_item.signature

    def test_method_has_docstring(self, cart_result):
        add_item = [
            n for n in cart_result.nodes
            if n.node_type == NodeType.FUNCTION and n.name == "addItem"
        ][0]
        assert add_item.docstring is not None

    def test_method_has_line_numbers(self, cart_result):
        add_item = [
            n for n in cart_result.nodes
            if n.node_type == NodeType.FUNCTION and n.name == "addItem"
        ][0]
        assert add_item.start_line > 0
        assert add_item.end_line >= add_item.start_line


# ---------------------------------------------------------------------------
# Edge extraction tests
# ---------------------------------------------------------------------------


class TestEdgeExtraction:
    def test_import_edges(self, cart_result):
        imports = [e for e in cart_result.edges if e.edge_type == EdgeType.IMPORTS]
        import_targets = {e.target_uid for e in imports}
        assert any("java.util.List" in t for t in import_targets)
        assert any("java.util.ArrayList" in t for t in import_targets)

    def test_method_call_edges(self, cart_result):
        calls = [e for e in cart_result.edges if e.edge_type == EdgeType.CALLS]
        assert len(calls) > 0

    def test_contains_edges(self, cart_result):
        contains = [e for e in cart_result.edges if e.edge_type == EdgeType.CONTAINS]
        assert len(contains) > 5  # file->class, class->methods, class->constructor


# ---------------------------------------------------------------------------
# Conditional branch tests
# ---------------------------------------------------------------------------


class TestConditionalBranches:
    def test_if_branches_extracted(self, cart_result):
        branches = [n for n in cart_result.nodes if n.node_type == NodeType.CONDITIONAL_BRANCH]
        # calculateTotal has an if, applyBulkDiscount has if/else-if/else-if
        assert len(branches) >= 2

    def test_branch_has_condition_text(self, cart_result):
        branches = [n for n in cart_result.nodes if n.node_type == NodeType.CONDITIONAL_BRANCH]
        has_condition = [b for b in branches if b.docstring and "Condition:" in b.docstring]
        assert len(has_condition) > 0


# ---------------------------------------------------------------------------
# Cross-file call tests (CheckoutService -> ShoppingCart)
# ---------------------------------------------------------------------------


class TestCrossFileCalls:
    def test_checkout_calls_cart_methods(self, checkout_result):
        calls = [e for e in checkout_result.edges if e.edge_type == EdgeType.CALLS]
        call_targets = {e.target_uid for e in calls}
        # Calls go through object reference: cart.applyBulkDiscount() -> "unresolved:cart.applyBulkDiscount"
        assert any("applyBulkDiscount" in t for t in call_targets)
        assert any("calculateTotal" in t for t in call_targets)


# ---------------------------------------------------------------------------
# CartItem tests (simple POJO)
# ---------------------------------------------------------------------------


class TestCartItem:
    def test_all_getters_extracted(self, item_result):
        methods = [n for n in item_result.nodes if n.node_type == NodeType.FUNCTION]
        method_names = {m.name for m in methods}
        assert "getProductId" in method_names
        assert "getName" in method_names
        assert "getPrice" in method_names
        assert "getQuantity" in method_names
        assert "setQuantity" in method_names
        assert "toString" in method_names

    def test_constructor_with_params(self, item_result):
        ctors = [n for n in item_result.nodes if n.node_type == NodeType.CONSTRUCTOR]
        assert len(ctors) == 1
        assert "String productId" in ctors[0].signature


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_nonexistent_file_raises(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent.java"), Path("/"))
