import unittest
import os
import json
import sys

# إضافة المسار الرئيسي للمشروع عشان يقدر يشوف مجلد app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app import db

class URLShortenerTestCase(unittest.TestCase):

    def setUp(self):
        """يتم تشغيل هذه الدالة قبل كل اختبار"""
        # استخدام قاعدة بيانات مؤقتة للاختبارات
        self.test_db_path = 'test_urls.db'
        
        # تغيير مسار الداتابيز في موديول db ليؤشر على الملف المؤقت
        db.DB_PATH = self.test_db_path
        db.init_db(self.test_db_path)

        # تجهيز عميل الاختبار (Test Client) الخاص بـ Flask
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        """يتم تشغيل هذه الدالة بعد كل اختبار"""
        # حذف قاعدة البيانات المؤقتة لتنظيف المكان
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_health_check(self):
        """اختبار الـ Health Check"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "healthy"})

    def test_shorten_url(self):
        """اختبار إنشاء رابط مختصر"""
        payload = {"url": "https://www.google.com"}
        response = self.app.post('/shorten', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("short_code", data)
        self.assertEqual(data["original_url"], "https://www.google.com")
        return data["short_code"]

    def test_redirect(self):
        """اختبار التوجيه (Redirection)"""
        # أولاً ننشئ رابط
        short_code = self.test_shorten_url()
        
        # ثم نحاول الدخول عليه
        response = self.app.get(f'/{short_code}')
        self.assertEqual(response.status_code, 302) # 302 تعني تحويل ناجح
        self.assertIn("google.com", response.location)

    def test_404_not_found(self):
        """اختبار رابط غير موجود"""
        response = self.app.get('/nonexistent123')
        self.assertEqual(response.status_code, 404)

    def test_metrics_endpoint(self):
        """اختبار وجود الـ Metrics"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"url_requests_total", response.data)

if __name__ == '__main__':
    unittest.main()
