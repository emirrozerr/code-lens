"""Neo4j graph database client stub.

Provides connection management and basic read/write helpers for code graph nodes,
edges, rule nodes, and vector index operations.
"""


class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self._driver = None  # TODO: initialize neo4j.GraphDatabase.driver

    def connect(self) -> None:
        """Open the Neo4j driver connection.

        TODO: self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        """

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()

    def run(self, cypher: str, **params):
        """Execute a Cypher query and return results.

        TODO: Use self._driver.session().run(cypher, **params)
        """
        raise NotImplementedError

    def write_nodes(self, nodes: list[dict]) -> None:
        """Batch-write code graph nodes to Neo4j.

        TODO: Use MERGE on node id to support incremental updates.
        """

    def write_edges(self, edges: list[dict]) -> None:
        """Batch-write code graph edges to Neo4j.

        TODO: Use MERGE on (source)-[edge]->(target).
        """


def get_client() -> Neo4jClient:
    """Return a configured Neo4jClient using app settings."""
    from app.core.config import settings

    return Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
    )
