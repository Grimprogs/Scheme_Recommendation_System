import socket, ssl, os
from dotenv import load_dotenv
load_dotenv()
host = os.getenv('NEO4J_URI','').replace('neo4j+s://','').replace('neo4j://','').split('/')[0]
port = 7687
print('Checking TLS to', host, port)
ctx = ssl.create_default_context()
# allow cert validation to run (we just want to see handshake)
try:
    with socket.create_connection((host, port), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ss:
            cert = ss.getpeercert()
            print('TLS handshake OK. Certificate subject:', cert.get('subject'))
except Exception as e:
    print('TLS check failed:', type(e).__name__, e)
