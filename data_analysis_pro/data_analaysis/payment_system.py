# payment_system.py
import streamlit as st
import json
import time
from datetime import datetime, timedelta
import sqlite3

class PaymentSystem:
    def __init__(self, db_manager):
        self.db = db_manager
        self.payment_methods = {
            "credit_card": {
                "name": "Credit Card",
                "icon": "💳",
                "currencies": ["USD", "EUR", "GBP"]
            },
            "paypal": {
                "name": "PayPal", 
                "icon": "🔵",
                "currencies": ["USD", "EUR"]
            },
            "crypto": {
                "name": "Cryptocurrency",
                "icon": "₿",
                "currencies": ["BTC", "ETH", "USDT"]
            },
            "bank_transfer": {
                "name": "Bank Transfer",
                "icon": "🏦",
                "currencies": ["USD", "EUR", "GBP"]
            }
        }
        
        self.subscription_plans = {
            "Pro": {
                "monthly": 29.99,
                "yearly": 299.99,
                "lifetime": 999.99,
                "features": [
                    "100MB file uploads",
                    "Unlimited analyses", 
                    "Advanced visualizations",
                    "All export formats",
                    "Priority support",
                    "Advanced ML models"
                ]
            },
            "Enterprise": {
                "monthly": 99.99,
                "yearly": 999.99, 
                "lifetime": 2999.99,
                "features": [
                    "All Pro features +",
                    "Unlimited file uploads",
                    "Real-time analytics",
                    "API access", 
                    "Custom solutions",
                    "24/7 premium support",
                    "White-label options"
                ]
            }
        }
    
    def render_payment_page(self, user_id, plan_name, lang):
        """عرض صفحة الدفع"""
        st.title(f"💳 {lang.get('payment_details', 'Payment Details')}")
        
        # معلومات الخطة
        st.header(f"📦 {plan_name} {lang.get('plan', 'Plan')}")
        self.render_plan_summary(plan_name, lang)
        
        # اختيار مدة الاشتراك
        st.subheader(f"⏰ {lang.get('select_duration', 'Select Duration')}")
        duration = st.radio(
            "",
            options=["monthly", "yearly", "lifetime"],
            format_func=lambda x: self.get_duration_display(x, lang),
            horizontal=True
        )
        
        # حساب السعر
        price = self.calculate_price(plan_name, duration)
        discount = self.calculate_discount(plan_name, duration)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(lang.get("price", "Price"), f"${price}")
        with col2:
            if discount > 0:
                st.metric(lang.get("discount", "Discount"), f"{discount}%")
        with col3:
            st.metric(lang.get("total_amount", "Total Amount"), f"${price}")
        
        # اختيار طريقة الدفع
        st.subheader(f"🔗 {lang.get('payment_method', 'Payment Method')}")
        payment_method = st.selectbox(
            "",
            options=list(self.payment_methods.keys()),
            format_func=lambda x: f"{self.payment_methods[x]['icon']} {self.payment_methods[x]['name']}"
        )
        
        # نموذج الدفع
        if payment_method == "credit_card":
            self.render_credit_card_form(lang)
        elif payment_method == "paypal":
            self.render_paypal_form(lang)
        elif payment_method == "crypto":
            self.render_crypto_form(lang)
        elif payment_method == "bank_transfer":
            self.render_bank_transfer_form(lang)
        
        # معلومات الفواتير
        st.subheader(f"📝 {lang.get('billing_info', 'Billing Information')}")
        self.render_billing_form(lang)
        
        # زر الدفع النهائي
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"🚀 {lang.get('pay_now', 'Pay Now')} - ${price}", 
                use_container_width=True,
                type="primary"
            ):
                self.process_payment(user_id, plan_name, duration, price, payment_method, lang)
    
    def render_plan_summary(self, plan_name, lang):
        """عرض ملخص الخطة"""
        plan = self.subscription_plans[plan_name]
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**{plan_name} {lang.get('plan', 'Plan')}**")
            for feature in plan['features']:
                st.write(f"✅ {feature}")
        with col2:
            st.success("**💰 Pricing**")
            st.write(f"💵 Monthly: ${plan['monthly']}")
            st.write(f"📅 Yearly: ${plan['yearly']} ({lang.get('save_20', 'Save 20%')})")
            st.write(f"🌟 Lifetime: ${plan['lifetime']}")
    
    def render_credit_card_form(self, lang):
        """نموذج بطاقة الائتمان"""
        col1, col2 = st.columns(2)
        
        with col1:
            card_number = st.text_input(
                lang.get("card_number", "Card Number"),
                placeholder="1234 5678 9012 3456",
                max_chars=19
            )
            name_on_card = st.text_input(
                lang.get("name_on_card", "Name on Card")
            )
        
        with col2:
            col2a, col2b = st.columns(2)
            with col2a:
                expiry_date = st.text_input(
                    lang.get("expiry_date", "Expiry Date"),
                    placeholder="MM/YY",
                    max_chars=5
                )
            with col2b:
                cvv = st.text_input(
                    lang.get("cvv", "CVV"),
                    placeholder="123",
                    max_chars=3,
                    type="password"
                )
        
        # Accepted cards
        st.write("**Accepted Cards:**")
        card_cols = st.columns(4)
        with card_cols[0]:
            st.write("💳 Visa")
        with card_cols[1]:
            st.write("💳 MasterCard") 
        with card_cols[2]:
            st.write("💳 American Express")
        with card_cols[3]:
            st.write("💳 Discover")
    
    def render_paypal_form(self, lang):
        """نموذج باي بال"""
        st.info("🔵 You will be redirected to PayPal to complete your payment securely.")
        
        col1, col2 = st.columns(2)
        with col1:
            paypal_email = st.text_input("PayPal Email")
        with col2:
            st.write("")  # Spacer
        
        st.write("**Benefits:**")
        st.write("✅ Fast and secure checkout")
        st.write("✅ Buyer protection")
        st.write("✅ No need to share card details")
    
    def render_crypto_form(self, lang):
        """نموذج العملات المشفرة"""
        st.info("₿ Pay with cryptocurrency for maximum privacy and security.")
        
        crypto_option = st.selectbox(
            "Select Cryptocurrency",
            options=["Bitcoin (BTC)", "Ethereum (ETH)", "USDT", "USDC"]
        )
        
        # محاكاة عنوان المحفظة
        if crypto_option == "Bitcoin (BTC)":
            wallet_address = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        elif crypto_option == "Ethereum (ETH)":
            wallet_address = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
        elif crypto_option == "USDT":
            wallet_address = "TBA1cyKdKXvZSiLf7umMfE8JbeZbPej6R9"  
        else:
            wallet_address = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
        
        st.text_area("Send payment to:", wallet_address, height=60)
        
        st.warning("⚠️ Send exact amount. Transactions may take 10-30 minutes to confirm.")
    
    def render_bank_transfer_form(self, lang):
        """نموذج التحويل البنكي"""
        st.info("🏦 Bank transfer details for manual payment.")
        
        st.write("**Bank Details:**")
        st.write("Bank: Global Business Bank")
        st.write("Account: 123456789")
        st.write("Routing: 021000021")
        st.write("SWIFT: GBOBUS33")
        st.write("Beneficiary: Data Analysis Pro Inc.")
        
        st.text_area("Reference/Note:", "Your username + subscription")
        
        st.warning("⚠️ Please include your username in the transfer reference.")
    
    def render_billing_form(self, lang):
        """نموذج معلومات الفواتير"""
        col1, col2 = st.columns(2)
        
        with col1:
            billing_name = st.text_input("Full Name")
            email = st.text_input("Email", type="default")
            phone = st.text_input(lang.get("phone", "Phone Number"))
        
        with col2:
            address = st.text_input(lang.get("address", "Address"))
            city = st.text_input(lang.get("city", "City"))
            col2a, col2b = st.columns(2)
            with col2a:
                country = st.selectbox(lang.get("country", "Country"), ["United States", "Canada", "United Kingdom", "Germany", "France", "Other"])
            with col2b:
                zip_code = st.text_input(lang.get("zip_code", "ZIP Code"))
    
    def calculate_price(self, plan_name, duration):
        """حساب السعر"""
        plan = self.subscription_plans[plan_name]
        return plan[duration]
    
    def calculate_discount(self, plan_name, duration):
        """حساب الخصم"""
        if duration == "yearly":
            monthly_price = self.subscription_plans[plan_name]["monthly"]
            yearly_price = self.subscription_plans[plan_name]["yearly"]
            yearly_cost_monthly = monthly_price * 12
            discount = ((yearly_cost_monthly - yearly_price) / yearly_cost_monthly) * 100
            return int(discount)
        return 0
    
    def get_duration_display(self, duration, lang):
        """عرض مدة الاشتراك"""
        if duration == "monthly":
            return f"📅 {lang.get('monthly', 'Monthly')}"
        elif duration == "yearly":
            return f"💰 {lang.get('yearly', 'Yearly')} ({lang.get('save_20', 'Save 20%')})"
        else:
            return f"🌟 {lang.get('lifetime', 'Lifetime Access')}"
    
    def process_payment(self, user_id, plan_name, duration, amount, payment_method, lang):
        """معالجة الدفع"""
        try:
            with st.spinner(f"🔄 {lang.get('processing_payment', 'Processing your payment...')}"):
                # محاكاة معالجة الدفع
                time.sleep(2)
                
                # في التطبيق الحقيقي، هنا ستتكامل مع بوابة الدفع
                success = self.mock_payment_processing(amount, payment_method)
                
                if success:
                    # تحديث حساب المستخدم
                    self.update_user_subscription(user_id, plan_name, duration)
                    
                    st.success(f"🎉 {lang.get('payment_success', 'Payment Successful!')}")
                    st.balloons()
                    
                    # عرض تفاصيل الاشتراك
                    st.info(f"""
                    **Subscription Details:**
                    - Plan: {plan_name}
                    - Duration: {duration}
                    - Amount: ${amount}
                    - Next Billing: {self.get_next_billing_date(duration)}
                    - Status: Active ✅
                    """)
                    
                    # إعادة التوجيه بعد 3 ثواني
                    time.sleep(3)
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ {lang.get('payment_failed', 'Payment Failed')}")
                    
        except Exception as e:
            st.error(f"Payment processing error: {e}")
    
    def mock_payment_processing(self, amount, payment_method):
        """محاكاة معالجة الدفع (في التطبيق الحقيقي استبدل هذا ببوابة دفع حقيقية)"""
        # محاكاة نجاح الدفع بنسبة 95%
        import random
        return random.random() > 0.05  # 95% success rate
    
    def update_user_subscription(self, user_id, plan_name, duration):
        """تحديث اشتراك المستخدم"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            # حساب تاريخ الانتهاء
            if duration == "monthly":
                subscription_end = datetime.now() + timedelta(days=30)
                lifetime = False
            elif duration == "yearly":
                subscription_end = datetime.now() + timedelta(days=365) 
                lifetime = False
            else:  # lifetime
                subscription_end = None
                lifetime = True
            
            cursor.execute('''
                UPDATE users 
                SET account_type = ?, subscription_end = ?, lifetime = ?
                WHERE id = ?
            ''', (plan_name, subscription_end, lifetime, user_id))
            
            # تسجيل عملية الدفع
            cursor.execute('''
                INSERT INTO payments 
                (user_id, plan_name, duration, amount, payment_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, plan_name, duration, 
                  self.calculate_price(plan_name, duration), 
                  'credit_card', 'completed', datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Error updating subscription: {e}")
    
    def get_next_billing_date(self, duration):
        """الحصول على تاريخ الفاتورة التالية"""
        if duration == "monthly":
            return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        elif duration == "yearly":
            return (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        else:
            return "Never (Lifetime)"
    
    def create_payments_table(self):
        """إنشاء جدول المدفوعات إذا لم يكن موجوداً"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan_name VARCHAR(50),
                    duration VARCHAR(20),
                    amount FLOAT,
                    payment_method VARCHAR(50),
                    status VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    transaction_id VARCHAR(100)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Error creating payments table: {e}")
    
    def get_payment_history(self, user_id):
        """الحصول على سجل المدفوعات"""
        try:
            conn = sqlite3.connect('data_analysis_pro.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT plan_name, duration, amount, payment_method, status, created_at
                FROM payments 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            payments = cursor.fetchall()
            conn.close()
            
            return payments
            
        except Exception as e:
            st.error(f"Error getting payment history: {e}")
            return []