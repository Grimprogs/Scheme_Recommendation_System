from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from schemes import SchemeManager
from neo4j_connector import Neo4jConnector
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production!
scheme_manager = SchemeManager()
# Create connector but don't force connectivity at import time. The connector
# will attempt a lazy connection when it's first used. This avoids crashing the
# Flask app when the DB is temporarily unreachable.
neo4j = Neo4jConnector()

# --- Login required decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Signup route ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Check DB availability first
        if not neo4j.ping():
            flash('Database unavailable — please try again later.')
            return render_template('signup.html')

        if neo4j.find_user_by_email(email):
            flash('Email already registered!')
            return redirect(url_for('signup'))
        created = neo4j.create_user_node(name, email, password)
        if not created:
            flash('Could not create account — database error.')
            return render_template('signup.html')
        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

# --- Login route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check DB availability first
        if not neo4j.ping():
            flash('Database unavailable — please try again later.')
            return render_template('login.html')

        user = neo4j.verify_user(email, password)
        if user:
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            flash('Logged in successfully!')
            return redirect(url_for('home'))
        else:
            # Could be invalid credentials or missing DB write — show friendly message
            flash('Invalid credentials or user does not exist.')
            return render_template('login.html')
    return render_template('login.html')

# --- Logout route ---
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!')
    return redirect(url_for('login'))

# --- Home page ---
@app.route('/', methods=['GET', 'POST'])
def home():
    schemes = scheme_manager.get_all_schemes()
    trending = neo4j.get_trending_schemes_by_access()
    user_name = session.get('user_name')
    query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()
    # Get all unique categories
    categories = sorted(list(set([v['category'] for v in schemes.values()])))
    filtered_schemes = schemes
    filtered_trending = trending
    if selected_category:
        # Use Neo4j to get scheme IDs for the selected category
        scheme_ids = neo4j.get_schemes_by_category(selected_category)
        filtered_schemes = {k: v for k, v in schemes.items() if k in scheme_ids}
        filtered_trending = [s for s in trending if (s['scheme_id'] in filtered_schemes)]
    elif query:
        filtered_schemes = {k: v for k, v in schemes.items() if query.lower() in v['name'].lower() or query.lower() in v['category'].lower()}
        filtered_trending = [s for s in trending if (s['scheme_id'] in filtered_schemes)]
    return render_template('index.html', schemes=filtered_schemes, trending=filtered_trending, user_name=user_name, query=query, categories=categories, selected_category=selected_category)

# --- Scheme detail page ---
@app.route('/scheme/<scheme_id>')
@login_required
def view_scheme(scheme_id):
    user_email = session['user_email']
    scheme = scheme_manager.get_scheme_details(scheme_id)
    if not scheme:
        return "Scheme not found", 404
    # Check if user has accessed this scheme
    accessed = False
    accessed_schemes = neo4j.get_user_access_schemes(user_email)
    if scheme_id in accessed_schemes:
        accessed = True
    return render_template('scheme.html', scheme=scheme, scheme_id=scheme_id, user_email=user_email, accessed=accessed)

# --- Access scheme (button) ---
@app.route('/scheme/<scheme_id>/access', methods=['POST'])
@login_required
def access_scheme(scheme_id):
    user_email = session['user_email']
    scheme = scheme_manager.get_scheme_details(scheme_id)
    neo4j.record_scheme_access(user_email, scheme_id, scheme['name'])
    flash('Scheme accessed!')
    return redirect(url_for('view_scheme', scheme_id=scheme_id))

# --- Trending API ---
@app.route('/api/trending')
def get_trending():
    trending = neo4j.get_trending_schemes_by_access()
    return jsonify(trending)

if __name__ == '__main__':
    app.run(debug=True) 