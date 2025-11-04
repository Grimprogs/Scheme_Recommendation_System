from neo4j_connector import Neo4jConnector

c = Neo4jConnector()
try:
    # try without immediate connectivity verification
    c.connect(verify=False)
    with c.driver.session(database=c.database) as s:
        try:
            res = s.run("RETURN 1 as x")
            print('Query result:', [r['x'] for r in res])
        except Exception as e:
            print('Session run exception:', type(e).__name__, str(e))
except Exception as e:
    print('Connect exception:', type(e).__name__, str(e))
finally:
    c.close()
