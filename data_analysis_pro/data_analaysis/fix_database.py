import streamlit as st
import sqlite3
import json
from passlib.hash import pbkdf2_sha256
import os

def fix_database():
    st.title("🔧 إصلاح قاعدة البيانات")
    
    st.info("""
    هذه الأداة ستعمل على إصلاح قاعدة البيانات وإنشاء الهيكل الصحيح.
    سيتم إنشاء الجداول المطلوبة وإضافة المستخدم المسؤول.
    """)
    
    if st.button("🚀 بدء الإصلاح", type="primary"):
        with st.spinner("جاري إصلاح قاعدة البيانات..."):
            try:
                # الاتصال بقاعدة البيانات
                conn = sqlite3.connect('data_analysis_pro.db')
                cursor = conn.cursor()
                
                # إنشاء الجداول
                tables = [
                    # جدول المستخدمين
                    '''
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
                    ''',
                    
                    # جدول مجموعات البيانات
                    '''
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
                    ''',
                    
                    # جدول خطط الاشتراك
                    '''
                    CREATE TABLE IF NOT EXISTS subscription_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(50),
                        price_monthly FLOAT,
                        price_yearly FLOAT,
                        features TEXT,
                        limits TEXT,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                    '''
                ]
                
                for table_sql in tables:
                    cursor.execute(table_sql)
                
                # إضافة المستخدم المسؤول
                hashed_password = pbkdf2_sha256.hash('KINGSMAN238185')
                cursor.execute('''
                    INSERT OR IGNORE INTO users 
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
                
                # إضافة خطط الاشتراك
                plans = [
                    ('Free', 0, 0, 
                     '["تحميل ملفات حتى 10MB", "5 تحليلات أساسية شهرياً", "التصورات الأساسية", "تصدير CSV فقط"]',
                     '{"max_file_size": 10, "max_analyses_per_month": 5, "max_datasets": 3, "export_formats": ["csv"]}'),
                    
                    ('Pro', 29.99, 299.99,
                     '["تحميل ملفات حتى 100MB", "تحليلات غير محدودة", "جميع أنواع التصورات", "التعلم الآلي المتقدم", "التصدير لجميع الصيغ", "دعم فني متميز"]',
                     '{"max_file_size": 100, "max_analyses_per_month": 9999, "max_datasets": 50, "export_formats": ["csv", "excel", "json", "pdf"]}'),
                    
                    ('Enterprise', 99.99, 999.99,
                     '["كل ميزات Pro +", "تحميل ملفات غير محدود", "API متقدم", "تحليلات في الوقت الفعلي", "دعم 24/7", "تخصيص كامل"]',
                     '{"max_file_size": 1024, "max_analyses_per_month": 99999, "max_datasets": 1000, "export_formats": ["csv", "excel", "json", "pdf", "html"]}')
                ]
                
                for plan in plans:
                    cursor.execute('''
                        INSERT OR IGNORE INTO subscription_plans 
                        (name, price_monthly, price_yearly, features, limits) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', plan)
                
                conn.commit()
                conn.close()
                
                st.success("✅ تم إصلاح قاعدة البيانات بنجاح!")
                st.balloons()
                
                st.info("""
                **بيانات الدخول:**
                - **Username:** muhammedjwad18@gmail.com
                - **Password:** KINGSMAN238185
                - **Account Type:** Admin
                """)
                
            except Exception as e:
                st.error(f"❌ خطأ في إصلاح قاعدة البيانات: {e}")

if __name__ == "__main__":
    fix_database()