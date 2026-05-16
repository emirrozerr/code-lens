"""Integration tests for the Neo4j client.

These tests require a running Neo4j database on localhost:7687.
They will be skipped if Neo4j is not reachable.
"""

import pytest
from neo4j.exceptions import ServiceUnavailable

from codelens.graph.neo4j_client import Neo4jClient
from codelens.indexer.models import CodeNode, CodeEdge, NodeType, EdgeType, ParseResult


@pytest.fixture(scope="module")
def neo4j_client():
    """Provides a Neo4jClient, skipping tests if DB is offline."""
    client = Neo4jClient()
    try:
        # Test connection
        with client.session() as session:
            session.run("RETURN 1")
    except ServiceUnavailable:
        pytest.skip("Neo4j is not running on localhost:7687")
        return

    yield client
    client.close()


@pytest.fixture(autouse=True)
def clean_db(neo4j_client):
    """Clear the database before each test."""
    neo4j_client.clear_database()
    neo4j_client.setup_schema()


def test_schema_setup(neo4j_client):
    """Test that unique constraints are created successfully."""
    # Run setup again (should be idempotent)
    neo4j_client.setup_schema()

    with neo4j_client.session() as session:
        result = session.run("SHOW CONSTRAINTS")
        constraints = [record["name"] for record in result]
        
    assert "unique_uid_class" in constraints
    assert "unique_uid_function" in constraints


def test_ingest_nodes(neo4j_client):
    """Test inserting a set of nodes."""
    node1 = CodeNode(uid="file1", name="Main.java", qualified_name="Main.java", node_type=NodeType.FILE, filepath="Main.java", start_line=1, end_line=10)
    node2 = CodeNode(uid="class1", name="Main", qualified_name="Main", node_type=NodeType.CLASS, filepath="Main.java", start_line=1, end_line=10)
    
    result = ParseResult(filepath=".", nodes=[node1, node2], edges=[], errors=[])
    neo4j_client.ingest_parse_result(result)

    with neo4j_client.session() as session:
        res = session.run("MATCH (n) RETURN count(n) as count")
        assert res.single()["count"] == 2
        
        # Verify properties
        res = session.run("MATCH (n:Class {uid: 'class1'}) RETURN n.name as name")
        assert res.single()["name"] == "Main"


def test_ingest_edges(neo4j_client):
    """Test inserting edges between nodes."""
    node1 = CodeNode(uid="func1", name="caller", qualified_name="caller", node_type=NodeType.FUNCTION, filepath="test", start_line=1, end_line=5)
    node2 = CodeNode(uid="func2", name="callee", qualified_name="callee", node_type=NodeType.FUNCTION, filepath="test", start_line=6, end_line=10)
    edge = CodeEdge(source_uid="func1", target_uid="func2", edge_type=EdgeType.CALLS, filepath="test")

    result = ParseResult(filepath=".", nodes=[node1, node2], edges=[edge], errors=[])
    neo4j_client.ingest_parse_result(result)

    with neo4j_client.session() as session:
        res = session.run("MATCH (a)-[r:calls]->(b) RETURN a.uid as src, b.uid as tgt")
        record = res.single()
        assert record["src"] == "func1"
        assert record["tgt"] == "func2"


def test_unresolved_targets(neo4j_client):
    """Test that edges pointing to unknown nodes create an Unresolved node."""
    node1 = CodeNode(uid="func1", name="caller", qualified_name="caller", node_type=NodeType.FUNCTION, filepath="test", start_line=1, end_line=5)
    # Missing target node!
    edge = CodeEdge(source_uid="func1", target_uid="unresolved:missing", edge_type=EdgeType.CALLS, filepath="test")

    result = ParseResult(filepath=".", nodes=[node1], edges=[edge], errors=[])
    neo4j_client.ingest_parse_result(result)

    with neo4j_client.session() as session:
        # Check that Unresolved node was created
        res = session.run("MATCH (n:Unresolved) RETURN n.uid as uid")
        assert res.single()["uid"] == "unresolved:missing"


def test_delete_file_subgraph(neo4j_client):
    """Test deleting all nodes belonging to a specific file."""
    node_keep = CodeNode(uid="keep", name="keep", qualified_name="keep", node_type=NodeType.FILE, filepath="keep.java", start_line=1, end_line=5)
    node_del = CodeNode(uid="del", name="del", qualified_name="del", node_type=NodeType.FILE, filepath="del.java", start_line=1, end_line=5)
    
    result = ParseResult(filepath=".", nodes=[node_keep, node_del], edges=[], errors=[])
    neo4j_client.ingest_parse_result(result)
    
    neo4j_client.delete_file_subgraph("del.java")
    
    with neo4j_client.session() as session:
        res = session.run("MATCH (n) RETURN n.filepath as path")
        paths = [r["path"] for r in res]
        assert "keep.java" in paths
        assert "del.java" not in paths
