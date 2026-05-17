"""Unit and integration tests for DomainClusterer community detection."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from codelens.graph.clustering import DomainClusterer
from codelens.graph.neo4j_client import Neo4jClient
from codelens.indexer.indexer import Indexer

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sample-java-repo"


@pytest.fixture(scope="module")
def setup_db():
    """Ingest sample repo data into Neo4j for clustering tests."""
    indexer = Indexer()
    result = indexer.index_repository(FIXTURES)
    
    client = Neo4jClient()
    try:
        client.clear_database()
        client.setup_schema()
        client.ingest_parse_result(result)
    finally:
        client.close()


def test_domain_clusterer_empty_graph():
    # Test clustering when graph is empty
    with patch("codelens.graph.clustering.DomainClusterer._extract_graph_from_neo4j") as mock_extract:
        import networkx as nx
        mock_extract.return_value = (nx.DiGraph(), {})
        
        clusterer = DomainClusterer()
        result = clusterer.run_clustering()
        assert result is None


def test_domain_clusterer_pipeline(setup_db):
    clusterer = DomainClusterer()
    
    # 1. Run clustering with the fallback/mock LLM generator
    domains = clusterer.run_clustering()
    
    assert domains is not None
    assert len(domains) > 0
    
    for d in domains:
        assert "uid" in d
        assert "name" in d
        assert "summary" in d
        assert "members" in d
        assert "Mock summary for Domain_" in d["summary"]

    # Verify that Domain nodes actually exist in Neo4j
    client = Neo4jClient()
    try:
        with client.session() as session:
            res = session.run("MATCH (d:Domain) RETURN d.uid AS uid, d.name AS name, d.summary AS summary")
            saved_domains = [record.data() for record in res]
            assert len(saved_domains) == len(domains)
            
            # Check relationships exist
            rel_res = session.run("MATCH (n)-[:IN_DOMAIN]->(d:Domain) RETURN count(n) AS count")
            assert rel_res.single()["count"] > 0
    finally:
        client.close()


def test_domain_clusterer_llm_api_call():
    # Test the real model.generate_content API call path via Mock
    with patch("google.genai.Client") as MockClient:
        mock_genai_instance = MagicMock()
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a summarized domain for orders."
        
        mock_model_instance.generate_content.return_value = mock_response
        mock_genai_instance.models = mock_model_instance
        MockClient.return_value = mock_genai_instance
        
        clusterer = DomainClusterer(api_key="fake-api-key")
        summary = clusterer._generate_domain_summary("Domain_1", "CheckoutService\nCartItem")
        
        assert summary == "This is a summarized domain for orders."
        mock_model_instance.generate_content.assert_called_once()
        
        # Test API exception handling
        mock_model_instance.generate_content.side_effect = Exception("Quota exceeded")
        err_summary = clusterer._generate_domain_summary("Domain_1", "CheckoutService\nCartItem")
        assert "Error generating summary" in err_summary
