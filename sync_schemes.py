"""Seed script: upsert the in-memory schemes from SchemeManager into Neo4j.
Run this with your virtualenv active after you set `.env` with NEO4J_URI, NEO4J_USER and NEO4J_PASSWORD.
"""
from schemes import SchemeManager

def main():
    sm = SchemeManager()
    # ensure connector is connected via SchemeManager (it connects in __init__)
    neo = sm.neo4j

    schemes = sm.get_all_schemes()
    print(f"Found {len(schemes)} schemes to upsert")

    for scheme_id, data in schemes.items():
        print(f"Upserting {scheme_id}: {data.get('name')}")
        neo.upsert_scheme(scheme_id, data)

    print("Done seeding schemes.")
    sm.close()

if __name__ == '__main__':
    main()
from schemes import SchemeManager

manager = SchemeManager()
for scheme_id, scheme_data in manager.get_all_schemes().items():
    manager.neo4j.upsert_scheme(scheme_id, scheme_data)
print("All schemes synced to Neo4j!") 