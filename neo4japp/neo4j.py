from neo4j import GraphDatabase

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def create_node(self, label, properties):
        query = f"CREATE (n:{label} $props) RETURN n"
        return self.query(query, parameters={"props": properties})

    def create_relationship(self, label1, properties1, label2, properties2, rel_type):
        query = (
            f"MATCH (a:{label1} {{name: $props1.name}}), (b:{label2} {{name: $props2.name}}) "
            f"CREATE (a)-[r:{rel_type}]->(b) RETURN type(r)"
        )
        return self.query(query, parameters={"props1": properties1, "props2": properties2})

# Example usage
# conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
# conn.create_node("City", {"name": "Rabat"})
# conn.create_relationship("City", {"name": "Rabat"}, "Amenity", {"name": "Hospital"}, "HAS_AMENITY")
# conn.close()
