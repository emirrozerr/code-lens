"""Integration tests for the FastMCP Server tools.

These tests require a running Neo4j database on localhost:7687 
with the sample-java-repo test data ingested.
"""

import pytest
from neo4j.exceptions import ServiceUnavailable

from codelens.graph.neo4j_client import Neo4jClient
from codelens.mcp_server.server import search_nodes, get_code_context, get_callers, get_callees, get_domains, get_domain


@pytest.fixture(scope="module")
def check_db():
    """Ingest the sample-java-repo to ensure Neo4j has correct test data."""
    from pathlib import Path
    from codelens.indexer.indexer import Indexer
    
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"
    indexer = Indexer()
    result = indexer.index_repository(fixtures_dir)
    
    client = Neo4jClient()
    try:
        # Check connection first
        with client.session() as s:
            s.run("RETURN 1")
        
        # Clear and ingest test dataset
        client.clear_database()
        client.setup_schema()
        client.ingest_parse_result(result)
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


def test_get_domains_and_domain(check_db):
    """Test the get_domains and get_domain MCP tools."""
    # 1. Clean/prepare mock domain
    client = Neo4jClient()
    try:
        with client.session() as session:
            # Clean existing domains
            session.run("MATCH (d:Domain) DETACH DELETE d")
            
            # Check empty domains message
            res_empty = get_domains()
            assert "No domains found. Run clustering first." in res_empty
            
            # Test getting non-existent domain
            res_missing = get_domain("NonExistentDomain")
            assert "Domain 'NonExistentDomain' not found" in res_missing
            
            # Create a mock Domain and link a node to it
            session.run("""
                CREATE (d:Domain {name: 'Test Domain', summary: 'A mock domain for testing'})
                WITH d
                MATCH (n:Class {name: 'CheckoutService'})
                CREATE (n)-[:IN_DOMAIN]->(d)
            """)
            
            # Test get_domains returns it
            res_list = get_domains()
            assert "Test Domain" in res_list
            assert "A mock domain for testing" in res_list
            
            # Test get_domain returns members
            res_single = get_domain("Test Domain")
            assert "=== Test Domain ===" in res_single
            assert "CheckoutService" in res_single
    finally:
        # Clean up domains so we don't pollute subsequent queries
        with client.session() as session:
            session.run("MATCH (d:Domain) DETACH DELETE d")
        client.close()

