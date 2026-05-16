CREATE (a:File {name: "app.py"});
CREATE (b:File {name: "db.py"});
CREATE (c:File {name: "auth.py"});
CREATE (a)-[:IMPORTS]->(b);
CREATE (a)-[:IMPORTS]->(c);