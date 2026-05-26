"""Neo4j client for managing the graph schema and ingesting data."""

import logging
from contextlib import contextmanager

from neo4j import GraphDatabase, Session

from codelens.indexer.models import CodeNode, CodeEdge, NodeType, ParseResult
from codelens.settings import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Manages connections, schema constraints, and data ingestion into Neo4j."""

    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self.uri = uri or settings.neo4j_uri
        self.username = username or settings.neo4j_username
        self.password = password or settings.neo4j_password
        self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def close(self):
        """Close the underlying Neo4j driver."""
        self._driver.close()

    @contextmanager
    def session(self) -> Session:
        """Yield a Neo4j session."""
        with self._driver.session() as session:
            yield session

    # ---------------------------------------------------------------------------
    # Schema Management
    # ---------------------------------------------------------------------------

    def setup_schema(self):
        """Create necessary indexes and constraints in Neo4j."""
        logger.info("Setting up Neo4j schema constraints...")
        
        # We want a unique constraint on 'uid' for every node type we insert.
        # Neo4j constraints must be applied per-label.
        labels = [t.value for t in NodeType]
        # 'Unresolved' label is used as a fallback for targets that aren't fully known yet
        labels.append("Unresolved")

        with self.session() as session:
            for label in labels:
                constraint_name = f"unique_uid_{label.lower()}"
                
                # Check if constraint exists, create if not
                query = f"""
                CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                FOR (n:{label}) REQUIRE n.uid IS UNIQUE
                """
                try:
                    session.run(query)
                except Exception as e:
                    logger.warning(f"Could not create constraint for {label}: {e}")

        logger.info("Schema setup complete.")

    def clear_database(self):
        """DANGEROUS: Deletes all nodes and relationships from the database."""
        logger.warning("Clearing entire Neo4j database!")
        with self.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    # ---------------------------------------------------------------------------
    # Ingestion
    # ---------------------------------------------------------------------------

    def ingest_parse_result(self, result: ParseResult):
        """Ingest a complete ParseResult (nodes and edges) into Neo4j."""
        if not result.nodes and not result.edges:
            return

        with self.session() as session:
            # 1. Upsert Nodes
            logger.info(f"Ingesting {len(result.nodes)} nodes...")
            self._ingest_nodes(session, result.nodes)

            # 2. Upsert Edges
            logger.info(f"Ingesting {len(result.edges)} edges...")
            self._ingest_edges(session, result.edges)

            # 3. Clean up orphans (e.g. Unresolved nodes that never got edges)
            session.run("MATCH (n:Unresolved) WHERE NOT (n)--() DELETE n")

    def _ingest_nodes(self, session: Session, nodes: list[CodeNode]):
        """Upsert nodes in batches."""
        # We group nodes by label because Cypher's MERGE requires static labels
        grouped_nodes = {}
        for node in nodes:
            grouped_nodes.setdefault(node.node_type.value, []).append(node)

        for label, node_group in grouped_nodes.items():
            query = f"""
            UNWIND $batch AS data
            MERGE (n:{label} {{uid: data.uid}})
            SET n.name = data.name,
                n.qualified_name = data.qualified_name,
                n.filepath = data.filepath,
                n.start_line = data.start_line,
                n.end_line = data.end_line,
                n.docstring = data.docstring,
                n.signature = data.signature,
                n.file_hash = data.file_hash
            """
            # Convert models to dicts for Neo4j parameters
            batch = [n.model_dump(exclude_none=True) for n in node_group]
            session.run(query, batch=batch)

    def _ingest_edges(self, session: Session, edges: list[CodeEdge]):
        """Upsert edges in batches."""
        grouped_edges = {}
        for edge in edges:
            grouped_edges.setdefault(edge.edge_type.value, []).append(edge)

        for rel_type, edge_group in grouped_edges.items():
            # For target nodes that don't exist yet (especially 'unresolved:' targets),
            # we MERGE them with a fallback label. 
            # We don't know the exact label of the target, so we just use the UID.
            query = f"""
            UNWIND $batch AS data
            // Match or create the source node (it should already exist from _ingest_nodes)
            MERGE (source {{uid: data.source_uid}})
            
            // Match or create the target node
            // We use MERGE without a label so we don't accidentally assign the wrong label.
            // If it's unresolved, we add the 'Unresolved' label for easy querying later.
            MERGE (target {{uid: data.target_uid}})
            ON CREATE SET target:Unresolved
            
            // Create the relationship
            MERGE (source)-[r:{rel_type}]->(target)
            SET r.filepath = data.filepath,
                r.line = data.line
            """
            batch = [e.model_dump(exclude_none=True) for e in edge_group]
            session.run(query, batch=batch)

    # ---------------------------------------------------------------------------
    # Incremental Updates
    # ---------------------------------------------------------------------------

    def delete_file_subgraph(self, filepath: str):
        """Delete all nodes (and their edges) that belong to a specific file."""
        query = """
        MATCH (n)
        WHERE n.filepath = $filepath
        DETACH DELETE n
        """
        with self.session() as session:
            session.run(query, filepath=filepath)
