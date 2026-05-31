"""Integration tests for the FastMCP Server tools.

These tests require a running Neo4j database on localhost:7687 
with the sample-java-repo test data ingested.
"""

import pytest
from neo4j.exceptions import ServiceUnavailable

from codelens.graph.neo4j_client import Neo4jClient
from codelens.mcp_server.server import search_nodes, get_code_context, get_callers, get_callees, get_domains, get_domain, get_domain_content


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


def test_get_domains_and_domain_content(check_db):
    """Test the get_domains and get_domain_content MCP tools."""
    client = Neo4jClient()
    try:
        with client.session() as session:
            session.run("MATCH (d:Domain) DETACH DELETE d")

            # Empty state
            res_empty = get_domains()
            assert "No domains found. Run clustering first." in res_empty

            # Missing domain
            res_missing = get_domain_content("NonExistentDomain")
            assert "Domain 'NonExistentDomain' not found" in res_missing

            # Create a mock Domain and link a node to it
            session.run("""
                CREATE (d:Domain {name: 'Test Domain', summary: 'A mock domain for testing'})
                WITH d
                MATCH (n:Class {name: 'CheckoutService'})
                CREATE (n)-[:IN_DOMAIN]->(d)
            """)

            # get_domains lists it
            res_list = get_domains()
            assert "Test Domain" in res_list
            assert "A mock domain for testing" in res_list

            # get_domain_content returns members by domain name
            res_content = get_domain_content("Test Domain")
            assert "=== Test Domain ===" in res_content
            assert "CheckoutService" in res_content
    finally:
        with client.session() as session:
            session.run("MATCH (d:Domain) DETACH DELETE d")
        client.close()


def test_get_domain_by_symbol(check_db):
    """Test get_domain — finds the domain a symbol belongs to."""
    client = Neo4jClient()
    try:
        with client.session() as session:
            session.run("MATCH (d:Domain) DETACH DELETE d")

            # No domain assigned yet
            res_none = get_domain("CheckoutService")
            assert "No domain found" in res_none

            # Assign CheckoutService to a domain
            session.run("""
                CREATE (d:Domain {name: 'Commerce Domain', summary: 'Handles checkout and cart logic'})
                WITH d
                MATCH (n:Class {name: 'CheckoutService'})
                CREATE (n)-[:IN_DOMAIN]->(d)
            """)

            # Now get_domain by symbol name finds it
            res = get_domain("CheckoutService")
            assert "=== Commerce Domain ===" in res
            assert "Handles checkout and cart logic" in res
    finally:
        with client.session() as session:
            session.run("MATCH (d:Domain) DETACH DELETE d")
        client.close()

