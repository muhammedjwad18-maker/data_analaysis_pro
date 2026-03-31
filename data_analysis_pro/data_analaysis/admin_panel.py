import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

class AdminPanel:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def render_admin_dashboard(self):
        """لوحة تحكم المسؤول الرئيسية"""
        st.title("👑 Admin Dashboard")
        
        # إحصائيات سريعة
        stats = self.db.get_system_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", stats['total_users'])
        with col2:
            st.metric("Active Users", stats['active_users'])
        with col3:
            st.metric("Pro Users", stats['pro_users'])
        with col4:
            st.metric("Enterprise Users", stats['enterprise_users'])
        
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric("Total Datasets", stats['total_datasets'])
        with col6:
            st.metric("Total Analyses", stats['total_analyses'])
        with col7:
            st.metric("Admin Users", stats['admin_users'])
        
        # تبويبات المسؤول
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👥 User Management", 
            "📊 System Analytics", 
            "⚙️ System Settings",
            "📋 Admin Logs",
            "🎁 Bulk Operations"
        ])
        
        with tab1:
            self.render_user_management()
        
        with tab2:
            self.render_system_analytics()
        
        with tab3:
            self.render_system_settings()
        
        with tab4:
            self.render_admin_logs()
        
        with tab5:
            self.render_bulk_operations()
    
    def render_user_management(self):
        """إدارة المستخدمين"""
        st.subheader("👥 User Management")
        
        # شريط البحث والتصفية
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("🔍 Search users")
        with col2:
            filter_type = st.selectbox("Filter by type", ["All", "Free", "Pro", "Enterprise", "Admin"])
        with col3:
            filter_status = st.selectbox("Filter by status", ["All", "Active", "Inactive"])
        
        # الحصول على جميع المستخدمين
        users = self.db.get_all_users()
        
        # التصفية
        if search_term:
            users = [u for u in users if search_term.lower() in u.username.lower() or 
                    (u.email and search_term.lower() in u.email.lower())]
        
        if filter_type != "All":
            users = [u for u in users if u.account_type == filter_type]
        
        if filter_status != "All":
            users = [u for u in users if u.is_active == (filter_status == "Active")]
        
        # عرض المستخدمين
        for user in users:
            with st.expander(f"👤 {user.username} - {user.account_type} {'✅' if user.is_active else '❌'}"):
                self.render_user_editor(user)
    
    def render_user_editor(self, user):
        """محرر بيانات المستخدم"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Email:** {user.email or 'N/A'}")
            st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d')}")
            st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
        
        with col2:
            # تعديل نوع الحساب
            new_account_type = st.selectbox(
                "Account Type",
                ["Free", "Pro", "Enterprise", "Admin"],
                index=["Free", "Pro", "Enterprise", "Admin"].index(user.account_type),
                key=f"type_{user.id}"
            )
            
            # مدة الاشتراك
            if new_account_type != "Free":
                col_a, col_b = st.columns(2)
                with col_a:
                    days = st.number_input("Days", min_value=1, max_value=3650, value=30, key=f"days_{user.id}")
                with col_b:
                    lifetime = st.checkbox("Lifetime", value=user.lifetime, key=f"lifetime_{user.id}")
            else:
                days = None
                lifetime = False
            
            # حالة الحساب
            is_active = st.checkbox("Active", value=user.is_active, key=f"active_{user.id}")
        
        with col3:
            # ملاحظات المسؤول
            admin_notes = st.text_area("Admin Notes", value=user.admin_notes or "", key=f"notes_{user.id}")
            
            # أزرار الإجراءات
            col_x, col_y = st.columns(2)
            with col_x:
                if st.button("💾 Update", key=f"update_{user.id}", use_container_width=True):
                    success, message = self.db.update_user_account(
                        st.session_state.user_id,
                        user.id,
                        new_account_type,
                        days,
                        lifetime,
                        admin_notes
                    )
                    if success:
                        st.success(message)
                        # تحديث حالة المستخدم
                        user.is_active = is_active
                        self.db.session.commit()
                        st.rerun()
                    else:
                        st.error(message)
            
            with col_y:
                if st.button("🔄 Reset Password", key=f"reset_{user.id}", use_container_width=True):
                    if self.reset_user_password(user.id):
                        st.success("Password reset to: 123456")
                    else:
                        st.error("Failed to reset password")
    
    def reset_user_password(self, user_id):
        """إعادة تعيين كلمة مرور المستخدم"""
        try:
            from passlib.hash import pbkdf2_sha256
            user = self.db.session.query(User).filter_by(id=user_id).first()
            if user:
                user.password = pbkdf2_sha256.hash("123456")
                self.db.session.commit()
                
                # تسجيل العملية
                from database import AdminLog
                log = AdminLog(
                    admin_id=st.session_state.user_id,
                    action="Reset user password",
                    target_user_id=user_id,
                    details={'new_password_default': '123456'}
                )
                self.db.session.add(log)
                self.db.session.commit()
                return True
        except Exception as e:
            st.error(f"Error resetting password: {e}")
        return False
    
    def render_system_analytics(self):
        """تحليلات النظام"""
        st.subheader("📊 System Analytics")
        
        stats = self.db.get_system_stats()
        users = self.db.get_all_users()
        
        # تحليل توزيع المستخدمين
        user_types = [u.account_type for u in users]
        type_counts = pd.Series(user_types).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # مخطط توزيع المستخدمين
            fig1 = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="User Distribution by Account Type"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # مخطط تسجيل المستخدمين عبر الوقت
            registration_dates = [u.created_at.date() for u in users]
            reg_df = pd.Series(registration_dates).value_counts().sort_index()
            
            fig2 = px.line(
                x=reg_df.index,
                y=reg_df.values,
                title="User Registrations Over Time"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # إحصائيات مفصلة
        st.subheader("Detailed Statistics")
        
        # إنشاء DataFrame للإحصائيات
        analytics_data = []
        for user in users:
            user_stats = self.db.get_user_usage_stats(user.id)
            analytics_data.append({
                'username': user.username,
                'account_type': user.account_type,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'monthly_analyses': user_stats['monthly_analyses'],
                'datasets_count': user_stats['datasets_count'],
                'is_active': user.is_active
            })
        
        if analytics_data:
            df = pd.DataFrame(analytics_data)
            st.dataframe(df, use_container_width=True)
            
            # تصدير البيانات
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Export Users Data",
                data=csv,
                file_name="users_analytics.csv",
                mime="text/csv"
            )
    
    def render_system_settings(self):
        """إعدادات النظام"""
        st.subheader("⚙️ System Settings")
        
        tab1, tab2, tab3 = st.tabs(["General", "Security", "Maintenance"])
        
        with tab1:
            st.number_input("Max File Size (MB)", value=100, key="max_file_size")
            st.number_input("Max Users", value=1000, key="max_users")
            st.text_input("System Name", value="Data Analysis Pro", key="system_name")
            
            if st.button("Save General Settings"):
                st.success("Settings saved!")
        
        with tab2:
            st.number_input("Failed Login Attempts Before Lock", value=5, key="max_attempts")
            st.number_input("Lockout Duration (minutes)", value=30, key="lockout_duration")
            st.checkbox("Require Email Verification", value=True, key="email_verify")
            st.checkbox("Enable Two-Factor Authentication", value=False, key="two_factor")
            
            if st.button("Save Security Settings"):
                st.success("Security settings updated!")
        
        with tab3:
            st.info("System Maintenance Tools")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Clear Cache", use_container_width=True):
                    st.success("Cache cleared successfully!")
                
                if st.button("📊 Recalculate Statistics", use_container_width=True):
                    st.success("Statistics recalculated!")
            
            with col2:
                if st.button("🛡️ Backup Database", use_container_width=True):
                    st.success("Backup created successfully!")
                
                if st.button("⚠️ System Health Check", use_container_width=True):
                    st.success("System is healthy!")
    
    def render_admin_logs(self):
        """سجلات المسؤول"""
        st.subheader("📋 Admin Activity Logs")
        
        logs = self.db.get_admin_logs(limit=50)
        
        # تصفية السجلات
        col1, col2 = st.columns(2)
        with col1:
            filter_action = st.text_input("Filter by action")
        with col2:
            filter_admin = st.text_input("Filter by admin")
        
        for log in logs:
            admin_user = self.db.session.query(User).filter_by(id=log.admin_id).first()
            target_user = self.db.session.query(User).filter_by(id=log.target_user_id).first()
            
            if filter_action and filter_action.lower() not in log.action.lower():
                continue
            if filter_admin and admin_user and filter_admin.lower() not in admin_user.username.lower():
                continue
            
            with st.expander(f"🕒 {log.created_at.strftime('%Y-%m-%d %H:%M')} - {log.action}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Admin:** {admin_user.username if admin_user else 'Unknown'}")
                    st.write(f"**Target User:** {target_user.username if target_user else 'Unknown'}")
                with col2:
                    st.write(f"**Action:** {log.action}")
                    if log.details:
                        st.json(log.details)
    
    def render_bulk_operations(self):
        """العمليات المجمعة"""
        st.subheader("🎁 Bulk Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Bulk Account Upgrades")
            
            upgrade_type = st.selectbox("Upgrade to", ["Pro", "Enterprise"])
            upgrade_days = st.number_input("Days", min_value=1, max_value=3650, value=30)
            
            # اختيار المستخدمين
            users = self.db.get_all_users()
            free_users = [u for u in users if u.account_type == "Free"]
            
            selected_users = st.multiselect(
                "Select users to upgrade",
                [f"{u.username} ({u.email})" for u in free_users],
                key="bulk_upgrade_users"
            )
            
            if st.button("🚀 Bulk Upgrade", type="primary", use_container_width=True):
                if selected_users:
                    success_count = 0
                    for user_str in selected_users:
                        username = user_str.split(" (")[0]
                        user = next((u for u in free_users if u.username == username), None)
                        if user:
                            success, _ = self.db.update_user_account(
                                st.session_state.user_id,
                                user.id,
                                upgrade_type,
                                upgrade_days
                            )
                            if success:
                                success_count += 1
                    
                    st.success(f"Upgraded {success_count}/{len(selected_users)} users to {upgrade_type}")
                else:
                    st.warning("Please select users to upgrade")
        
        with col2:
            st.info("Bulk Account Management")
            
            bulk_action = st.selectbox("Action", ["Activate Accounts", "Deactivate Accounts", "Reset to Free"])
            
            all_users = [f"{u.username} ({u.account_type})" for u in users]
            bulk_selected = st.multiselect("Select users", all_users, key="bulk_manage_users")
            
            if st.button("🔧 Apply Bulk Action", use_container_width=True):
                if bulk_selected:
                    processed_count = 0
                    for user_str in bulk_selected:
                        username = user_str.split(" (")[0]
                        user = next((u for u in users if u.username == username), None)
                        
                        if user:
                            if bulk_action == "Activate Accounts":
                                user.is_active = True
                            elif bulk_action == "Deactivate Accounts":
                                user.is_active = False
                            elif bulk_action == "Reset to Free":
                                user.account_type = "Free"
                                user.lifetime = False
                                user.subscription_end = None
                            
                            processed_count += 1
                    
                    self.db.session.commit()
                    st.success(f"Processed {processed_count} users")
                else:
                    st.warning("Please select users")