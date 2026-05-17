"""Integration tests for the FastMCP Server tools.

These tests require a running Neo4j database on localhost:7687 
with the sample-java-repo test data ingested.
"""

import pytest
from neo4j.exceptions import ServiceUnavailable

from codelens.graph.neo4j_client import Neo4jClient
from codelens.mcp_server.server import search_nodes, get_code_context, get_callers, get_callees


@pytest.fixture(scope="module")
def check_db():
    """Skip tests if Neo4j is offline or empty."""
    client = Neo4jClient()
    try:
        with client.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            if result.single()["count"] == 0:
                pytest.skip("Neo4j database is empty. Run 'codelens ingest' first.")
    except ServiceUnavailable:
        pytest.skip("Neo4j is not running on localhost:7687")
    finally:
        client.close()


def test_search_nodes_finds_checkout(check_db):
    """Test the native Lucene full-text search tool."""
    # This shouldn't be async since FastMCP wrapper runs it synchronously in tests
    result = search_nodes("CheckoutService")
    
    assert "No nodes found" not in result
    assert "[Class] CheckoutService" in result
    assert "CheckoutService.java" in result


def test_search_nodes_not_found(check_db):
    """Test search with no matches."""
    result = search_nodes("NonExistentClassXYZ123")
    assert "No nodes found" in result


def test_get_code_context(check_db):
    """Test getting the multi-hop context for a specific function."""
    result = get_code_context("calculateTotal")
    
    assert "Context for [Function] calculateTotal" in result
    assert "Callers" in result
    assert "Callees" in result
    assert "Conditional Branches" in result
    
    # Check that we found its branches
    assert "for_statement" in result or "if_statement" in result
    
    # Check that we found callees
    assert "getPrice" in result


def test_get_code_context_not_found(check_db):
    """Test context for a missing node."""
    result = get_code_context("NonExistentFunction")
    assert "not found in the graph" in result


def test_get_callers(check_db):
    """Test getting all callers for a symbol."""
    # We know CheckoutService.checkout calls calculateTotal
    result = get_callers("calculateTotal")
    
    assert "Callers of 'calculateTotal':" in result
    assert "checkout" in result


def test_get_callees(check_db):
    """Test getting all callees of a symbol."""
    result = get_callees("calculateTotal")
    
    assert "Symbols called by 'calculateTotal':" in result
    assert "getPrice" in result
    assert "getQuantity" in result
