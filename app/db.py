import sqlite3
import os

# تحديد المسار الافتراضي لقاعدة البيانات
# نستخدم المسار النسبي بالنسبة لمكان تشغيل التطبيق
DB_FOLDER = os.path.join(os.getcwd(), 'data')
DB_PATH = os.path.join(DB_FOLDER, 'urls.db')

def ensure_db_directory():
    """تأكد من وجود مجلد البيانات"""
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

def get_connection(db_path=None):
    """إنشاء اتصال بقاعدة البيانات"""
    target_path = db_path if db_path else DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    """تهيئة الجدول في قاعدة البيانات"""
    ensure_db_directory()
    conn = get_connection(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  original_url TEXT NOT NULL, 
                  short_code TEXT UNIQUE NOT NULL, 
                  clicks INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# --- عمليات قاعدة البيانات (CRUD Operations) ---

def create_short_url_entry(original_url, short_code):
    """إدخال رابط جديد"""
    conn = get_connection()
    try:
        conn.execute('INSERT INTO urls (original_url, short_code) VALUES (?, ?)',
                     (original_url, short_code))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_original_url(short_code):
    """جلب الرابط الأصلي بناء على الكود المختصر"""
    conn = get_connection()
    entry = conn.execute('SELECT original_url FROM urls WHERE short_code = ?', 
                         (short_code,)).fetchone()
    conn.close()
    return entry['original_url'] if entry else None

def increment_clicks(short_code):
    """زيادة عدد النقرات"""
    conn = get_connection()
    conn.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', (short_code,))
    conn.commit()
    conn.close()
