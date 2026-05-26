from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "codelens_dev")
    )

    with driver.session() as session:
        result = session.run("RETURN 'Neo4j OK' AS msg")
        print(result.single()["msg"])

    driver.close()

except Exception as e:
    print("Connection failed:", e)