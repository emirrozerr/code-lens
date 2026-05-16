from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "codelens_dev")
)

with driver.session() as session:
    # write test
    session.run("CREATE (:Test {name: 'demo'})")

    # read test
    res = session.run("MATCH (n:Test) RETURN count(n) AS c")
    print("Test nodes:", res.single()["c"])

driver.close() 
