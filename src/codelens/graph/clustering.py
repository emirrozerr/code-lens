"""Domain clustering (Community Detection) using NetworkX and Louvain algorithm.

This module pulls the structural graph from Neo4j, runs a community detection algorithm
to find highly connected code clusters, and then uses an LLM (Gemini) to generate a
plain-English summary of what that business domain does.
"""

import logging
import networkx as nx
import community as community_louvain  # python-louvain

from typing import Dict, List, Any
from codelens.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class DomainClusterer:
    def __init__(self, api_key: str = None):
        # api_key kept for backwards compat but Groq is now the LLM backend
        self.api_key = api_key
        self._groq_client = None
        try:
            from codelens.settings import settings
            if settings.groq_api_key:
                from groq import Groq
                self._groq_client = Groq(api_key=settings.groq_api_key)
        except Exception:
            pass

    def run_clustering(self, repo_id: str = "default"):
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
            # Skip singleton clusters
            if len(members) < 2:
                continue
                
            cluster_id = f"Domain_{c_id}"

            # Prepare context for the LLM
            signatures = []
            for m in members:
                info = node_info.get(m, {})
                node_name = info.get("name", m)
                sig = info.get("signature", "")
                if sig:
                    signatures.append(f"- {node_name}: {sig}")
                else:
                    signatures.append(f"- {node_name}")

            context_text = "\n".join(signatures)

            logger.info(f"Naming and summarizing cluster {c_id} ({len(members)} nodes)...")
            domain_name, summary = self._generate_domain_name_and_summary(cluster_id, context_text)

            domains_data.append({
                "uid": cluster_id,
                "name": domain_name,
                "summary": summary,
                "members": members
            })
            
        logger.info("Saving domains to Neo4j...")
        self._save_domains_to_neo4j(domains_data, repo_id=repo_id)
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

    def _generate_domain_name_and_summary(self, domain_id: str, context: str) -> tuple[str, str]:
        """Call Groq to generate a short Turkish domain name and a summary.

        Returns (name, summary). Falls back to (domain_id, plain context) if no key.
        """
        if not self._groq_client:
            fallback_name = domain_id.replace("_", " ").title()
            fallback_summary = f"Members:\n{context[:300]}"
            return fallback_name, fallback_summary

        prompt = (
            "You are a software architect. Below are function and class signatures from a code cluster.\n\n"
            f"Signatures:\n{context}\n\n"
            "For this cluster:\n"
            "1. Generate a short, meaningful English name (2-4 words, e.g. 'Blog Management', 'User Authentication')\n"
            "2. Write a 1-2 sentence English description of what this cluster does\n\n"
            "Reply in exactly this format:\n"
            "NAME: <short name>\n"
            "SUMMARY: <1-2 sentence description>"
        )

        try:
            from codelens.settings import settings
            response = self._groq_client.chat.completions.create(
                model=settings.groq_model_quality,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )
            text = response.choices[0].message.content.strip()

            name, summary = domain_id, text
            for line in text.splitlines():
                if line.upper().startswith("NAME:"):
                    name = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SUMMARY:"):
                    summary = line.split(":", 1)[1].strip()
            return name, summary

        except Exception as exc:
            logger.error("Groq API error: %s", exc)
            return domain_id, f"Özet üretilemedi: {exc}"

    def _generate_domain_summary(self, domain_id: str, context: str) -> str:
        """Backwards-compat wrapper used by the regenerate API endpoint."""
        _, summary = self._generate_domain_name_and_summary(domain_id, context)
        return summary

    def _save_domains_to_neo4j(self, domains_data: List[Dict], repo_id: str = "default"):
        """Persist the Domain nodes and IN_DOMAIN edges to Neo4j."""
        client = Neo4jClient()
        try:
            with client.session() as session:
                # Clear only this repo's existing domains to avoid duplicates
                session.run(
                    "MATCH (d:Domain) WHERE coalesce(d.repo_id, 'default') = $rid DETACH DELETE d",
                    rid=repo_id,
                )

                for domain in domains_data:
                    session.run(
                        """
                        MERGE (d:Domain {uid: $uid})
                        SET d.name = $name, d.summary = $summary, d.repo_id = $repo_id
                        """,
                        uid=domain["uid"],
                        name=domain["name"],
                        summary=domain["summary"],
                        repo_id=repo_id,
                    )

                    session.run(
                        """
                        UNWIND $members AS member_uid
                        MATCH (n) WHERE n.uid = member_uid
                        MATCH (d:Domain {uid: $domain_uid})
                        MERGE (n)-[:IN_DOMAIN]->(d)
                        """,
                        members=domain["members"],
                        domain_uid=domain["uid"],
                    )
        finally:
            client.close()
