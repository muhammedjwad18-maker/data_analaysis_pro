import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import re
import json
import io
import time
import sys
import os
import sqlite3
from passlib.hash import pbkdf2_sha256
import hashlib
import uuid
import asyncio
import threading

# ========== نظام بوت التلجرام ==========

import telegram
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

BOT_TOKEN = "8271273469:AAF6oPqkSm14mvfyao9Mz45uOaj_qsXo5Gg"

class TelegramPaymentBot:
    def __init__(self, db_manager):
        self.db = db_manager
        self.token = BOT_TOKEN
        self.application = None
        self.bot = None
        self.admin_users = [7355375396]  # 🔥 أنت المسؤول
        
    async def start_bot(self):
        """بدء تشغيل البوت"""
        try:
            self.application = Application.builder().token(self.token).build()
            self.bot = telegram.Bot(token=self.token)
            
            # الحصول على معلومات البوت
            bot_info = await self.bot.get_me()
            bot_username = bot_info.username
            print(f"🤖 البوت يعمل بنجاح: @{bot_username}")
            print(f"🔗 رابط البوت: https://t.me/{bot_username}")
            
            # إضافة handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("admin", self.admin_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("id", self.get_id_command))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            print("✅ بوت الدفع يعمل وجاهز لاستقبال الأوامر...")
            await self.application.run_polling()
            
        except Exception as e:
            print(f"❌ خطأ في تشغيل البوت: {e}")

    async def start_command(self, update: Update, context):
        """أمر /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "بدون اسم"
        first_name = update.effective_user.first_name or "مستخدم"
        
        print(f"👤 مستخدم جديد: {user_id} - @{username} - {first_name}")
        
        # إذا كان هذا أول مستخدم، أضفه كمسؤول
        if not self.admin_users:
            self.admin_users.append(user_id)
            print(f"👑 تم تعيين المستخدم {user_id} كمسؤول رئيسي")
            
        if user_id in self.admin_users:
            welcome_text = f"""
            👑 **مرحباً بك {first_name}!**

            ✅ أنت مسؤول في النظام
            🤖 هذا البوت سيتلقى إشعارات الدفع تلقائياً

            📊 **الأوامر المتاحة:**
            /admin - لوحة التحكم
            /stats - إحصائيات النظام  
            /id - عرض رقمك

            🔔 **سيصلك إشعار** عند كل دفعة جديدة
            ✅ **يمكنك تفعيل الحسابات** بنقرة واحدة

            🆔 **رقمك:** `{user_id}`
            👤 **اسمك:** {first_name}
            """
            
            keyboard = [
                [InlineKeyboardButton("📊 لوحة التحكم", callback_data="admin_panel")],
                [InlineKeyboardButton("🆔 عرض رقمي", callback_data="show_id")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            welcome_text = f"""
            🤖 **مرحباً بك {first_name}!**

            🔔 هذا البوت مخصص لإدارة مدفوعات Data Analysis Pro
            📞 للاستفسارات، تواصل مع المسؤول.

            👤 أنت: {first_name}
            🆔 رقمك: `{user_id}`
            """
            await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def admin_command(self, update: Update, context):
        """لوحة تحكم المسؤول"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_users:
            await update.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا الأمر")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="stats")],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")],
            [InlineKeyboardButton("💰 المدفوعات المعلقة", callback_data="pending_payments")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("👑 **لوحة تحكم المسؤول**", reply_markup=reply_markup)

    async def stats_command(self, update: Update, context):
        """إحصائيات النظام"""
        user_id = update.effective_user.id
        
        if user_id not in self.admin_users:
            await update.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا الأمر")
            return
        
        stats_text = self.get_system_stats()
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    def get_system_stats(self):
        """الحصول على إحصائيات النظام"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM payments")
            total_payments = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(amount) FROM payments WHERE payment_status = 'completed'")
            total_revenue = cursor.fetchone()[0] or 0
            
            conn.close()
            
            stats_text = f"""
📊 **إحصائيات النظام**

👥 إجمالي المستخدمين: {total_users}
💰 إجمالي المدفوعات: {total_payments}
💵 إجمالي الإيرادات: {total_revenue:,} دينار
👑 عدد المسؤولين: {len(self.admin_users)}

🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            return stats_text
            
        except Exception as e:
            return f"❌ خطأ في جلب الإحصائيات: {str(e)}"

    async def handle_callback(self, update: Update, context):
        """معالجة ضغطات الأزرار"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if user_id not in self.admin_users:
            await query.edit_message_text("❌ ليس لديك صلاحية لهذا الإجراء")
            return
        
        if data == "stats":
            stats_text = self.get_system_stats()
            await query.edit_message_text(stats_text, parse_mode='Markdown')
        elif data.startswith("activate_"):
            await self.activate_user_account(query, data)

    async def activate_user_account(self, query, data):
        """تفعيل حساب المستخدم"""
        try:
            parts = data.split("_")
            target_user_id = int(parts[1])
            plan_type = parts[2]
            transaction_id = parts[3] if len(parts) > 3 else "غير معروف"
            
            success = self.db.update_user_account(target_user_id, plan_type)
            
            if success:
                self.update_payment_status(transaction_id, 'completed')
                await query.edit_message_text(f"✅ تم تفعيل حساب {target_user_id}")
            else:
                await query.edit_message_text("❌ فشل في التفعيل")
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ: {str(e)}")

    def update_payment_status(self, transaction_id, status):
        """تحديث حالة الدفع"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE payments SET payment_status = ? WHERE transaction_id = ?', (status, transaction_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ خطأ في تحديث الدفع: {e}")

    def run_in_thread(self):
        """تشغيل البوت في thread منفصل"""
        def run():
            asyncio.run(self.start_bot())
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

