import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

class StoreManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def render_store_page(self, user_id):
        """عرض صفحة المتجر والترقيات"""
        st.title("🏪 Upgrade Your Plan")
        
        user_info = self.db.get_user_info(user_id)
        current_plan = user_info['account_type'] if user_info else 'Free'
        
        st.header(f"Current Plan: {current_plan}")
        
        # عرض خطط الاشتراك
        plans = self.db.session.query(SubscriptionPlan).filter_by(is_active=True).all()
        
        col1, col2, col3 = st.columns(3)
        
        for i, plan in enumerate(plans):
            with [col1, col2, col3][i]:
                self.render_plan_card(plan, current_plan, user_id)
        
        # عرض إحصائيات الاستخدام
        st.header("📊 Usage Statistics")
        self.render_usage_stats(user_id)
    
    def render_plan_card(self, plan, current_plan, user_id):
        """عرض بطاقة خطة الاشتراك"""
        is_current = plan.name == current_plan
        is_upgrade = plan.name != 'Free' and current_plan == 'Free'
        
        st.subheader(f"{plan.name} {'⭐' if plan.name != 'Free' else ''}")
        
        # السعر
        if plan.name == 'Free':
            st.markdown("### 🎁 FREE")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### ${plan.price_monthly}")
                st.caption("per month")
            with col2:
                st.markdown(f"### ${plan.price_yearly}")
                st.caption("per year (save 17%)")
        
        # الميزات
        st.markdown("**Features:**")
        for feature in plan.features:
            st.markdown(f"✅ {feature}")
        
        # الأزرار
        if is_current:
            st.success("🎯 Current Plan")
            if plan.name != 'Free':
                days_left = (user_info['subscription_end'] - datetime.now()).days
                st.info(f"Renews in {days_left} days")
        else:
            if st.button(f"Upgrade to {plan.name}", key=f"upgrade_{plan.name}", use_container_width=True):
                self.handle_upgrade(user_id, plan.name)
    
    def render_usage_stats(self, user_id):
        """عرض إحصائيات الاستخدام"""
        usage = self.db.get_user_usage_stats(user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Monthly Analyses", 
                f"{usage['monthly_analyses']}/{usage['max_monthly_analyses']}",
                delta=f"{usage['monthly_analyses'] - usage['max_monthly_analyses']}" if usage['monthly_analyses'] > usage['max_monthly_analyses'] else None
            )
        
        with col2:
            st.metric(
                "Datasets Stored",
                f"{usage['datasets_count']}/{usage['max_datasets']}"
            )
        
        with col3:
            max_size = usage['plan_limits'].get('max_file_size', 10)
            st.metric("Max File Size", f"{max_size} MB")
        
        with col4:
            export_formats = len(usage['plan_limits'].get('export_formats', ['csv']))
            st.metric("Export Formats", export_formats)
        
        # مخطط استخدام التحليلات
        if usage['max_monthly_analyses'] < 9999:  # ليس غير محدود
            fig = px.bar(
                x=['Used', 'Remaining'],
                y=[usage['monthly_analyses'], max(0, usage['max_monthly_analyses'] - usage['monthly_analyses'])],
                title="Monthly Analysis Usage"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def handle_upgrade(self, user_id, new_plan):
        """معالجة ترقية الخطة"""
        success, message = self.db.upgrade_user_plan(user_id, new_plan)
        
        if success:
            st.success(f"🎉 {message}")
            st.balloons()
            
            # عرض ميزات جديدة
            st.info(f"✨ You now have access to all {new_plan} features!")
            
            # إعادة تحميل الصفحة
            st.rerun()
        else:
            st.error(f"❌ {message}")
    
    def render_admin_subscription_panel(self):
        """لوحة إدارة الاشتراكات للمسؤول"""
        st.header("👑 Subscription Management")
        
        # إحصائيات الاشتراكات
        total_users = self.db.session.query(User).count()
        pro_users = self.db.session.query(User).filter(User.account_type == 'Pro').count()
        enterprise_users = self.db.session.query(User).filter(User.account_type == 'Enterprise').count()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Pro Users", pro_users)
        with col3:
            st.metric("Enterprise Users", enterprise_users)
        
        # إدارة المستخدمين
        st.subheader("User Management")
        users = self.db.get_all_users()
        
        for user in users:
            with st.expander(f"👤 {user.username} - {user.account_type} {'✅' if user.is_active else '❌'}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_plan = st.selectbox(
                        "Plan",
                        ["Free", "Pro", "Enterprise", "Admin"],
                        index=["Free", "Pro", "Enterprise", "Admin"].index(user.account_type),
                        key=f"plan_{user.id}"
                    )
                
                with col2:
                    days = st.number_input(
                        "Subscription Days",
                        min_value=0,
                        value=30,
                        key=f"days_{user.id}"
                    )
                
                with col3:
                    if st.button("Update", key=f"update_{user.id}"):
                        if new_plan != user.account_type:
                            self.db.upgrade_user_plan(user.id, new_plan, days)
                        else:
                            user.subscription_end = datetime.now() + timedelta(days=days)
                            self.db.session.commit()
                        st.success("User updated!")