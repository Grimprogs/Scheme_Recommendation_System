from neo4j_connector import Neo4jConnector
from datetime import datetime

def test_connection():
    # Initialize the connector
    neo4j = Neo4jConnector()
    
    try:
        # Connect to the database
        neo4j.connect()
        print("Successfully connected to Neo4j!")
        
        # Create a test user
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        neo4j.create_user('test123', user_data)
        print("Created test user")
        
        # Track some activities
        activities = [
            ('VIEW_SCHEME', {'timestamp': datetime.now().isoformat(), 'scheme_id': 'scheme1'}),
            ('SEARCH_SCHEME', {'timestamp': datetime.now().isoformat(), 'query': 'retirement'}),
            ('CLICK_SCHEME', {'timestamp': datetime.now().isoformat(), 'scheme_id': 'scheme2'})
        ]
        
        for activity_type, activity_data in activities:
            neo4j.track_activity('test123', activity_type, activity_data)
            print(f"Tracked activity: {activity_type}")
        
        # Get user trends
        trends = neo4j.get_user_trends('test123')
        print("\nUser Activity Trends:")
        for trend in trends:
            print(f"{trend['activity_type']}: {trend['count']} times")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        neo4j.close()

if __name__ == "__main__":
    test_connection() 