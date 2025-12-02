import sqlite3
import string
import random
import os
from flask import Flask, request, redirect, Response, jsonify, render_template
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

# --- Fix Import Error ---
# استخدام import db بدلاً من from . import db لأننا نشغل الملف مباشرة
import db 

app = Flask(__name__)

# --- Configuration ---
DB_FOLDER = os.path.join(os.getcwd(), 'data')
DB_PATH = os.path.join(DB_FOLDER, 'urls.db')

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter('url_requests_total', 'Total URL Creation Requests', ['endpoint'])
REDIRECT_COUNT = Counter('url_redirects_total', 'Total Redirections', ['short_code'])

# --- Database Setup ---
# نتأكد من تهيئة قاعدة البيانات عند بداية التشغيل
db.init_db()

# --- Helper Functions ---
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html') 

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    REQUEST_COUNT.labels(endpoint='/shorten').inc()
    
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    original_url = data['url']
    short_code = generate_short_code()
    
    # استخدام الدالة من موديول db
    success = db.create_short_url_entry(original_url, short_code)
    
    if not success:
        return jsonify({"error": "Collision detected, try again"}), 500
        
    return jsonify({
        "original_url": original_url,
        "short_url": request.host_url + short_code,
        "short_code": short_code
    }), 201

@app.route('/<short_code>')
def redirect_to_url(short_code):
    original_url = db.get_original_url(short_code)
    
    if original_url:
        db.increment_clicks(short_code)
        REDIRECT_COUNT.labels(short_code=short_code).inc()
        return redirect(original_url)
    else:
        return jsonify({"error": "URL not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
