import sqlite3
import string
import random
import os
from flask import Flask, request, redirect, Response, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- Configuration ---
# تحديد مسار قاعدة البيانات ليكون داخل مجلد data
DB_FOLDER = os.path.join(os.getcwd(), 'data')
DB_PATH = os.path.join(DB_FOLDER, 'urls.db')

# التأكد من وجود مجلد البيانات
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter('url_requests_total', 'Total URL Creation Requests', ['endpoint'])
REDIRECT_COUNT = Counter('url_redirects_total', 'Total Redirections', ['short_code'])

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  original_url TEXT NOT NULL, 
                  short_code TEXT UNIQUE NOT NULL, 
                  clicks INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# --- Helper Functions ---
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Routes ---

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
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO urls (original_url, short_code) VALUES (?, ?)',
                     (original_url, short_code))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Collision detected, try again"}), 500
    finally:
        conn.close()
        
    return jsonify({
        "original_url": original_url,
        "short_url": request.host_url + short_code,
        "short_code": short_code
    }), 201

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = get_db_connection()
    url_entry = conn.execute('SELECT original_url FROM urls WHERE short_code = ?', 
                             (short_code,)).fetchone()
    
    if url_entry:
        conn.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', (short_code,))
        conn.commit()
        conn.close()
        
        REDIRECT_COUNT.labels(short_code=short_code).inc()
        return redirect(url_entry['original_url'])
    else:
        conn.close()
        return jsonify({"error": "URL not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
