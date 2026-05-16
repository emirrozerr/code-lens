"""Integration tests for the FastMCP Server tools.

These tests require a running Neo4j database on localhost:7687 
with the Spring PetClinic test data ingested.
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


def test_search_nodes_finds_owner(check_db):
    """Test the native Lucene full-text search tool."""
    # This shouldn't be async since FastMCP wrapper runs it synchronously in tests
    result = search_nodes("OwnerRepository")
    
    assert "No nodes found" not in result
    assert "[Interface] OwnerRepository" in result
    assert "petclinic" in result


def test_search_nodes_not_found(check_db):
    """Test search with no matches."""
    result = search_nodes("NonExistentClassXYZ123")
    assert "No nodes found" in result


def test_get_code_context(check_db):
    """Test getting the multi-hop context for a specific function."""
    # OwnerController's processFindForm
    result = get_code_context("processFindForm")
    
    assert "Context for [Function] processFindForm" in result
    assert "Callers" in result
    assert "Callees" in result
    assert "Conditional Branches" in result
    
    # Check that we found its branches
    assert "if_statement" in result
    
    # Check that we found callees
    assert "findPaginatedForOwnersLastName" in result


def test_get_code_context_not_found(check_db):
    """Test context for a missing node."""
    result = get_code_context("NonExistentFunction")
    assert "not found in the graph" in result


def test_get_callers(check_db):
    """Test getting all callers for a symbol."""
    # We know processFindForm calls findPaginatedForOwnersLastName
    result = get_callers("findPaginatedForOwnersLastName")
    
    assert "Callers of 'findPaginatedForOwnersLastName':" in result
    assert "processFindForm" in result


def test_get_callees(check_db):
    """Test getting all callees of a symbol."""
    result = get_callees("processFindForm")
    
    assert "Symbols called by 'processFindForm':" in result
    assert "findPaginatedForOwnersLastName" in result
    assert "getLastName" in result
