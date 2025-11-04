from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv
import os
import time
import json
import ssl
from ssl import SSLCertVerificationError


class Neo4jConnector:
    """Neo4j connector used by the project.

    - Reads connection info from environment variables:
      - NEO4J_URI (e.g. neo4j+s://...)
      - NEO4J_USER
      - NEO4J_PASSWORD
      - NEO4J_DATABASE (optional, default 'neo4j')
    - Provides a few helper methods used by tests and the seeder.
    """

    def __init__(self):
        load_dotenv()
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.driver = None

    def connect(self, verify=True):
        """Create the driver. Optionally verify connectivity immediately.

        Raises ServiceUnavailable when the driver cannot reach the server.
        """
        # Allow opting out of certificate verification for development environments
        trust_all = os.getenv("NEO4J_TRUST_ALL_CERTS", "false").lower() in ("1", "true", "yes")
        # If user opted into trusting all certs for development, prefer using
        # a '+ssc' URI (e.g. neo4j+ssc://...) which tells the driver to accept
        # the server certificate chain. If the URI already uses '+ssc' or '+s',
        # just create the driver normally. Otherwise fall back to creating an
        # ssl_context that disables verification (dev only).
        if trust_all:
            if "+ssc" in self.uri or "+s" in self.uri:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            else:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password), ssl_context=ctx)
        else:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        if verify:
            try:
                # verify connectivity and routing table
                self.driver.verify_connectivity()
            except ServiceUnavailable:
                # let caller handle; keep driver open for potential retries
                raise

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass

    def _run_with_retry(self, query, parameters=None, attempts=3, backoff=1.0):
        """Run a query with a small retry/backoff on ServiceUnavailable.

        Returns the Result object on success or raises the last exception.
        """
        if parameters is None:
            parameters = {}

        last_exc = None
        # If driver wasn't created yet, try to create it lazily without strict verification
        if self.driver is None:
            try:
                self.connect(verify=False)
            except ServiceUnavailable as exc:
                print("Warning: cannot connect to Neo4j (lazy connect failed):", exc)
                return []
        for attempt in range(1, attempts + 1):
            try:
                with self.driver.session(database=self.database) as session:
                    result = session.run(query, **parameters)
                    # consume the result while the session is open and return a list
                    return list(result)
            except ServiceUnavailable as exc:
                # Do not raise to the web layer; log and return empty result so
                # the application can continue to serve pages when the DB is
                # temporarily unreachable. Retry a few times first.
                last_exc = exc
                print("Warning: Neo4j ServiceUnavailable (attempt", attempt, "):", exc)
                if attempt < attempts:
                    time.sleep(backoff * attempt)
                    continue
                # Final failure: return empty list rather than raising an exception
                return []

    def upsert_scheme(self, scheme_id, scheme_data):
        """Create or update a Scheme node.

        scheme_data should contain keys: name, category, description, min_amount, url
        """
        query = (
            """
            MERGE (s:Scheme {id: $scheme_id})
            SET s.name = $name,
                s.category = $category,
                s.description = $description,
                s.min_amount = $min_amount,
                s.url = $url
            RETURN s.id AS id
            """
        )
        params = {
            "scheme_id": scheme_id,
            "name": scheme_data.get("name"),
            "category": scheme_data.get("category"),
            "description": scheme_data.get("description"),
            "min_amount": scheme_data.get("min_amount"),
            "url": scheme_data.get("url"),
        }
        # Use retry wrapper to give a chance if routing info is transiently unavailable
        # we don't need the returned rows for upsert; calling _run_with_retry will
        # execute the query and return any rows if present.
        _ = self._run_with_retry(query, params)

    def record_scheme_access(self, user_email, scheme_id, scheme_name=None):
        """Record that a user accessed (viewed/clicked) a scheme."""
        query = (
            """
            MERGE (u:User {email: $email})
            MERGE (s:Scheme {id: $scheme_id})
            SET s.name = coalesce(s.name, $scheme_name)
            MERGE (u)-[r:ACCESSED]->(s)
            ON CREATE SET r.count = 1
            ON MATCH SET r.count = coalesce(r.count,0) + 1
            RETURN r.count AS count
            """
        )
        params = {"email": user_email, "scheme_id": scheme_id, "scheme_name": scheme_name}
        res = self._run_with_retry(query, params)
        return [dict(rec) for rec in res]

    def get_trending_schemes_by_access(self, limit=10):
        query = (
            """
            MATCH (u:User)-[r:ACCESSED]->(s:Scheme)
            RETURN s.id AS scheme_id, s.name AS scheme_name, SUM(r.count) AS access_count
            ORDER BY access_count DESC
            LIMIT $limit
            """
        )
        res = self._run_with_retry(query, {"limit": limit})
        return [dict(rec) for rec in res]

    def get_schemes_by_category(self, category):
        query = "MATCH (s:Scheme) WHERE toLower(s.category)=toLower($category) RETURN s.id as scheme_id"
        res = self._run_with_retry(query, {"category": category})
        return [r["scheme_id"] for r in res]

    # ---- Methods used by the test harness (minimal implementations) ----
    def create_user(self, user_id, user_data):
        """Create or update a simple User node used by tests.

        user_data: dict with keys like 'name' and 'email'
        """
        query = (
            "MERGE (u:User {id: $id}) SET u.name = $name, u.email = $email RETURN u.id AS id"
        )
        params = {"id": user_id, "name": user_data.get("name"), "email": user_data.get("email")}
        res = self._run_with_retry(query, params)
        return [dict(r) for r in res]

    # ---- Compatibility API expected by app.py -----
    def create_user_node(self, name, email, password):
        """Compatibility: create a user node. Stores password as-is (simple).

        In production you should hash passwords. This keeps behavior simple for now.
        """
        query = (
            "MERGE (u:User {email: $email}) SET u.name = $name, u.password = $password RETURN u.email AS email, u.name AS name"
        )
        params = {"email": email, "name": name, "password": password}
        res = self._run_with_retry(query, params)
        rows = [dict(r) for r in res]
        return rows[0] if rows else None

    def find_user_by_email(self, email):
        query = "MATCH (u:User {email: $email}) RETURN u.name AS name, u.email AS email, u.password AS password LIMIT 1"
        res = self._run_with_retry(query, {"email": email})
        rows = [dict(r) for r in res]
        return rows[0] if rows else None

    def verify_user(self, email, password):
        """Simple verification: returns user dict if password matches."""
        user = self.find_user_by_email(email)
        if not user:
            return None
        # simple equality check; production should use hashing
        if user.get("password") == password:
            return {"email": user.get("email"), "name": user.get("name")}
        return None

    def get_user_access_schemes(self, user_email):
        """Return list of scheme ids accessed by the user."""
        query = "MATCH (u:User {email: $email})-[r:ACCESSED]->(s:Scheme) RETURN s.id AS scheme_id"
        res = self._run_with_retry(query, {"email": user_email})
        return [r["scheme_id"] for r in res]

    def ping(self, timeout_seconds: float = 3.0) -> bool:
        """Quick connectivity check to the database.

        Returns True when a simple query succeeds, False otherwise.
        """
        try:
            # Ensure driver exists (lazy connect)
            if self.driver is None:
                self.connect(verify=False)
            # Try a very small run
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1 AS x")
            return True
        except Exception as e:
            # Log the underlying reason for debugging
            print("Neo4j ping failed:", type(e).__name__, str(e))
            return False

    def track_activity(self, user_id, activity_type, activity_data):
        """Record a simple activity node and link it to the user."""
        # store activity details as JSON string for simplicity
        details = json.dumps(activity_data or {})
        query = (
            """
            MERGE (u:User {id: $user_id})
            CREATE (a:Activity {type: $atype, details: $details, timestamp: $ts})
            MERGE (u)-[:PERFORMED]->(a)
            RETURN a.type AS type, a.timestamp AS timestamp
            """
        )
        params = {"user_id": user_id, "atype": activity_type, "details": details, "ts": time.time()}
        res = self._run_with_retry(query, params)
        return [dict(r) for r in res]

    def get_user_trends(self, user_id):
        """Return counts of activity types for a user."""
        query = (
            "MATCH (u:User {id: $user_id})-[:PERFORMED]->(a:Activity)"
            " RETURN a.type AS activity_type, count(*) AS count ORDER BY count DESC"
        )
        res = self._run_with_retry(query, {"user_id": user_id})
        return [dict(r) for r in res]

