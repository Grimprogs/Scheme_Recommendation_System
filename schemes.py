from neo4j_connector import Neo4jConnector
from datetime import datetime

class SchemeManager:
    def __init__(self):
        # Create connector but defer connecting to avoid crashing the app
        # if the database is temporarily unreachable.
        self.neo4j = Neo4jConnector()
        
        # Sample schemes data
        self.schemes = {
            'scheme1': {
                'name': 'Retirement Savings Plan',
                'description': 'Long-term retirement savings with tax benefits',
                'category': 'retirement',
                'min_amount': 5000,
                'url': 'https://www.npscra.nsdl.co.in/'
            },
            'scheme2': {
                'name': 'Education Fund',
                'description': 'Save for your child\'s education',
                'category': 'education',
                'min_amount': 10000,
                'url': 'https://scholarships.gov.in/'
            },
            'scheme3': {
                'name': 'Health Insurance Plan',
                'description': 'Comprehensive health coverage',
                'category': 'health',
                'min_amount': 2000,
                'url': 'https://www.pmjay.gov.in/'
            },
            'scheme4': {
                'name': 'Wealth Builder',
                'description': 'High-growth investment opportunity',
                'category': 'investment',
                'min_amount': 25000,
                'url': 'https://www.nsc.gov.in/'
            },
            'scheme5': {
                'name': 'Emergency Fund',
                'description': 'Quick access savings for emergencies',
                'category': 'savings',
                'min_amount': 1000,
                'url': 'https://www.rbi.org.in/'
            },
            'scheme6': {
                'name': 'Pradhan Mantri Jan Dhan Yojana',
                'description': 'Financial inclusion for all households in India',
                'category': 'banking',
                'min_amount': 0,
                'url': 'https://pmjdy.gov.in/'
            },
            'scheme7': {
                'name': 'Sukanya Samriddhi Yojana',
                'description': 'Savings scheme for the girl child',
                'category': 'women',
                'min_amount': 250,
                'url': 'https://www.nsiindia.gov.in/'
            },
            'scheme8': {
                'name': 'Pradhan Mantri Jeevan Jyoti Bima Yojana',
                'description': 'Life insurance cover for all',
                'category': 'insurance',
                'min_amount': 330,
                'url': 'https://www.jansuraksha.gov.in/Forms-PMJJBY.aspx'
            },
            'scheme9': {
                'name': 'Pradhan Mantri Suraksha Bima Yojana',
                'description': 'Accident insurance cover for all',
                'category': 'insurance',
                'min_amount': 12,
                'url': 'https://www.jansuraksha.gov.in/Forms-PMSBY.aspx'
            },
            'scheme10': {
                'name': 'Atal Pension Yojana',
                'description': 'Pension scheme for unorganized sector workers',
                'category': 'retirement',
                'min_amount': 100,
                'url': 'https://npscra.nsdl.co.in/scheme-details.php'
            },
            'scheme11': {
                'name': 'Pradhan Mantri Awas Yojana',
                'description': 'Affordable housing for all',
                'category': 'housing',
                'min_amount': 0,
                'url': 'https://pmaymis.gov.in/'
            },
            'scheme12': {
                'name': 'Kisan Credit Card',
                'description': 'Credit support for farmers',
                'category': 'agriculture',
                'min_amount': 0,
                'url': 'https://pmkisan.gov.in/'
            },
            'scheme13': {
                'name': 'Pradhan Mantri Fasal Bima Yojana',
                'description': 'Crop insurance for farmers',
                'category': 'agriculture',
                'min_amount': 100,
                'url': 'https://pmfby.gov.in/'
            },
            'scheme14': {
                'name': 'Stand Up India',
                'description': 'Promoting entrepreneurship among women and SC/ST',
                'category': 'entrepreneurship',
                'min_amount': 10000,
                'url': 'https://www.standupmitra.in/'
            },
            'scheme15': {
                'name': 'National Social Assistance Programme',
                'description': 'Social pension for elderly, widows, and disabled',
                'category': 'social',
                'min_amount': 0,
                'url': 'https://nsap.nic.in/'
            },
            'scheme16': {
                'name': 'Pradhan Mantri Mudra Yojana',
                'description': 'Loans for small businesses',
                'category': 'business',
                'min_amount': 50000,
                'url': 'https://www.mudra.org.in/'
            },
            'scheme17': {
                'name': 'Swachh Bharat Mission',
                'description': 'Clean India campaign',
                'category': 'sanitation',
                'min_amount': 0,
                'url': 'https://swachhbharatmission.gov.in/'
            },
            'scheme18': {
                'name': 'Digital India',
                'description': 'Transforming India into a digitally empowered society',
                'category': 'technology',
                'min_amount': 0,
                'url': 'https://digitalindia.gov.in/'
            },
            'scheme19': {
                'name': 'Beti Bachao Beti Padhao',
                'description': 'Empowering the girl child through education',
                'category': 'women',
                'min_amount': 0,
                'url': 'https://wcd.nic.in/bbbp-schemes'
            },
            'scheme20': {
                'name': 'National Pension System',
                'description': 'Voluntary retirement savings scheme',
                'category': 'retirement',
                'min_amount': 500,
                'url': 'https://www.npscra.nsdl.co.in/'
            }
        }

    def get_all_schemes(self):
        """Return all available schemes"""
        return self.schemes

    def track_scheme_view(self, user_id, scheme_id):
        """Track when a user views a scheme"""
        activity_data = {
            'timestamp': datetime.now().isoformat(),
            'scheme_id': scheme_id,
            'scheme_name': self.schemes[scheme_id]['name']
        }
        self.neo4j.track_activity(user_id, 'VIEW_SCHEME', activity_data)

    def get_trending_schemes(self, limit=5):
        """Get trending schemes based on user views"""
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Activity {type: 'VIEW_SCHEME'})
                WITH a.scheme_id as scheme_id, a.scheme_name as scheme_name, count(*) as view_count
                ORDER BY view_count DESC
                LIMIT $limit
                RETURN scheme_id, scheme_name, view_count
                """,
                limit=limit
            )
            return [dict(record) for record in result]

    def get_scheme_details(self, scheme_id):
        """Get detailed information about a specific scheme"""
        return self.schemes.get(scheme_id)

    def close(self):
        """Close the Neo4j connection"""
        self.neo4j.close() 