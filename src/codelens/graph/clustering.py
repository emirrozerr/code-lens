"""Domain clustering (Community Detection) using NetworkX and Louvain algorithm.

This module pulls the structural graph from Neo4j, runs a community detection algorithm
to find highly connected code clusters, and then uses an LLM (Gemini) to generate a
plain-English summary of what that business domain does.
"""

import logging
import networkx as nx
import community as community_louvain # python-louvain

from typing import Dict, List, Any
from codelens.graph.neo4j_client import Neo4jClient
from google import genai

logger = logging.getLogger(__name__)


class DomainClusterer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # We initialize the Gemini client if an API key is provided
        self.client = genai.Client(api_key=api_key) if api_key else None

    def run_clustering(self):
        """Main pipeline for clustering the Neo4j graph into domains."""
        logger.info("Extracting structural graph from Neo4j...")
        G, node_info = self._extract_graph_from_neo4j()
        
        if len(G.nodes) == 0:
            logger.warning("No nodes found in graph to cluster.")
            return

        logger.info(f"Running community detection on {len(G.nodes)} nodes and {len(G.edges)} edges...")
        # community_louvain.best_partition returns a dict: {node_id: community_id}
        partition = community_louvain.best_partition(G.to_undirected())
        
        # Group nodes by their assigned community ID
        clusters: Dict[int, List[str]] = {}
        for node_uid, community_id in partition.items():
            clusters.setdefault(community_id, []).append(node_uid)
            
        logger.info(f"Discovered {len(clusters)} distinct business domains.")
        
        domains_data = []
        for c_id, members in clusters.items():
            # Skip tiny clusters (e.g., just 1-2 unconnected functions)
            if len(members) < 3:
                continue
                
            domain_name = f"Domain_{c_id}"
            
            # Prepare context for the LLM
            signatures = []
            for m in members:
                info = node_info.get(m, {})
                name = info.get("name", m)
                sig = info.get("signature", "")
                if sig:
                    signatures.append(f"- {name}: {sig}")
                else:
                    signatures.append(f"- {name}")
            
            context_text = "\n".join(signatures)
            
            logger.info(f"Summarizing {domain_name} ({len(members)} nodes)...")
            summary = self._generate_domain_summary(domain_name, context_text)
            
            domains_data.append({
                "uid": domain_name,
                "name": f"Domain {c_id}",
                "summary": summary,
                "members": members
            })
            
        logger.info("Saving domains to Neo4j...")
        self._save_domains_to_neo4j(domains_data)
        logger.info("Clustering complete!")
        return domains_data

    def _extract_graph_from_neo4j(self) -> tuple[nx.DiGraph, Dict[str, Any]]:
        """Query Neo4j and build a local NetworkX graph for community detection."""
        G = nx.DiGraph()
        node_info = {}
        
        client = Neo4jClient()
        try:
            with client.session() as session:
                # 1. Fetch all structural nodes
                nodes_query = """
                MATCH (n) 
                WHERE n:Class OR n:Function OR n:Interface 
                RETURN n.uid AS uid, n.name AS name, n.signature AS signature
                """
                for record in session.run(nodes_query):
                    uid = record["uid"]
                    G.add_node(uid)
                    node_info[uid] = {
                        "name": record["name"],
                        "signature": record["signature"]
                    }
                    
                # 2. Fetch structural edges (calls, contains, implements, extends)
                edges_query = """
                MATCH (a)-[r:calls|contains|implements|extends]->(b)
                WHERE (a:Class OR a:Function OR a:Interface) 
                  AND (b:Class OR b:Function OR b:Interface)
                RETURN a.uid AS source, b.uid AS target
                """
                for record in session.run(edges_query):
                    # We only add edges where both nodes are in our graph
                    if G.has_node(record["source"]) and G.has_node(record["target"]):
                        G.add_edge(record["source"], record["target"])
                        
        finally:
            client.close()
            
        return G, node_info

    def _generate_domain_summary(self, domain_id: str, context: str) -> str:
        """Call the LLM to generate a plain English summary of the domain."""
        if not self.client:
            # Fallback if no API key is provided
            return f"Mock summary for {domain_id}. (Set Gemini API key to generate real summaries). Contains:\n{context[:100]}..."
            
        prompt = f"""
        You are an expert software architect analyzing a codebase.
        I used community detection algorithms to group related code functions and classes into a cluster.
        Based on the following list of signatures from this cluster, write a brief, 1-2 sentence 
        plain-English summary explaining what business logic or system domain this cluster handles.
        
        Signatures:
        {context}
        
        Provide only the summary. No introductory text.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            return f"Error generating summary: {e}"

    def _save_domains_to_neo4j(self, domains_data: List[Dict]):
        """Persist the Domain nodes and IN_DOMAIN edges to Neo4j."""
        client = Neo4jClient()
        try:
            with client.session() as session:
                # Clear existing domains so we don't duplicate
                session.run("MATCH (d:Domain) DETACH DELETE d")
                
                for domain in domains_data:
                    # Create the Domain node
                    session.run("""
                        MERGE (d:Domain {uid: $uid})
                        SET d.name = $name, d.summary = $summary
                    """, uid=domain["uid"], name=domain["name"], summary=domain["summary"])
                    
                    # Create the IN_DOMAIN edges for all members
                    session.run("""
                        UNWIND $members AS member_uid
                        MATCH (n) WHERE n.uid = member_uid
                        MATCH (d:Domain {uid: $domain_uid})
                        MERGE (n)-[:IN_DOMAIN]->(d)
                    """, members=domain["members"], domain_uid=domain["uid"])
        finally:
            client.close()
