# Deploying the Flask + Neo4j app

This document explains how to deploy the full Flask backend (with Neo4j Aura) to Render. It also includes a short note about hosting a static frontend on Netlify and the `neo4j` driver TLS caveat.

## Recommended: Host full app on Render (simple)
1. Push your repository to GitHub.
2. Create a new Web Service on Render and connect your GitHub repo + branch.
3. Set build & start settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - (Procfile and runtime.txt are included in this repo for convenience.)
4. Add the environment variables in the Render dashboard (Settings -> Environment):
   - `NEO4J_URI` = `neo4j+s://<your-aura-host>`
   - `NEO4J_USER` = `neo4j`
   - `NEO4J_PASSWORD` = `<your-aura-password>`
   - `NEO4J_DATABASE` = `neo4j`
   - Do NOT set `NEO4J_TRUST_ALL_CERTS` in production.
5. Deploy and watch the logs. If the service fails to connect to Neo4j, verify the password and network egress rules.
6. (Optional) Run the seeder remotely (one-off job) or include a migration hook to run `python sync_schemes.py` once after deployment.

## Netlify (frontend-only) + Render backend (hybrid)
- Netlify serves static files; it cannot run the Flask server. If you want a CDN frontend:
  1. Extract templates / build a static SPA and push to GitHub.
  2. Deploy static site on Netlify.
  3. Deploy Flask API on Render as above.
  4. Configure CORS on your Flask API and set the API base URL in the frontend.
  5. Optionally configure Netlify `_redirects` to proxy API paths to the Render service.

## TLS and local dev caveats
- For production, always use `neo4j+s://` and ensure your environment has the correct password.
- During local development, if your network intercepts TLS (corporate proxy), you may have used `neo4j+ssc://` or `NEO4J_TRUST_ALL_CERTS=true`. Do not use these in production.

## Quick Render checklist
- Repo linked to Render
- `requirements.txt` contains `Flask` and `neo4j` (this repo pins `neo4j==5.14.1`)
- Env vars set in dashboard
- Start command set to use Gunicorn

If you want, I can also:
- Add a `render.yaml` if you want Infrastructure-as-Code for Render.
- Add a GitHub Actions workflow that auto-deploys to Render on push.

