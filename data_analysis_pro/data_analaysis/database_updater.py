import sqlite3
import os
from datetime import datetime

class DatabaseUpdater:
    def __init__(self, db_path="data_analysis_pro.db"):
        self.db_path = db_path
    
    def update_database_schema(self):
        """تحديث مخطط قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود الجداول وإضافتها إذا لم تكن موجودة
            self.create_tables(cursor)
            
            # تحديث الجداول الحالية بإضافة الأعمدة الجديدة
            self.update_existing_tables(cursor)
            
            conn.commit()
            conn.close()
            print("✅ تم تحديث قاعدة البيانات بنجاح!")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحديث قاعدة البيانات: {e}")
            return False
    
    def create_tables(self, cursor):
        """إنشاء الجداول إذا لم تكن موجودة"""
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE,
                password VARCHAR(255),
                email VARCHAR(100),
                account_type VARCHAR(20) DEFAULT 'Free',
                subscription_end DATETIME,
                lifetime BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                settings TEXT,
                usage_stats TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                admin_notes TEXT
            )
        ''')
        
        # جدول مجموعات البيانات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(255),
                filename VARCHAR(500),
                description TEXT,
                rows INTEGER,
                columns INTEGER,
                file_size FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_preview TEXT
            )
        ''')
        
        # جدول التحليلات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dataset_id INTEGER,
                analysis_type VARCHAR(100),
                parameters TEXT,
                results TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول خطط الاشتراك
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50),
                price_monthly FLOAT,
                price_yearly FLOAT,
                features TEXT,
                limits TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # جدول اشتراكات المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_id INTEGER,
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                payment_status VARCHAR(20) DEFAULT 'pending'
            )
        ''')
        
        # جدول سجلات المسؤول
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action VARCHAR(255),
                target_user_id INTEGER,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def update_existing_tables(self, cursor):
        """تحديث الجداول الحالية بإضافة الأعمدة المفقودة"""
        
        # التحقق من الأعمدة في جدول users وإضافتها إذا كانت مفقودة
        columns_to_add = [
            ('usage_stats', 'TEXT'),
            ('is_active', 'BOOLEAN DEFAULT TRUE'),
            ('admin_notes', 'TEXT')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                print(f"✅ تم إضافة العمود {column_name} إلى جدول users")
            except sqlite3.OperationalError:
                print(f"ℹ️ العمود {column_name} موجود بالفعل في جدول users")
        
        # إضافة البيانات الأولية
        self.insert_initial_data(cursor)
    
    def insert_initial_data(self, cursor):
        """إدخال البيانات الأولية"""
        
        # إضافة المستخدم المسؤول إذا لم يكن موجوداً
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", 
                      ('muhammedjwad18@gmail.com',))
        if cursor.fetchone()[0] == 0:
            from passlib.hash import pbkdf2_sha256
            hashed_password = pbkdf2_sha256.hash('KINGSMAN238185')
            
            cursor.execute('''
                INSERT INTO users 
                (username, password, email, account_type, lifetime, is_active) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'muhammedjwad18@gmail.com',
                hashed_password,
                'muhammedjwad18@gmail.com',
                'Admin',
                True,
                True
            ))
            print("✅ تم إنشاء المستخدم المسؤول")
        
        # إضافة خطط الاشتراك
        plans = [
            {
                'name': 'Free',
                'price_monthly': 0,
                'price_yearly': 0,
                'features': json.dumps([
                    'تحميل ملفات حتى 10MB',
                    '5 تحليلات أساسية شهرياً',
                    'التصورات الأساسية',
                    'تصدير CSV فقط'
                ]),
                'limits': json.dumps({
                    'max_file_size': 10,
                    'max_analyses_per_month': 5,
                    'max_datasets': 3,
                    'export_formats': ['csv']
                })
            },
            {
                'name': 'Pro',
                'price_monthly': 29.99,
                'price_yearly': 299.99,
                'features': json.dumps([
                    'تحميل ملفات حتى 100MB',
                    'تحليلات غير محدودة',
                    'جميع أنواع التصورات',
                    'التعلم الآلي المتقدم',
                    'التصدير لجميع الصيغ',
                    'دعم فني متميز'
                ]),
                'limits': json.dumps({
                    'max_file_size': 100,
                    'max_analyses_per_month': 9999,
                    'max_datasets': 50,
                    'export_formats': ['csv', 'excel', 'json', 'pdf']
                })
            },
            {
                'name': 'Enterprise',
                'price_monthly': 99.99,
                'price_yearly': 999.99,
                'features': json.dumps([
                    'كل ميزات Pro +',
                    'تحميل ملفات غير محدود',
                    'API متقدم',
                    'تحليلات في الوقت الفعلي',
                    'دعم 24/7',
                    'تخصيص كامل'
                ]),
                'limits': json.dumps({
                    'max_file_size': 1024,
                    'max_analyses_per_month': 99999,
                    'max_datasets': 1000,
                    'export_formats': ['csv', 'excel', 'json', 'pdf', 'html']
                })
            }
        ]
        
        for plan in plans:
            cursor.execute("SELECT COUNT(*) FROM subscription_plans WHERE name = ?", (plan['name'],))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO subscription_plans 
                    (name, price_monthly, price_yearly, features, limits) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    plan['name'],
                    plan['price_monthly'],
                    plan['price_yearly'],
                    plan['features'],
                    plan['limits']
                ))
                print(f"✅ تم إضافة خطة {plan['name']}")

# تشغيل تحديث قاعدة البيانات
if __name__ == "__main__":
    updater = DatabaseUpdater()
    updater.update_database_schema()