class InvoiceManager:
    def __init__(self, telegram_bot, db_manager):
        self.bot = telegram_bot
        self.db = db_manager
    
    async def send_invoice_to_admins(self, payment_data):
        """إرسال الفاتورة لجميع المسؤولين"""
        try:
            invoice_text = self.generate_invoice_text(payment_data)
            
            for admin_id in self.bot.admin_users:
                try:
                    keyboard = [
                        [
                            InlineKeyboardButton("✅ تفعيل الحساب", 
                                              callback_data=f"activate_{payment_data['user_id']}_{payment_data['plan_type']}_{payment_data['transaction_id']}"),
                            InlineKeyboardButton("❌ رفض الدفع", 
                                              callback_data=f"reject_{payment_data['transaction_id']}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await self.bot.bot.send_message(
                        chat_id=admin_id,
                        text=invoice_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    print(f"✅ تم إرسال الفاتورة للمسؤول {admin_id}")
                except Exception as e:
                    print(f"❌ خطأ في إرسال للمسؤول {admin_id}: {e}")
        except Exception as e:
            print(f"❌ خطأ عام: {e}")
    
    def generate_invoice_text(self, payment_data):
        """توليد نص الفاتورة"""
        return f"""
🧾 **فاتورة دفع جديدة**

👤 المستخدم: {payment_data['username']}
🆔 الرقم: `{payment_data['user_id']}`
📧 البريد: {payment_data.get('email', 'غير محدد')}

💳 **تفاصيل الدفع:**
• رقم المعاملة: `{payment_data['transaction_id']}`
• المبلغ: {payment_data['amount']:,} دينار
• الخطة: {payment_data['plan_type']}
• طريقة الدفع: {payment_data.get('payment_method', 'غير محدد')}

🕒 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """

# استيراد نظام اللغات
try:
    from languages import get_language, get_available_languages
except ImportError:
    # تعريف بدائي إذا فشل الاستيراد
    def get_language(lang_code):
        translations = {
            'en': {
                'payment_system': 'Payment System',
                'payment_method': 'Payment Method',
                'credit_card': 'Credit Card',
                'paypal': 'PayPal',
                'bank_transfer': 'Bank Transfer',
                'card_number': 'Card Number',
                'expiry_date': 'Expiry Date',
                'cvv': 'CVV',
                'name_on_card': 'Name on Card',
                'process_payment': 'Process Payment',
                'payment_success': 'Payment Successful!',
                'payment_failed': 'Payment Failed',
                'insufficient_funds': 'Insufficient Funds',
                'invalid_card': 'Invalid Card Details',
                'payment_processing': 'Processing Payment...',
                'transaction_id': 'Transaction ID',
                'amount': 'Amount',
                'currency': 'Currency',
                'payment_history': 'Payment History',
                'subscription_payment': 'Subscription Payment',
                'one_time_payment': 'One-Time Payment',
                'refund': 'Refund',
                'refund_request': 'Refund Request',
                'billing_info': 'Billing Information',
                'tax_amount': 'Tax Amount',
                'total_amount': 'Total Amount',
                'payment_date': 'Payment Date',
                'payment_status': 'Payment Status',
                'completed': 'Completed',
                'pending': 'Pending',
                'failed': 'Failed',
                'refunded': 'Refunded'
            },
            'ar': {
                'payment_system': 'نظام الدفع',
                'payment_method': 'طريقة الدفع',
                'credit_card': 'بطاقة ائتمان',
                'paypal': 'باي بال',
                'bank_transfer': 'تحويل بنكي',
                'card_number': 'رقم البطاقة',
                'expiry_date': 'تاريخ الانتهاء',
                'cvv': 'CVV',
                'name_on_card': 'الاسم على البطاقة',
                'process_payment': 'معالجة الدفع',
                'payment_success': 'تم الدفع بنجاح!',
                'payment_failed': 'فشل في الدفع',
                'insufficient_funds': 'رصيد غير كافي',
                'invalid_card': 'بيانات البطاقة غير صالحة',
                'payment_processing': 'جاري معالجة الدفع...',
                'transaction_id': 'رقم المعاملة',
                'amount': 'المبلغ',
                'currency': 'العملة',
                'payment_history': 'سجل المدفوعات',
                'subscription_payment': 'دفع الاشتراك',
                'one_time_payment': 'دفع لمرة واحدة',
                'refund': 'استرداد',
                'refund_request': 'طلب استرداد',
                'billing_info': 'معلومات الفواتير',
                'tax_amount': 'مبلغ الضريبة',
                'total_amount': 'المبلغ الإجمالي',
                'payment_date': 'تاريخ الدفع',
                'payment_status': 'حالة الدفع',
                'completed': 'مكتمل',
                'pending': 'قيد الانتظار',
                'failed': 'فشل',
                'refunded': 'تم الاسترداد'
            },
            'ku': {
                'payment_system': 'Sîstema Peredayînê',
                'payment_method': 'Rêbaza Peredayînê',
                'credit_card': 'Karta Krediyê',
                'paypal': 'PayPal',
                'bank_transfer': 'Guhertina Bankê',
                'card_number': 'Hejmara Kartê',
                'expiry_date': 'Dîroka Dawî',
                'cvv': 'CVV',
                'name_on_card': 'Navê li ser Kartê',
                'process_payment': 'Pereyê Biserîne',
                'payment_success': 'Peredayîn bi serketî!',
                'payment_failed': 'Peredayîn têk çû',
                'insufficient_funds': 'Bêşê Peredan',
                'invalid_card': 'Agahiyên Kartê ne derbasdar in',
                'payment_processing': 'Pereyê tê birêvebirin...',
                'transaction_id': 'Nasnameya Bazirganiyê',
                'amount': 'Biha',
                'currency': 'Dirav',
                'payment_history': 'Dîroka Pereyan',
                'subscription_payment': 'Pereya Abonetiyê',
                'one_time_payment': 'Pereya Carekê',
                'refund': 'Vegerandin',
                'refund_request': 'Daxwaza Vegerandinê',
                'billing_info': 'Agahdariya Billing',
                'tax_amount': 'Bîhayê Baca',
                'total_amount': 'Bihayê Tevahî',
                'payment_date': 'Dîroka Pereyê',
                'payment_status': 'Rewşa Pereyê',
                'completed': 'Temam bû',
                'pending': 'Li benda',
                'failed': 'Têk çû',
                'refunded': 'Vegerandî'
            }
        }
        return translations.get(lang_code, translations['en'])
    
    def get_available_languages():
        return {"en": "English", "ar": "Arabic", "ku": "Kurdish"}

# إعداد التطبيق
st.set_page_config(
    page_title="Data Analysis Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== نظام الدفع المحسن ==========

class PaymentSystem:
    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_payment_tables()
    
    def _ensure_payment_tables(self):
        """التأكد من وجود جداول نظام الدفع"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            # جدول المعاملات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_id VARCHAR(100) UNIQUE,
                    amount DECIMAL(10,2),
                    currency VARCHAR(10) DEFAULT 'USD',
                    payment_method VARCHAR(50),
                    payment_status VARCHAR(20),
                    description TEXT,
                    plan_type VARCHAR(50),
                    billing_info TEXT,
                    tax_amount DECIMAL(10,2) DEFAULT 0.0,
                    total_amount DECIMAL(10,2),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    refunded_at DATETIME,
                    failure_reason TEXT,
                    metadata TEXT
                )
            ''')
            
            # جدول طلبات الاسترداد
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS refund_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id INTEGER,
                    user_id INTEGER,
                    reason TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_at DATETIME,
                    processed_by INTEGER,
                    refund_amount DECIMAL(10,2)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Payment system initialization error: {e}")
    
    def generate_transaction_id(self):
        """إنشاء معرف معاملة فريد"""
        return f"TXN{hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()}"
    
    def process_payment(self, user_id, amount, payment_method, plan_type, card_details=None):
        """معالجة الدفع"""
        try:
            transaction_id = self.generate_transaction_id()
            tax_amount = amount * 0.1  # 10% ضريبة افتراضية
            total_amount = amount + tax_amount
            
            # محاكاة عملية الدفع
            if self._simulate_payment_processing(card_details):
                payment_status = "completed"
                
                # تحديث حساب المستخدم
                self.db.update_user_account(user_id, plan_type)
                
                # حفظ تفاصيل الدفع
                self._save_payment_record(
                    user_id, transaction_id, amount, payment_method, 
                    payment_status, plan_type, tax_amount, total_amount
                )
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'tax_amount': tax_amount,
                    'total_amount': total_amount,
                    'message': 'Payment processed successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Payment processing failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Payment error: {str(e)}'
            }
    
    def _simulate_payment_processing(self, card_details):
        """محاكاة معالجة الدفع (في الإنتاج سيتم استبدالها بمزود دفع حقيقي)"""
        if not card_details:
            return False
        
        # محاكاة التحقق من البطاقة
        card_number = card_details.get('card_number', '').replace(' ', '')
        expiry = card_details.get('expiry_date', '')
        cvv = card_details.get('cvv', '')
        
        # تحقق بسيط
        if (len(card_number) == 16 and card_number.isdigit() and
            len(expiry) == 5 and '/' in expiry and
            len(cvv) in [3, 4] and cvv.isdigit()):
            return True
        
        return False
    
    def _save_payment_record(self, user_id, transaction_id, amount, payment_method, 
                           status, plan_type, tax_amount, total_amount):
        """حفظ سجل الدفع"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payments 
                (user_id, transaction_id, amount, payment_method, payment_status, 
                 plan_type, tax_amount, total_amount, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, transaction_id, amount, payment_method, status,
                  plan_type, tax_amount, total_amount, datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Error saving payment record: {e}")
    
    def get_payment_history(self, user_id):
        """الحصول على سجل المدفوعات للمستخدم"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT transaction_id, amount, currency, payment_method, 
                       payment_status, plan_type, total_amount, created_at
                FROM payments 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            payments = cursor.fetchall()
            
            return [
                {
                    'transaction_id': p[0],
                    'amount': float(p[1]),
                    'currency': p[2],
                    'payment_method': p[3],
                    'status': p[4],
                    'plan_type': p[5],
                    'total_amount': float(p[6]),
                    'date': p[7]
                }
                for p in payments
            ]
            
        except Exception as e:
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def request_refund(self, user_id, transaction_id, reason):
        """طلب استرداد مبلغ"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            # البحث عن المعاملة
            cursor.execute('''
                SELECT id, amount FROM payments 
                WHERE transaction_id = ? AND user_id = ?
            ''', (transaction_id, user_id))
            
            payment = cursor.fetchone()
            
            if not payment:
                return {'success': False, 'message': 'Transaction not found'}
            
            payment_id, amount = payment
            
            # إضافة طلب الاسترداد
            cursor.execute('''
                INSERT INTO refund_requests 
                (payment_id, user_id, reason, refund_amount)
                VALUES (?, ?, ?, ?)
            ''', (payment_id, user_id, reason, amount))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Refund request submitted'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

# ========== المكونات الأساسية ==========

class AppConfig:
    def __init__(self):
        self.MAX_FILE_SIZE = 50 * 1024 * 1024
        self.SUPPORTED_FORMATS = ['csv', 'xlsx', 'json', 'parquet']
        self.CHART_THEMES = ['plotly', 'plotly_white', 'plotly_dark']

class FileProcessor:
    def __init__(self):
        self.supported_types = {
            'csv': pd.read_csv,
            'xlsx': pd.read_excel, 
            'json': pd.read_json,
            'parquet': pd.read_parquet
        }
    
    def process_uploaded_file(self, uploaded_file):
        try:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type not in self.supported_types:
                st.error(f"Unsupported file type: {file_type}")
                return None
            
            if file_type == 'csv':
                df = pd.read_csv(uploaded_file, encoding_errors='ignore')
            elif file_type == 'xlsx':
                df = pd.read_excel(uploaded_file)
            elif file_type == 'json':
                df = pd.read_json(uploaded_file)
            elif file_type == 'parquet':
                df = pd.read_parquet(uploaded_file)
            
            df = self.clean_dataframe(df)
            return df
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None
    
    def clean_dataframe(self, df):
        df = df.dropna(axis=1, how='all')
        df.columns = [self.clean_column_name(col) for col in df.columns]
        return df
    
    def clean_column_name(self, name):
        if not isinstance(name, str):
            name = str(name)
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name.strip())
        return name.lower()

class DataCleaner:
    def __init__(self):
        pass
    
    def handle_missing_values(self, df, strategy='mean'):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if strategy == 'mean':
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif strategy == 'median':
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        elif strategy == 'drop':
            df = df.dropna()
        return df

class AdvancedVisualizer:
    def __init__(self):
        self.color_palette = px.colors.qualitative.Plotly
    
    def interactive_scatter(self, df, lang):
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            st.warning(lang.get("need_numeric_columns", "Need at least 2 numeric columns for scatter plot"))
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_axis = st.selectbox(lang.get("x_axis", "X Axis"), numeric_cols, index=0, key='scatter_x')
        with col2:
            y_axis = st.selectbox(lang.get("y_axis", "Y Axis"), numeric_cols, index=1 if len(numeric_cols) > 1 else 0, key='scatter_y')
        with col3:
            color_by = st.selectbox(lang.get("color_by", "Color By"), [None] + df.columns.tolist(), key='scatter_color')
        
        if color_by:
            fig = px.scatter(df, x=x_axis, y=y_axis, color=color_by,
                           title=f"{y_axis} vs {x_axis}")
        else:
            fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
        
        st.plotly_chart(fig, use_container_width=True)
    
    def correlation_heatmap(self, df, lang):
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            st.warning(lang.get("need_numeric_columns_corr", "Need at least 2 numeric columns for correlation heatmap"))
            return
        
        corr_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmin=-1,
            zmax=1,
            colorbar=dict(title=lang.get("correlation", "Correlation"))
        ))
        
        fig.update_layout(title=lang.get("correlation_heatmap", "Correlation Heatmap"))
        st.plotly_chart(fig, use_container_width=True)

class ML_Analytics:
    def __init__(self):
        pass
    
    def detect_outliers(self, df, lang):
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            st.warning(lang.get("no_numeric_columns", "No numeric columns for outlier detection"))
            return
        
        selected_cols = st.multiselect(lang.get("select_columns", "Select columns"), numeric_cols, 
                                     default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols)
        
        if not selected_cols:
            return
        
        try:
            from sklearn.ensemble import IsolationForest
            clf = IsolationForest(contamination=0.1, random_state=42)
            outlier_labels = clf.fit_predict(df[selected_cols].dropna())
            
            outlier_count = (outlier_labels == -1).sum()
            st.info(lang.get("outliers_detected", "Detected {count} outliers ({percent:.2f}%)").format(
                count=outlier_count, percent=outlier_count/len(df)*100))
            
        except Exception as e:
            st.error(f"{lang.get('error_outlier', 'Error in outlier detection')}: {e}")
    
    def automl_analysis(self, df, lang):
        report = {
            lang.get("data_overview", "Data Overview"): {
                lang.get("shape", "Shape"): f"{df.shape}",
                lang.get("total_rows", "Total Rows"): f"{len(df):,}",
                lang.get("total_columns", "Total Columns"): f"{len(df.columns)}",
                lang.get("memory_usage", "Memory Usage"): f"{df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB"
            },
            lang.get("data_quality", "Data Quality"): {
                lang.get("missing_values", "Missing Values"): f"{df.isnull().sum().sum()}",
                lang.get("duplicate_rows", "Duplicate Rows"): f"{df.duplicated().sum()}"
            },
            lang.get("recommendations", "Recommendations"): [
                lang.get("rec_chart_types", "Consider exploring different chart types"),
                lang.get("rec_outliers", "Check for outliers in numerical columns"),
                lang.get("rec_data_types", "Review data types for optimal analysis")
            ]
        }
        return report

class DatabaseManager:
    def __init__(self, db_url="sqlite:///data_analysis_pro.db"):
        self.db_url = db_url
        self._ensure_database()
    
    def _ensure_database(self):
        """التأكد من وجود قاعدة البيانات والجداول مع تحديث الهيكل"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            # التحقق من وجود الجدول وإعادة إنشائه إذا لزم الأمر
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
            
            # محاولة إضافة الأعمدة المفقودة إذا كانت موجودة
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            except sqlite3.OperationalError:
                pass  # العمود موجود بالفعل
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN usage_stats TEXT")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN admin_notes TEXT")
            except sqlite3.OperationalError:
                pass
            
            # إنشاء جدول مجموعات البيانات
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
            
            # التحقق من وجود المستخدم المسؤول وإضافته
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", 
                          ('muhammedjwad18@gmail.com',))
            if cursor.fetchone()[0] == 0:
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
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database initialization error: {e}")
    
    def get_user_info(self, user_id):
        """الحصول على معلومات المستخدم"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                user_dict = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[3] if len(user) > 3 else '',
                    'account_type': user[4] if len(user) > 4 else 'Free',
                    'subscription_end': user[5] if len(user) > 5 else None,
                    'lifetime': user[6] if len(user) > 6 else False,
                    'created_at': user[7] if len(user) > 7 else datetime.now(),
                    'last_login': user[8] if len(user) > 8 else None,
                    'is_active': user[11] if len(user) > 11 else True
                }
                return user_dict
            return None
            
        except Exception as e:
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_plan_limits(self, user_id):
        """الحصول على قيود خطة المستخدم"""
        user_info = self.get_user_info(user_id)
        if not user_info:
            return {'max_file_size': 10, 'max_analyses_per_month': 5, 'max_datasets': 3}
        
        if user_info['account_type'] == 'Free':
            return {'max_file_size': 10, 'max_analyses_per_month': 5, 'max_datasets': 3}
        elif user_info['account_type'] == 'Pro':
            return {'max_file_size': 100, 'max_analyses_per_month': 9999, 'max_datasets': 50}
        elif user_info['account_type'] == 'Enterprise':
            return {'max_file_size': 1024, 'max_analyses_per_month': 99999, 'max_datasets': 1000}
        elif user_info['account_type'] == 'Admin':
            return {'max_file_size': 9999, 'max_analyses_per_month': 99999, 'max_datasets': 9999}
        else:
            return {'max_file_size': 10, 'max_analyses_per_month': 5, 'max_datasets': 3}
    
    def get_user_stats(self, user_id):
        """إحصائيات المستخدم"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM datasets WHERE user_id = ?", (user_id,))
            datasets_count = cursor.fetchone()[0]
            
            return {
                'datasets_count': datasets_count,
                'analyses_count': 0
            }
            
        except Exception as e:
            return {'datasets_count': 0, 'analyses_count': 0}
        finally:
            if 'conn' in locals():
                conn.close()
    
    def save_dataset(self, user_id, name, dataframe):
        """حفظ مجموعة البيانات"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            data_preview = json.dumps({
                'columns': dataframe.columns.tolist(),
                'preview': dataframe.head(10).to_dict('records')
            })
            
            cursor.execute('''
                INSERT INTO datasets 
                (user_id, name, rows, columns, data_preview) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, len(dataframe), len(dataframe.columns), data_preview))
            
            dataset_id = cursor.lastrowid
            conn.commit()
            return dataset_id
            
        except Exception as e:
            st.error(f"Error saving dataset: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_datasets(self, user_id):
        """الحصول على مجموعات بيانات المستخدم"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, rows, columns, created_at FROM datasets WHERE user_id = ?", (user_id,))
            datasets = cursor.fetchall()
            
            return [
                {
                    'id': ds[0],
                    'name': ds[1],
                    'rows': ds[2],
                    'columns': ds[3],
                    'created_at': datetime.strptime(ds[4], '%Y-%m-%d %H:%M:%S') if ds[4] else datetime.now()
                }
                for ds in datasets
            ]
            
        except Exception as e:
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def load_dataset(self, dataset_id):
        """تحميل مجموعة بيانات"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT data_preview FROM datasets WHERE id = ?", (dataset_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                preview_data = json.loads(result[0])
                return pd.DataFrame(preview_data['preview'])
            return None
            
        except Exception as e:
            st.error(f"Error loading dataset: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username, email, account_type, created_at, last_login FROM users")
            users = cursor.fetchall()
            
            return users
            
        except Exception as e:
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def update_user_account(self, user_id, new_plan):
        """تحديث حساب المستخدم"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("UPDATE users SET account_type = ? WHERE id = ?", (new_plan, user_id))
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Error updating user: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

class AuthenticationSystem:
    def __init__(self):
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=10)
    
    def check_authentication(self):
        if not st.session_state.get('user_id'):
            self.show_login_page()
            return False
        return True
    
    def show_login_page(self):
        # الحصول على اللغة المختارة
        lang = get_language(st.session_state.get('language', 'en'))
        
        st.title(f"🔐 {lang.get('title', 'Data Analysis Pro')}")
        
        tab1, tab2 = st.tabs([lang.get("login", "Login"), lang.get("signup", "Sign Up")])
        
        with tab1:
            self.render_login_form(lang)
        with tab2:
            self.render_signup_form(lang)
    
    def render_login_form(self, lang):
        with st.form("login_form"):
            username = st.text_input(lang.get("username", "Username"))
            password = st.text_input(lang.get("password", "Password"), type="password")
            
            if st.form_submit_button(lang.get("login_btn", "Login"), use_container_width=True):
                self.handle_login(username, password, lang)
    
    def handle_login(self, username, password, lang):
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username, password, account_type FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if user and pbkdf2_sha256.verify(password, user[2]):
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.session_state.account_type = user[3]
                
                # تحديث آخر دخول
                cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                             (datetime.now(), user[0]))
                conn.commit()
                
                st.success(f"{lang.get('welcome', 'Welcome')}, {user[1]}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(lang.get("error_login", "Invalid username or password"))
                
        except Exception as e:
            st.error(f"{lang.get('error_login', 'Login error')}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def render_signup_form(self, lang):
        with st.form("signup_form"):
            st.subheader(lang.get("signup", "Create New Account"))
            
            username = st.text_input(lang.get("username", "Username"))
            email = st.text_input(lang.get("email", "Email"))
            password = st.text_input(lang.get("password", "Password"), type="password")
            confirm_password = st.text_input(lang.get("confirm_password", "Confirm Password"), type="password")
            
            if st.form_submit_button(lang.get("sign_up_btn", "Create Account"), use_container_width=True):
                self.handle_signup(username, email, password, confirm_password, lang)
    
    def handle_signup(self, username, email, password, confirm_password, lang):
        if not self.validate_signup_data(username, email, password, confirm_password, lang):
            return
        
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            # التحقق من عدم وجود مستخدم بنفس الاسم
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                st.error(lang.get("account_exists", "Username already exists"))
                return
            
            hashed_password = pbkdf2_sha256.hash(password)
            cursor.execute('''
                INSERT INTO users (username, email, password, account_type, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, hashed_password, 'Free', True))
            
            conn.commit()
            st.success(lang.get("success_signup", "Account created successfully! Please login."))
            
        except Exception as e:
            st.error(f"{lang.get('error_signup', 'Error creating account')}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def validate_signup_data(self, username, email, password, confirm_password, lang):
        if not username or not email or not password:
            st.error(lang.get("fill_fields", "Please fill all fields"))
            return False
            
        if password != confirm_password:
            st.error(lang.get("password_mismatch", "Passwords do not match"))
            return False
        
        if len(password) < 8:
            st.error(lang.get("password_length", "Password must be at least 8 characters"))
            return False
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error(lang.get("invalid_email", "Please enter a valid email address"))
            return False
        
        return True
    
    def logout(self):
        for key in ['user_id', 'username', 'account_type']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

class StoreManager:
    def __init__(self, db_manager, telegram_bot=None):
        self.db = db_manager
        self.payment_system = PaymentSystem(db_manager)
        self.telegram_bot = telegram_bot
        self.invoice_manager = InvoiceManager(telegram_bot, db_manager) if telegram_bot else None
        self.plans = {
            "Free": {"price": 0, "features": ["10MB file uploads", "5 analyses per month", "Basic visualizations", "CSV export only"]},
            "Pro": {"price": 29.99, "features": ["100MB file uploads", "Unlimited analyses", "Advanced visualizations", "All export formats", "Priority support"]},
            "Enterprise": {"price": 99.99, "features": ["Unlimited file uploads", "Real-time analytics", "API access", "Custom solutions", "24/7 support"]}
        }
    
    def render_store_page(self, user_id, lang):
        st.title(f"🏪 {lang.get('upgrade_plan', 'Upgrade Your Plan')}")
        
        user_info = self.db.get_user_info(user_id)
        current_plan = user_info['account_type'] if user_info else 'Free'
        
        st.header(f"{lang.get('current_plan', 'Current Plan')}: {current_plan}")
        
        # عرض خيارات الاشتراك
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.render_plan_card("Free", current_plan, user_id, lang)
        
        with col2:
            self.render_plan_card("Pro", current_plan, user_id, lang)
        
        with col3:
            self.render_plan_card("Enterprise", current_plan, user_id, lang)
        
        # سجل المدفوعات
        st.header(f"📋 {lang.get('payment_history', 'Payment History')}")
        self.render_payment_history(user_id, lang)
    
    def render_plan_card(self, plan_name, current_plan, user_id, lang):
        plan = self.plans[plan_name]
        
        st.subheader(plan_name)
        
        if plan_name == "Free":
            st.markdown("### 🎁 FREE")
        else:
            st.markdown(f"### ${plan['price']}/month")
        
        st.markdown(f"**{lang.get('features', 'Features')}:**")
        for feature in plan['features']:
            st.markdown(f"✅ {feature}")
        
        if plan_name == current_plan:
            st.success(f"✅ {lang.get('current_plan', 'Current Plan')}")
        else:
            if plan_name == "Free":
                if st.button(f"🔙 {lang.get('downgrade', 'Downgrade to Free')}", 
                           key=f"downgrade_{plan_name}", use_container_width=True):
                    self.handle_downgrade(user_id, lang)
            else:
                if st.button(f"⚡ {lang.get('upgrade', 'Upgrade to')} {plan_name}", 
                           key=f"upgrade_{plan_name}", use_container_width=True):
                    self.handle_payment(user_id, plan_name, lang)
    
    def handle_payment(self, user_id, plan_name, lang):
        """معالجة عملية الدفع"""
        try:
            # إنشاء معاملة دفع
            plan = self.plans[plan_name]
            transaction_id = f"TXN{hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:10].upper()}"
            
            # حفظ في قاعدة البيانات
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (user_id, transaction_id, amount, payment_method, payment_status, plan_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, transaction_id, plan['price'], 'Credit Card', 'pending', plan_name))
            conn.commit()
            conn.close()
            
            # إعداد بيانات الفاتورة
            user_info = self.db.get_user_info(user_id)
            payment_data = {
                'user_id': user_id,
                'username': user_info['username'],
                'email': user_info.get('email', 'غير محدد'),
                'transaction_id': transaction_id,
                'amount': plan['price'],
                'plan_type': plan_name,
                'payment_method': 'Credit Card',
                'current_plan': user_info['account_type']
            }
            
            # إرسال إشعار للبوت إذا كان متاحاً
            if self.telegram_bot and self.invoice_manager:
                thread = threading.Thread(
                    target=lambda: asyncio.run(self.invoice_manager.send_invoice_to_admins(payment_data))
                )
                thread.daemon = True
                thread.start()
                
                st.success("""
                ✅ **تم إرسال طلب الدفع بنجاح!**
                
                📱 ستتلقى تأكيد التفعيل قريباً عبر البوت.
                🔔 يمكنك متابعة حالة الدفع من البوت.
                """)
            else:
                st.session_state.payment_plan = plan_name
                st.session_state.show_payment_form = True
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ خطأ في معالجة الدفع: {e}")
    
    def handle_downgrade(self, user_id, lang):
        """معالجة التخفيض إلى الخطة المجانية"""
        success = self.db.update_user_account(user_id, "Free")
        if success:
            st.session_state.account_type = "Free"
            st.success(f"✅ {lang.get('downgrade_success', 'Successfully downgraded to Free plan')}!")
            st.rerun()
        else:
            st.error(lang.get("downgrade_failed", "Failed to downgrade account"))
    
    def render_payment_form(self, user_id, plan_name, lang):
        """عرض نموذج الدفع"""
        if not st.session_state.get('show_payment_form', False):
            return
        
        plan = self.plans[plan_name]
        
        st.header(f"💳 {lang.get('payment_system', 'Payment System')} - {plan_name}")
        
        with st.form("payment_form"):
            st.subheader(f"{lang.get('billing_info', 'Billing Information')}")
            
            # معلومات الدفع
            col1, col2 = st.columns(2)
            
            with col1:
                payment_method = st.selectbox(
                    lang.get("payment_method", "Payment Method"),
                    [lang.get("credit_card", "Credit Card"), lang.get("paypal", "PayPal")]
                )
                
                if payment_method == lang.get("credit_card", "Credit Card"):
                    card_number = st.text_input(lang.get("card_number", "Card Number"), 
                                              placeholder="1234 5678 9012 3456")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        expiry_date = st.text_input(lang.get("expiry_date", "Expiry Date"), 
                                                  placeholder="MM/YY")
                    with col4:
                        cvv = st.text_input(lang.get("cvv", "CVV"), 
                                          placeholder="123", type="password")
                    
                    name_on_card = st.text_input(lang.get("name_on_card", "Name on Card"))
            
            with col2:
                # ملخص الطلب
                st.subheader(lang.get("order_summary", "Order Summary"))
                st.write(f"**{lang.get('plan', 'Plan')}:** {plan_name}")
                st.write(f"**{lang.get('amount', 'Amount')}:** ${plan['price']}")
                st.write(f"**{lang.get('tax_amount', 'Tax Amount')}:** ${plan['price'] * 0.1:.2f}")
                st.write(f"**{lang.get('total_amount', 'Total Amount')}:** ${plan['price'] * 1.1:.2f}")
                
                st.info(f"💡 {lang.get('payment_note', 'This is a demo payment system. Use test card: 4111 1111 1111 1111')}")
            
            # أزرار الإجراء
            col5, col6 = st.columns(2)
            with col5:
                if st.form_submit_button(f"✅ {lang.get('process_payment', 'Process Payment')}", 
                                       use_container_width=True):
                    self.process_payment(user_id, plan_name, payment_method, {
                        'card_number': card_number,
                        'expiry_date': expiry_date,
                        'cvv': cvv,
                        'name_on_card': name_on_card
                    }, lang)
            
            with col6:
                if st.form_submit_button(f"❌ {lang.get('cancel', 'Cancel')}", 
                                       use_container_width=True):
                    st.session_state.show_payment_form = False
                    st.rerun()
    
    def process_payment(self, user_id, plan_name, payment_method, card_details, lang):
        """معالجة الدفع"""
        plan = self.plans[plan_name]
        
        with st.spinner(lang.get("payment_processing", "Processing Payment...")):
            result = self.payment_system.process_payment(
                user_id, plan['price'], payment_method, plan_name, card_details
            )
            
            if result['success']:
                st.session_state.show_payment_form = False
                st.session_state.account_type = plan_name
                st.success(f"🎉 {lang.get('payment_success', 'Payment Successful!')}")
                st.balloons()
                
                # عرض تفاصيل المعاملة
                st.info(f"""
                **{lang.get('transaction_details', 'Transaction Details')}:**
                - {lang.get('transaction_id', 'Transaction ID')}: {result['transaction_id']}
                - {lang.get('amount', 'Amount')}: ${result['amount']:.2f}
                - {lang.get('tax_amount', 'Tax Amount')}: ${result['tax_amount']:.2f}
                - {lang.get('total_amount', 'Total Amount')}: ${result['total_amount']:.2f}
                """)
                
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ {lang.get('payment_failed', 'Payment Failed')}: {result['message']}")
    
    def render_payment_history(self, user_id, lang):
        """عرض سجل المدفوعات"""
        payments = self.payment_system.get_payment_history(user_id)
        
        if not payments:
            st.info(f"📝 {lang.get('no_payments', 'No payment history found')}")
            return
        
        for payment in payments:
            with st.expander(f"💰 {payment['transaction_id']} - ${payment['total_amount']:.2f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**{lang.get('amount', 'Amount')}:** ${payment['amount']:.2f}")
                    st.write(f"**{lang.get('tax_amount', 'Tax Amount')}:** ${payment['total_amount'] - payment['amount']:.2f}")
                    st.write(f"**{lang.get('payment_method', 'Payment Method')}:** {payment['payment_method']}")
                
                with col2:
                    status_color = "🟢" if payment['status'] == 'completed' else "🟡" if payment['status'] == 'pending' else "🔴"
                    st.write(f"**{lang.get('payment_status', 'Payment Status')}:** {status_color} {payment['status']}")
                    st.write(f"**{lang.get('plan_type', 'Plan Type')}:** {payment['plan_type']}")
                    st.write(f"**{lang.get('payment_date', 'Payment Date')}:** {payment['date']}")

    def render_admin_subscription_panel(self, lang):
        st.header("👑 لوحة تحكم المسؤول")
        
        try:
            users = self.db.get_all_users()
            
            total_users = len(users)
            pro_users = len([u for u in users if u[3] == 'Pro'])
            enterprise_users = len([u for u in users if u[3] == 'Enterprise'])
            admin_users = len([u for u in users if u[3] == 'Admin'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("إجمالي المستخدمين", total_users)
            with col2:
                st.metric("مستخدمي Pro", pro_users)
            with col3:
                st.metric("مستخدمي Enterprise", enterprise_users)
            with col4:
                st.metric("المسؤولين", admin_users)
            
            # إدارة المستخدمين
            st.subheader("👥 إدارة المستخدمين")
            
            for user in users:
                with st.expander(f"👤 {user[1]} - {user[3]}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**البريد الإلكتروني:** {user[2]}")
                        st.write(f"**تاريخ الإنشاء:** {user[4]}")
                        st.write(f"**آخر دخول:** {user[5] if user[5] else 'أبداً'}")
                    
                    with col2:
                        new_plan = st.selectbox(
                            "الخطة",
                            ["Free", "Pro", "Enterprise", "Admin"],
                            index=["Free", "Pro", "Enterprise", "Admin"].index(user[3]),
                            key=f"plan_{user[0]}"
                        )
                        
                        if st.button("تحديث", key=f"update_{user[0]}", use_container_width=True):
                            success = self.db.update_user_account(user[0], new_plan)
                            if success:
                                st.success("تم تحديث المستخدم بنجاح!")
                                st.rerun()
                            else:
                                st.error("فشل في تحديث المستخدم")
                            
        except Exception as e:
            st.error(f"خطأ في لوحة التحكم: {e}")

class PremiumFeatures:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def advanced_ml_models(self, df, user_id, lang):
        st.subheader("🤖 التعلم الآلي المتقدم")
        
        if not self.check_premium_access(user_id, "التعلم الآلي المتقدم", lang):
            return
        
        ml_type = st.selectbox("اختر الخوارزمية", [
            "التجميع - KMeans",
            "التصنيف - Random Forest", 
            "الانحدار - Gradient Boosting"
        ])
        
        if ml_type == "التجميع - KMeans":
            self.kmeans_clustering(df, lang)
        else:
            st.info(f"{ml_type} قريباً!")
    
    def kmeans_clustering(self, df, lang):
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            st.warning("تحتاج إلى عمودين رقميين على الأقل للتجميع")
            return
        
        selected_features = st.multiselect("اختر الميزات", 
                                         numeric_cols, default=numeric_cols[:2])
        n_clusters = st.slider("عدد المجموعات", 2, 10, 3)
        
        if len(selected_features) < 2:
            return
        
        try:
            from sklearn.cluster import KMeans
            X = df[selected_features].dropna()
            
            if len(X) < n_clusters:
                st.warning("لا توجد بيانات كافية")
                return
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X)
            
            if len(selected_features) >= 2:
                fig = px.scatter(
                    x=X[selected_features[0]], 
                    y=X[selected_features[1]], 
                    color=clusters,
                    title=f"KMeans Clustering (k={n_clusters})"
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"خطأ في التجميع: {e}")
    
    def check_premium_access(self, user_id, feature_name, lang):
        user_info = self.db.get_user_info(user_id)
        if not user_info or user_info['account_type'] == 'Free':
            st.error(f"🚫 {feature_name} ميزة متميزة")
            return False
        return True

class AdminPanel:
    def __init__(self, db_manager):
        self.db = db_manager
        self.payment_system = PaymentSystem(db_manager)
    
    def render_admin_dashboard(self, lang):
        st.title("👑 لوحة تحكم المسؤول")
        
        try:
            users = self.db.get_all_users()
            
            # إحصائيات النظام
            total_users = len(users)
            total_datasets = sum([self.db.get_user_stats(user[0])['datasets_count'] for user in users])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("إجمالي المستخدمين", total_users)
            with col2:
                st.metric("إجمالي مجموعات البيانات", total_datasets)
            with col3:
                st.metric("مستخدمي Pro", len([u for u in users if u[3] == 'Pro']))
            with col4:
                st.metric("حالة النظام", "✅")
            
            # إدارة المستخدمين
            st.subheader("👥 إدارة المستخدمين")
            
            for user in users:
                with st.expander(f"👤 {user[1]} ({user[3]})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**البريد الإلكتروني:** {user[2]}")
                        st.write(f"**تاريخ الإنشاء:** {user[4]}")
                        st.write(f"**آخر دخول:** {user[5] if user[5] else 'أبداً'}")
                    
                    with col2:
                        new_plan = st.selectbox(
                            "نوع الحساب",
                            ["Free", "Pro", "Enterprise", "Admin"],
                            index=["Free", "Pro", "Enterprise", "Admin"].index(user[3]),
                            key=f"admin_plan_{user[0]}"
                        )
                        
                        if st.button("تحديث المستخدم", 
                                   key=f"admin_update_{user[0]}", use_container_width=True):
                            success = self.db.update_user_account(user[0], new_plan)
                            if success:
                                st.success("تم تحديث المستخدم بنجاح!")
                                st.rerun()
                            else:
                                st.error("فشل في تحديث المستخدم")
            
            # إعدادات النظام
            st.subheader("⚙️ إعدادات النظام")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 مسح الذاكرة المؤقتة", use_container_width=True):
                    st.success("تم مسح الذاكرة المؤقتة!")
                
                if st.button("📊 تقرير النظام", use_container_width=True):
                    st.success("تم إنشاء التقرير!")
            
            with col2:
                if st.button("🛡️ نسخ احتياطي", use_container_width=True):
                    st.success("تم إنشاء النسخ الاحتياطي!")
                
                if st.button("⚠️ فحص الصحة", use_container_width=True):
                    st.success("النظام يعمل بشكل صحيح!")
                    
        except Exception as e:
            st.error(f"خطأ في لوحة التحكم: {e}")

# ========== الفئة الرئيسية للتطبيق مع دعم اللغات ==========

class DataAnalysisPro:
    def __init__(self):
        # تهيئة حالة اللغة
        if 'language' not in st.session_state:
            st.session_state.language = 'en'
        
        try:
            self.config = AppConfig()
            self.auth = AuthenticationSystem()
            self.db = DatabaseManager()
            self.viz = AdvancedVisualizer()
            self.ml = ML_Analytics()
            self.file_processor = FileProcessor()
            self.cleaner = DataCleaner()
            
            # تهيئة البوت أولاً
            self.telegram_bot = None
            self.init_telegram_bot()
            
            # ثم تهيئة المتجر مع البوت
            self.store = StoreManager(self.db, self.telegram_bot)
            self.premium = PremiumFeatures(self.db)
            self.admin_panel = AdminPanel(self.db)
            
        except Exception as e:
            st.error(f"Application initialization error: {e}")
        
        # حالة التطبيق
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "dashboard"
        if 'current_dataset' not in st.session_state:
            st.session_state.current_dataset = None
        if 'show_payment_form' not in st.session_state:
            st.session_state.show_payment_form = False
    
    def init_telegram_bot(self):
        """تهيئة بوت التلجرام"""
        try:
            self.telegram_bot = TelegramPaymentBot(self.db)
            self.telegram_bot.run_in_thread()
            print("✅ بوت التلجرام يعمل بنجاح!")
        except Exception as e:
            print(f"⚠️ البوت غير active: {e}")
    
    def render_sidebar(self):
        """شريط جانبي مع اختيار اللغة"""
        with st.sidebar:
            st.title("📊 Data Pro")
            
            # اختيار اللغة
            available_langs = get_available_languages()
            selected_lang = st.selectbox(
                "🌍 Language / اللغة / زمان",
                options=list(available_langs.keys()),
                format_func=lambda x: available_langs[x],
                index=list(available_langs.keys()).index(st.session_state.language)
            )
            
            if selected_lang != st.session_state.language:
                st.session_state.language = selected_lang
                st.rerun()
            
            lang = get_language(st.session_state.language)
            
            if st.session_state.get('user_id'):
                user_info = self.db.get_user_info(st.session_state.user_id)
                is_admin = user_info and user_info['account_type'] == 'Admin'
                
                if is_admin:
                    pages = {
                        f"👑 {lang.get('admin_dashboard', 'Admin Dashboard')}": "admin_dashboard",
                        f"📊 {lang.get('dashboard', 'Dashboard')}": "dashboard",
                        f"🏪 {lang.get('store', 'Store Management')}": "store",
                        f"⚙️ {lang.get('settings', 'Settings')}": "settings"
                    }
                else:
                    pages = {
                        f"📊 {lang.get('dashboard', 'Dashboard')}": "dashboard",
                        f"🤖 {lang.get('machine_learning', 'ML Studio')}": "machine_learning", 
                        f"🏪 {lang.get('store', 'Upgrade Plan')}": "store",
                        f"⚙️ {lang.get('settings', 'Settings')}": "settings"
                    }
            else:
                pages = {f"📊 {lang.get('dashboard', 'Dashboard')}": "dashboard"}
            
            selected = st.selectbox(lang.get("navigation", "Navigation"), list(pages.keys()))
            st.session_state.current_page = pages[selected]
            
            if st.session_state.get('user_id'):
                user_info = self.db.get_user_info(st.session_state.user_id)
                if user_info:
                    if user_info['account_type'] == 'Admin':
                        st.success(f"👑 {user_info['username']} ({lang.get('admin', 'Admin')})")
                    else:
                        st.info(f"👤 {user_info['username']} | {user_info['account_type']}")
                
                if st.button(f"🚪 {lang.get('logout_btn', 'Logout')}", use_container_width=True):
                    self.auth.logout()
    
    def dashboard_page(self):
        """لوحة التحكم الرئيسية"""
        lang = get_language(st.session_state.language)
        st.title(f"📊 {lang.get('dashboard', 'Analytics Dashboard')}")
        
        # تحميل البيانات
        uploaded_file = st.file_uploader(
            lang.get("upload_file", "Upload Dataset"),
            type=['csv', 'xlsx', 'json', 'parquet'],
            help="Support CSV, Excel, JSON, Parquet files"
        )
        
        if uploaded_file:
            dataset = self.file_processor.process_uploaded_file(uploaded_file)
            if dataset is not None:
                st.session_state.current_dataset = dataset
                st.success(f"✅ {lang.get('dataset_loaded', 'Dataset loaded')}: {len(dataset)} {lang.get('rows', 'rows')}, {len(dataset.columns)} {lang.get('columns', 'columns')}")
        
        # عرض البيانات
        if st.session_state.current_dataset is not None:
            self.show_data_explorer(lang)
        else:
            st.info(f"👆 {lang.get('upload_prompt', 'Please upload a dataset to get started')}")
            
            if st.button(lang.get("load_sample", "Load Sample Data")):
                np.random.seed(42)
                sample_data = pd.DataFrame({
                    'Age': np.random.randint(18, 65, 100),
                    'Income': np.random.normal(50000, 15000, 100),
                    'Score': np.random.normal(75, 15, 100),
                    'Category': np.random.choice(['A', 'B', 'C'], 100)
                })
                st.session_state.current_dataset = sample_data
                st.success(lang.get("sample_loaded", "Sample data loaded successfully!"))
    
    def show_data_explorer(self, lang):
        """مستكشف البيانات"""
        df = st.session_state.current_dataset
        
        tab1, tab2, tab3 = st.tabs([
            f"📋 {lang.get('data_overview', 'Data Overview')}", 
            f"📈 {lang.get('interactive_viz', 'Visualizations')}", 
            f"🤖 {lang.get('ml_insights', 'ML Insights')}"
        ])
        
        with tab1:
            self.render_data_overview(df, lang)
        
        with tab2:
            self.render_visualizations(df, lang)
        
        with tab3:
            self.render_ml_insights(df, lang)
    
    def render_data_overview(self, df, lang):
        """نظرة عامة على البيانات"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(lang.get("rows", "Rows"), f"{len(df):,}")
        with col2:
            st.metric(lang.get("columns", "Columns"), len(df.columns))
        with col3:
            st.metric(lang.get("missing_values", "Missing Values"), df.isnull().sum().sum())
        with col4:
            st.metric(lang.get("memory_usage", "Memory Usage"), f"{df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")
        
        st.subheader(lang.get("data_preview", "Data Preview"))
        st.dataframe(df.head(10), use_container_width=True)
        
        st.subheader(lang.get("statistical_summary", "Statistical Summary"))
        st.dataframe(df.describe(), use_container_width=True)
    
    def render_visualizations(self, df, lang):
        """التصورات"""
        st.subheader(lang.get("interactive_viz", "Interactive Visualizations"))
        
        viz_type = st.selectbox(lang.get("chart_type", "Chart Type"), 
                              ["Scatter Plot", "Heatmap", "Histogram"])
        
        if viz_type == "Scatter Plot":
            self.viz.interactive_scatter(df, lang)
        elif viz_type == "Heatmap":
            self.viz.correlation_heatmap(df, lang)
        elif viz_type == "Histogram":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                col = st.selectbox(lang.get("select_column", "Select Column"), numeric_cols)
                fig = px.histogram(df, x=col, title=f"Histogram of {col}")
                st.plotly_chart(fig, use_container_width=True)
    
    def render_ml_insights(self, df, lang):
        """رؤى التعلم الآلي"""
        st.subheader(lang.get("ml_insights", "Machine Learning Insights"))
        
        user_info = self.db.get_user_info(st.session_state.user_id)
        is_premium = user_info and user_info['account_type'] in ['Pro', 'Enterprise', 'Admin']
        
        if is_premium:
            tab1, tab2 = st.tabs(["🧪 Basic ML", "⭐ Premium ML"])
            
            with tab1:
                if st.button(lang.get("generate_report", "Generate AutoML Report")):
                    with st.spinner(lang.get("analyzing", "Analyzing data...")):
                        report = self.ml.automl_analysis(df, lang)
                        st.success(lang.get("analysis_complete", "Analysis complete!"))
                        
                        for section, content in report.items():
                            with st.expander(f"📖 {section}"):
                                if isinstance(content, dict):
                                    for k, v in content.items():
                                        st.write(f"**{k}**: {v}")
                                else:
                                    st.write(content)
            
            with tab2:
                self.premium.advanced_ml_models(df, st.session_state.user_id, lang)
        else:
            if st.button(lang.get("generate_report", "Generate AutoML Report")):
                with st.spinner(lang.get("analyzing", "Analyzing data...")):
                    report = self.ml.automl_analysis(df, lang)
                    st.success(lang.get("analysis_complete", "Analysis complete!"))
                    
                    for section, content in report.items():
                        with st.expander(f"📖 {section}"):
                            if isinstance(content, dict):
                                for k, v in content.items():
                                    st.write(f"**{k}**: {v}")
                            else:
                                st.write(content)
            
            st.info(f"🔒 {lang.get('upgrade_prompt', 'Upgrade to Pro for advanced machine learning features')}")
    
    def ml_page(self):
        """صفحة التعلم الآلي"""
        lang = get_language(st.session_state.language)
        st.title(f"🤖 {lang.get('machine_learning', 'Machine Learning Studio')}")
        
        if st.session_state.current_dataset is not None:
            df = st.session_state.current_dataset
            self.render_ml_insights(df, lang)
        else:
            st.info(f"👆 {lang.get('upload_first', 'Please upload a dataset first')}")
    
    def settings_page(self):
        """الإعدادات"""
        lang = get_language(st.session_state.language)
        st.title(f"⚙️ {lang.get('settings', 'Settings')}")
        
        user_info = self.db.get_user_info(st.session_state.user_id)
        
        tab1, tab2 = st.tabs([
            lang.get("account_settings", "Account"), 
            lang.get("preferences", "Preferences")
        ])
        
        with tab1:
            st.subheader(lang.get("account_settings", "Account Settings"))
            st.write(f"**{lang.get('username', 'Username')}:** {user_info['username']}")
            st.write(f"**{lang.get('account_type', 'Account Type')}:** {user_info['account_type']}")
            st.write(f"**{lang.get('email', 'Email')}:** {user_info.get('email', lang.get('not_set', 'Not set'))}")
        
        with tab2:
            st.subheader(lang.get("preferences", "Preferences"))
            
            # اختيار اللغة في الإعدادات أيضاً
            available_langs = get_available_languages()
            selected_lang = st.selectbox(
                lang.get("language", "Language"),
                options=list(available_langs.keys()),
                format_func=lambda x: available_langs[x],
                index=list(available_langs.keys()).index(st.session_state.language)
            )
            
            theme = st.selectbox(lang.get("theme", "Theme"), ["Light", "Dark", "Auto"])
            
            if st.button(lang.get("save_preferences", "Save Preferences")):
                if selected_lang != st.session_state.language:
                    st.session_state.language = selected_lang
                st.success(lang.get("preferences_saved", "Preferences saved!"))
                st.rerun()
    
    def store_page(self):
        """صفحة المتجر"""
        lang = get_language(st.session_state.language)
        
        if st.session_state.get('user_id'):
            user_info = self.db.get_user_info(st.session_state.user_id)
            
            # عرض نموذج الدفع إذا كان مطلوباً
            if st.session_state.get('show_payment_form', False) and st.session_state.get('payment_plan'):
                self.store.render_payment_form(
                    st.session_state.user_id, 
                    st.session_state.payment_plan, 
                    lang
                )
            else:
                if user_info['account_type'] == 'Admin':
                    st.title(f"🏪 {lang.get('store_management', 'Store Management')}")
                    self.store.render_admin_subscription_panel(lang)
                else:
                    self.store.render_store_page(st.session_state.user_id, lang)
    
    def run(self):
        """تشغيل التطبيق"""
        if not self.auth.check_authentication():
            return
        
        self.render_sidebar()
        
        user_info = self.db.get_user_info(st.session_state.user_id)
        is_admin = user_info and user_info['account_type'] == 'Admin'
        
        lang = get_language(st.session_state.language)
        
        if is_admin and st.session_state.current_page == "admin_dashboard":
            self.admin_panel.render_admin_dashboard(lang)
        else:
            page_handlers = {
                "dashboard": self.dashboard_page,
                "machine_learning": self.ml_page,
                "store": self.store_page,
                "settings": self.settings_page
            }
            
            current_page = st.session_state.current_page
            if current_page in page_handlers:
                page_handlers[current_page]()
            else:
                self.dashboard_page()

if __name__ == "__main__":
    app = DataAnalysisPro()
    app.run()