from passlib.hash import pbkdf2_sha256
import streamlit as st
from datetime import datetime, timedelta
import re
import time

class AuthenticationSystem:
    def __init__(self):
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=10)
    
    def check_authentication(self):
        """التحقق من حالة المصادقة"""
        if not st.session_state.get('user_id'):
            self.show_login_page()
            return False
        return True
    
    def show_login_page(self):
        """عرض صفحة تسجيل الدخول"""
        st.title("🔐 Data Analysis Pro")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            self.render_login_form()
        
        with tab2:
            self.render_signup_form()
    
    def render_login_form(self):
        """نموذج تسجيل الدخول"""
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            
            if st.form_submit_button("Login", use_container_width=True):
                self.handle_login(username, password, remember_me)
    
    def handle_login(self, username, password, remember_me):
        """معالجة تسجيل الدخول"""
        # التحقق من الحظر
        if self.is_user_locked(username):
            st.error("Account temporarily locked. Please try again later.")
            return
        
        # المصادقة
        user = self.authenticate_user(username, password)
        
        if user:
            # نجاح تسجيل الدخول
            st.session_state.user_id = user['id']
            st.session_state.username = user['username']
            st.session_state.account_type = user['account_type']
            
            # إعادة تعيين محاولات الدخول الفاشلة
            self.reset_login_attempts(username)
            
            st.success(f"Welcome back, {user['username']}!")
            time.sleep(1)
            st.rerun()
        else:
            # فشل تسجيل الدخول
            if username:  # فقط إذا أدخل اسم مستخدم
                self.record_failed_attempt(username)
            st.error("Invalid username or password")
    
    def authenticate_user(self, username, password):
        """المصادقة مع قاعدة البيانات"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # استيراد User هنا لتجنب التبعية الدائرية
            from database import User
            
            user = db.session.query(User).filter_by(username=username).first()
            if user and pbkdf2_sha256.verify(password, user.password):
                # تحديث آخر دخول
                user.last_login = datetime.now()
                db.session.commit()
                
                return {
                    'id': user.id,
                    'username': user.username,
                    'account_type': user.account_type,
                    'email': user.email
                }
            return None
        except Exception as e:
            st.error(f"Authentication error: {e}")
            return None
    
    def is_user_locked(self, username):
        """التحقق إذا كان المستخدم محظوراً"""
        if not username:
            return False
            
        attempts = st.session_state.get('login_attempts', {}).get(username, {})
        locked_until = attempts.get('locked_until')
        
        if locked_until and datetime.now() < locked_until:
            return True
        return False
    
    def record_failed_attempt(self, username):
        """تسجيل محاولة فاشلة"""
        attempts = st.session_state.setdefault('login_attempts', {})
        user_attempts = attempts.setdefault(username, {'count': 0})
        
        user_attempts['count'] += 1
        
        if user_attempts['count'] >= self.max_attempts:
            user_attempts['locked_until'] = datetime.now() + self.lockout_duration
            user_attempts['count'] = 0
    
    def reset_login_attempts(self, username):
        """إعادة تعيين المحاولات الفاشلة"""
        attempts = st.session_state.get('login_attempts', {})
        if username in attempts:
            del attempts[username]
    
    def render_signup_form(self):
        """نموذج التسجيل"""
        with st.form("signup_form"):
            st.subheader("Create New Account")
            
            username = st.text_input("Choose Username")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Account", use_container_width=True):
                self.handle_signup(username, email, password, confirm_password)
    
    def handle_signup(self, username, email, password, confirm_password):
        """معالجة التسجيل"""
        # التحقق من صحة البيانات
        if not self.validate_signup_data(username, email, password, confirm_password):
            return
        
        # إنشاء حساب جديد
        if self.create_user_account(username, email, password):
            st.success("Account created successfully! Please login.")
        else:
            st.error("Failed to create account. Username may already exist.")
    
    def validate_signup_data(self, username, email, password, confirm_password):
        """التحقق من صحة بيانات التسجيل"""
        if not username or not email or not password:
            st.error("All fields are required")
            return False
            
        if password != confirm_password:
            st.error("Passwords do not match")
            return False
        
        if len(password) < 8:
            st.error("Password must be at least 8 characters")
            return False
        
        if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            st.error("Password must contain both letters and numbers")
            return False
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Please enter a valid email address")
            return False
        
        return True
    
    def create_user_account(self, username, email, password):
        """إنشاء حساب مستخدم جديد"""
        try:
            from database import DatabaseManager
            from database import User
            
            db = DatabaseManager()
            
            # التحقق من عدم وجود مستخدم بنفس الاسم
            if db.session.query(User).filter_by(username=username).first():
                return False
            
            # إنشاء المستخدم
            hashed_password = pbkdf2_sha256.hash(password)
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                account_type='Free',
                lifetime=False,
                is_active=True
            )
            
            db.session.add(new_user)
            db.session.commit()
            return True
        except Exception as e:
            st.error(f"Error creating account: {e}")
            return False
    
    def logout(self):
        """تسجيل الخروج"""
        for key in ['user_id', 'username', 'account_type']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    def is_admin_user(self, username, password):
        """تحقق سريع إذا كان المستخدم مسؤولاً"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            user = db.session.query(User).filter_by(username=username).first()
            return user and user.account_type == 'Admin' and pbkdf2_sha256.verify(password, user.password)
        except:
            return False