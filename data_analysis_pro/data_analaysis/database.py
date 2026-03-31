from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import json
from datetime import datetime, timedelta
import pickle
import base64
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(255))
    email = Column(String(100))
    account_type = Column(String(20), default='Free')
    subscription_end = Column(DateTime)
    lifetime = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    settings = Column(Text)
    usage_stats = Column(Text)  # تم تغيير من JSON إلى Text
    is_active = Column(Boolean, default=True)
    admin_notes = Column(Text)

class Dataset(Base):
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String(255))
    filename = Column(String(500))
    description = Column(Text)
    rows = Column(Integer)
    columns = Column(Integer)
    file_size = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    data_preview = Column(Text)

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    dataset_id = Column(Integer)
    analysis_type = Column(String(100))
    parameters = Column(Text)
    results = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    price_monthly = Column(Float)
    price_yearly = Column(Float)
    features = Column(Text)  # تم تغيير من JSON إلى Text
    limits = Column(Text)    # تم تغيير من JSON إلى Text
    is_active = Column(Boolean, default=True)

class UserSubscription(Base):
    __tablename__ = 'user_subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    plan_id = Column(Integer)
    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    payment_status = Column(String(20), default='pending')

class AdminLog(Base):
    __tablename__ = 'admin_logs'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer)
    action = Column(String(255))
    target_user_id = Column(Integer)
    details = Column(Text)  # تم تغيير من JSON إلى Text
    created_at = Column(DateTime, default=datetime.now)

