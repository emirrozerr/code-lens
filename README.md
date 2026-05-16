## Seed Example Data

Run the following Cypher in Neo4j Browser (http://localhost:7474):

```cypher
CREATE (a:File {name: "app.py"});
CREATE (b:File {name: "db.py"});
CREATE (c:File {name: "auth.py"});

CREATE (a)-[:IMPORTS]->(b);
CREATE (a)-[:IMPORTS]->(c);
### Connection

- Neo4j HTTP: http://localhost:7474
- Neo4j Bolt: bolt://localhost:7687
- Default credentials: neo4j / codelens_dev