class DatabaseManager:
    def __init__(self, db_url="sqlite:///data_analysis_pro.db"):
        self.engine = create_engine(db_url)
        self._create_tables()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.init_default_plans()
        self.create_admin_user()
    
    def _create_tables(self):
        """إنشاء الجداول إذا لم تكن موجودة"""
        try:
            Base.metadata.create_all(self.engine)
            print("✅ تم إنشاء/تأكيد جداول قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجداول: {e}")
            # محاولة استخدام التحديث
            self._update_database()
    
    def _update_database(self):
        """تحديث قاعدة البيانات إذا كانت هناك مشاكل"""
        try:
            from database_updater import DatabaseUpdater
            updater = DatabaseUpdater("data_analysis_pro.db")
            if updater.update_database_schema():
                print("✅ تم تحديث قاعدة البيانات بنجاح")
            else:
                print("❌ فشل تحديث قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في تحديث قاعدة البيانات: {e}")
    
    def create_admin_user(self):
        """إنشاء المستخدم المسؤول الافتراضي"""
        try:
            admin_user = self.session.query(User).filter_by(username='muhammedjwad18@gmail.com').first()
            if not admin_user:
                from passlib.hash import pbkdf2_sha256
                hashed_password = pbkdf2_sha256.hash('KINGSMAN238185')
                
                admin_user = User(
                    username='muhammedjwad18@gmail.com',
                    password=hashed_password,
                    email='muhammedjwad18@gmail.com',
                    account_type='Admin',
                    lifetime=True,
                    is_active=True,
                    usage_stats=json.dumps({'analyses_count': 0, 'datasets_count': 0})
                )
                self.session.add(admin_user)
                self.session.commit()
                print("✅ تم إنشاء المستخدم المسؤول بنجاح!")
            else:
                print("✅ المستخدم المسؤول موجود بالفعل")
        except Exception as e:
            print(f"❌ خطأ في إنشاء المستخدم المسؤول: {e}")
            self.session.rollback()
    
    def init_default_plans(self):
        """تهيئة خطط الاشتراك الافتراضية"""
        try:
            plans_data = [
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
            
            for plan_data in plans_data:
                existing = self.session.query(SubscriptionPlan).filter_by(name=plan_data['name']).first()
                if not existing:
                    plan = SubscriptionPlan(**plan_data)
                    self.session.add(plan)
            
            self.session.commit()
            print("✅ تم تهيئة خطط الاشتراك بنجاح")
        except Exception as e:
            print(f"❌ خطأ في تهيئة خطط الاشتراك: {e}")
            self.session.rollback()
    
    def get_user_info(self, user_id):
        """الحصول على معلومات المستخدم مع معالجة الأخطاء"""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if user:
                days_left = None
                if user.subscription_end and not user.lifetime:
                    days_left = (user.subscription_end - datetime.now()).days
                    days_left = max(0, days_left)
                
                return {
                    'username': user.username,
                    'account_type': user.account_type,
                    'subscription_end': user.subscription_end,
                    'days_left': days_left,
                    'email': user.email,
                    'created_at': user.created_at,
                    'last_login': user.last_login
                }
            return None
        except Exception as e:
            print(f"❌ خطأ في الحصول على معلومات المستخدم: {e}")
            return None
    
    def get_user_plan_limits(self, user_id):
        """الحصول على قيود خطة المستخدم"""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                return None
            
            if user.account_type == 'Free':
                plan = self.session.query(SubscriptionPlan).filter_by(name='Free').first()
            elif user.account_type == 'Pro':
                plan = self.session.query(SubscriptionPlan).filter_by(name='Pro').first()
            elif user.account_type == 'Enterprise':
                plan = self.session.query(SubscriptionPlan).filter_by(name='Enterprise').first()
            elif user.account_type == 'Admin':
                # المسؤولين لديهم جميع الصلاحيات
                return {
                    'max_file_size': 9999,
                    'max_analyses_per_month': 99999,
                    'max_datasets': 9999,
                    'export_formats': ['csv', 'excel', 'json', 'pdf', 'html']
                }
            else:
                plan = self.session.query(SubscriptionPlan).filter_by(name='Free').first()
            
            if plan and plan.limits:
                return json.loads(plan.limits)
            return None
        except Exception as e:
            print(f"❌ خطأ في الحصول على قيود الخطة: {e}")
            return {
                'max_file_size': 10,
                'max_analyses_per_month': 5,
                'max_datasets': 3,
                'export_formats': ['csv']
            }
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        try:
            return self.session.query(User).order_by(User.created_at.desc()).all()
        except Exception as e:
            print(f"❌ خطأ في الحصول على المستخدمين: {e}")
            return []
    
    def get_user_stats(self, user_id):
        """إحصائيات المستخدم"""
        try:
            datasets_count = self.session.query(Dataset).filter_by(user_id=user_id).count()
            analyses_count = self.session.query(Analysis).filter_by(user_id=user_id).count()
            
            return {
                'datasets_count': datasets_count,
                'analyses_count': analyses_count
            }
        except Exception as e:
            print(f"❌ خطأ في الحصول على إحصائيات المستخدم: {e}")
            return {'datasets_count': 0, 'analyses_count': 0}
    
    def update_user_account(self, admin_id, target_user_id, account_type, days=None, lifetime=False, notes=None):
        """تحديث حساب المستخدم"""
        try:
            user = self.session.query(User).filter_by(id=target_user_id).first()
            if not user:
                return False, "User not found"
            
            old_type = user.account_type
            user.account_type = account_type
            
            if lifetime:
                user.lifetime = True
                user.subscription_end = None
            elif days is not None:
                user.lifetime = False
                user.subscription_end = datetime.now() + timedelta(days=days)
            
            if notes:
                user.admin_notes = notes
            
            # تسجيل العملية في السجلات
            log = AdminLog(
                admin_id=admin_id,
                action=f"Updated user account: {old_type} -> {account_type}",
                target_user_id=target_user_id,
                details=json.dumps({
                    'old_account_type': old_type,
                    'new_account_type': account_type,
                    'days_added': days,
                    'lifetime': lifetime,
                    'notes': notes
                })
            )
            self.session.add(log)
            self.session.commit()
            
            return True, "User account updated successfully"
        except Exception as e:
            self.session.rollback()
            return False, f"Error: {str(e)}"
    
    def get_system_stats(self):
        """إحصائيات النظام"""
        try:
            total_users = self.session.query(User).count()
            active_users = self.session.query(User).filter_by(is_active=True).count()
            pro_users = self.session.query(User).filter_by(account_type='Pro').count()
            enterprise_users = self.session.query(User).filter_by(account_type='Enterprise').count()
            admin_users = self.session.query(User).filter_by(account_type='Admin').count()
            
            total_datasets = self.session.query(Dataset).count()
            total_analyses = self.session.query(Analysis).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'pro_users': pro_users,
                'enterprise_users': enterprise_users,
                'admin_users': admin_users,
                'total_datasets': total_datasets,
                'total_analyses': total_analyses
            }
        except Exception as e:
            print(f"❌ خطأ في الحصول على إحصائيات النظام: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'pro_users': 0,
                'enterprise_users': 0,
                'admin_users': 0,
                'total_datasets': 0,
                'total_analyses': 0
            }

    def close(self):
        """إغلاق الجلسة"""
        self.session.close()