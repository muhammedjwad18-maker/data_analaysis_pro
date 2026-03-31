import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import io
from sqlalchemy import func

class AdvancedAdminSystem:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def render_advanced_dashboard(self):
        """لوحة التحكم المتقدمة للمسؤول"""
        st.title("🚀 Advanced Admin Dashboard")
        
        # تبويبات المسؤول المتقدم
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Advanced Analytics", 
            "👥 User Behavior", 
            "💰 Revenue Analytics",
            "🔧 System Health",
            "📊 Performance Metrics",
            "🎯 AI Insights"
        ])
        
        with tab1:
            self.render_advanced_analytics()
        
        with tab2:
            self.render_user_behavior_analytics()
        
        with tab3:
            self.render_revenue_analytics()
        
        with tab4:
            self.render_system_health()
        
        with tab5:
            self.render_performance_metrics()
        
        with tab6:
            self.render_ai_insights()
    
    def render_advanced_analytics(self):
        """تحليلات متقدمة للنظام"""
        st.header("📈 Advanced System Analytics")
        
        # بيانات النظام
        stats = self.db.get_system_stats()
        users = self.db.get_all_users()
        
        # تحليل النشاط المتقدم
        active_users = [u for u in users if u.last_login and (datetime.now() - u.last_login).days < 30]
        power_users = [u for u in users if self.is_power_user(u.id)]
        new_users_30d = [u for u in users if (datetime.now() - u.created_at).days <= 30]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            retention_rate = (len(active_users) / len(users)) * 100 if users else 0
            st.metric("Retention Rate (30d)", f"{retention_rate:.1f}%")
        
        with col2:
            power_user_rate = (len(power_users) / len(users)) * 100 if users else 0
            st.metric("Power Users", f"{power_user_rate:.1f}%")
        
        with col3:
            growth_rate = (len(new_users_30d) / len(users)) * 100 if users else 0
            st.metric("Growth Rate (30d)", f"{growth_rate:.1f}%")
        
        with col4:
            avg_sessions = self.calculate_avg_sessions_per_user()
            st.metric("Avg Sessions/User", f"{avg_sessions:.1f}")
        
        # مخططات متقدمة
        col1, col2 = st.columns(2)
        
        with col1:
            # تحليل تسجيل المستخدمين
            reg_data = self.get_registration_trends()
            if reg_data:
                fig = px.area(reg_data, x='date', y='registrations', 
                            title="User Registration Trends")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # تحليل نشاط المستخدمين
            activity_data = self.get_user_activity_data()
            if activity_data:
                fig = px.line(activity_data, x='date', y='active_users', 
                            title="Daily Active Users")
                st.plotly_chart(fig, use_container_width=True)
        
        # تحليل الاستخدام المتعمق
        st.subheader("🔍 Deep Usage Analysis")
        
        usage_metrics = self.get_usage_metrics()
        if usage_metrics:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fig = px.pie(values=usage_metrics['plan_distribution'].values(),
                           names=usage_metrics['plan_distribution'].keys(),
                           title="Plan Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(x=list(usage_metrics['usage_by_hour'].keys()),
                           y=list(usage_metrics['usage_by_hour'].values()),
                           title="Usage by Hour")
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                fig = px.scatter(usage_metrics['user_engagement'], 
                               x='sessions', y='analyses', 
                               color='account_type',
                               title="User Engagement")
                st.plotly_chart(fig, use_container_width=True)
    
    def render_user_behavior_analytics(self):
        """تحليل سلوك المستخدمين المتقدم"""
        st.header("🎯 User Behavior Analytics")
        
        # تحليل الشرائح
        st.subheader("👥 User Segmentation")
        
        segments = self.segment_users()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("High Value", f"{segments['high_value']} users")
            st.progress(min(segments['high_value'] / len(self.db.get_all_users()), 1.0))
        
        with col2:
            st.metric("Active", f"{segments['active']} users")
            st.progress(min(segments['active'] / len(self.db.get_all_users()), 1.0))
        
        with col3:
            st.metric("At Risk", f"{segments['at_risk']} users")
            st.progress(min(segments['at_risk'] / len(self.db.get_all_users()), 1.0))
        
        # تحليل مسار المستخدم
        st.subheader("🛣️ User Journey Analysis")
        
        journey_data = self.analyze_user_journey()
        if journey_data:
            fig = px.funnel(journey_data, x='count', y='stage', 
                          title="User Conversion Funnel")
            st.plotly_chart(fig, use_container_width=True)
        
        # تحليل الاحتفاظ
        st.subheader("📊 Retention Analysis")
        
        retention_data = self.calculate_retention_rates()
        if retention_data:
            fig = px.line(retention_data, x='cohort', y='retention_rate',
                        title="Cohort Retention Analysis")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_revenue_analytics(self):
        """تحليلات الإيرادات المتقدمة"""
        st.header("💰 Advanced Revenue Analytics")
        
        # بيانات الإيرادات
        revenue_data = self.get_revenue_data()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("MRR", f"${revenue_data['mrr']:,.2f}")
        
        with col2:
            st.metric("ARR", f"${revenue_data['arr']:,.2f}")
        
        with col3:
            st.metric("Churn Rate", f"{revenue_data['churn_rate']:.1f}%")
        
        with col4:
            st.metric("LTV", f"${revenue_data['ltv']:,.2f}")
        
        # مخططات الإيرادات
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(revenue_data['revenue_trends'], 
                         x='month', y=['pro_revenue', 'enterprise_revenue', 'total_revenue'],
                         title="Monthly Revenue Trends")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(revenue_data['revenue_sources'], 
                        x='source', y='revenue',
                        title="Revenue by Source")
            st.plotly_chart(fig, use_container_width=True)
        
        # تحليل القيمة الدائمة
        st.subheader("📈 Customer Lifetime Value Analysis")
        
        ltv_data = self.calculate_ltv_analysis()
        if ltv_data:
            fig = px.box(ltv_data, y='ltv', color='plan', 
                        title="LTV Distribution by Plan")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_system_health(self):
        """صحة النظام ومراقبة الأداء"""
        st.header("🔧 System Health Monitoring")
        
        # مؤشرات صحة النظام
        health_metrics = self.get_system_health_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "✅ Healthy" if health_metrics['database_health'] > 90 else "⚠️ Warning"
            st.metric("Database Health", f"{health_metrics['database_health']}%", status)
        
        with col2:
            status = "✅ Healthy" if health_metrics['server_uptime'] > 99 else "⚠️ Warning"
            st.metric("Server Uptime", f"{health_metrics['server_uptime']}%", status)
        
        with col3:
            status = "✅ Healthy" if health_metrics['response_time'] < 1000 else "⚠️ Slow"
            st.metric("Avg Response Time", f"{health_metrics['response_time']}ms", status)
        
        with col4:
            st.metric("Error Rate", f"{health_metrics['error_rate']:.2f}%")
        
        # مراقبة في الوقت الحقيقي
        st.subheader("⚡ Real-time Monitoring")
        
        if st.button("🔄 Refresh System Metrics"):
            real_time_data = self.get_real_time_metrics()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = real_time_data['cpu_usage'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "CPU Usage"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "red"}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = real_time_data['memory_usage'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Memory Usage"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 60], 'color': "lightgray"},
                            {'range': [60, 85], 'color': "yellow"},
                            {'range': [85, 100], 'color': "red"}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
        
        # سجلات الأخطاء
        st.subheader("🚨 Error Logs & Alerts")
        
        error_logs = self.get_error_logs()
        if error_logs:
            for error in error_logs[:10]:  # عرض آخر 10 أخطاء
                with st.expander(f"❌ {error['timestamp']} - {error['type']}"):
                    st.write(f"**Message:** {error['message']}")
                    st.write(f"**User:** {error['user']}")
                    st.code(error['stack_trace'])
    
    def render_performance_metrics(self):
        """مقاييس أداء متقدمة"""
        st.header("📊 Advanced Performance Metrics")
        
        # مؤشرات الأداء الرئيسية
        kpis = self.get_performance_kpis()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("User Satisfaction", f"{kpis['satisfaction_score']}/10")
            st.metric("Feature Adoption", f"{kpis['feature_adoption']}%")
        
        with col2:
            st.metric("Support Tickets", kpis['support_tickets'])
            st.metric("Avg Resolution Time", f"{kpis['resolution_time']}h")
        
        with col3:
            st.metric("System Load", f"{kpis['system_load']}%")
            st.metric("API Calls/Day", f"{kpis['api_calls']:,}")
        
        # تحليل الأداء الزمني
        st.subheader("⏱️ Performance Over Time")
        
        performance_data = self.get_performance_trends()
        if performance_data:
            fig = px.line(performance_data, x='date', 
                         y=['response_time', 'load_time', 'api_response_time'],
                         title="Performance Metrics Over Time")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_ai_insights(self):
        """رؤى الذكاء الاصطناعي"""
        st.header("🤖 AI-Powered Insights")
        
        # تنبؤات الذكاء الاصطناعي
        st.subheader("🔮 Predictive Analytics")
        
        predictions = self.get_ai_predictions()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Predicted Growth (30d)", f"+{predictions['growth_prediction']}%")
            st.metric("Churn Risk Alert", f"{predictions['churn_risk']} users")
        
        with col2:
            st.metric("Revenue Forecast", f"${predictions['revenue_forecast']:,.2f}")
            st.metric("Capacity Planning", f"{predictions['capacity_needed']}%")
        
        # توصيات الذكاء الاصطناعي
        st.subheader("💡 AI Recommendations")
        
        recommendations = self.get_ai_recommendations()
        for i, rec in enumerate(recommendations):
            with st.expander(f"📋 Recommendation #{i+1}: {rec['title']}"):
                st.write(f"**Impact:** {rec['impact']}")
                st.write(f"**Effort:** {rec['effort']}")
                st.write(f"**Description:** {rec['description']}")
                
                if st.button(f"Implement #{i+1}", key=f"implement_{i}"):
                    st.success(f"Implementing: {rec['title']}")
    
    # ========== الدوال المساعدة المتقدمة ==========
    
    def is_power_user(self, user_id):
        """تحديد إذا كان المستخدم مستخدم قوي"""
        user_stats = self.db.get_user_usage_stats(user_id)
        return user_stats['monthly_analyses'] > 50 or user_stats['datasets_count'] > 10
    
    def calculate_avg_sessions_per_user(self):
        """حساب متوسط الجلسات لكل مستخدم"""
        # محاكاة البيانات - في التطبيق الحقيقي ستأتي من قاعدة البيانات
        return 12.5
    
    def get_registration_trends(self):
        """الحصول على اتجاهات التسجيل"""
        # محاكاة البيانات
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        registrations = np.random.poisson(5, len(dates)) + np.sin(np.arange(len(dates)) * 0.1) * 2
        
        return pd.DataFrame({
            'date': dates,
            'registrations': registrations.cumsum()
        })
    
    def get_user_activity_data(self):
        """الحصول على بيانات نشاط المستخدمين"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        active_users = np.random.poisson(150, len(dates)) + np.random.normal(0, 10, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'active_users': active_users
        })
    
    def get_usage_metrics(self):
        """الحصول على مقاييس الاستخدام"""
        users = self.db.get_all_users()
        
        # توزيع الخطط
        plan_distribution = {}
        for user in users:
            plan_distribution[user.account_type] = plan_distribution.get(user.account_type, 0) + 1
        
        # الاستخدام حسب الساعة
        usage_by_hour = {f"{h:02d}:00": np.random.poisson(50) for h in range(24)}
        
        # مشاركة المستخدم
        user_engagement = []
        for user in users[:50]:  # عينة من المستخدمين
            user_engagement.append({
                'sessions': np.random.poisson(15),
                'analyses': np.random.poisson(8),
                'account_type': user.account_type
            })
        
        return {
            'plan_distribution': plan_distribution,
            'usage_by_hour': usage_by_hour,
            'user_engagement': pd.DataFrame(user_engagement)
        }
    
    def segment_users(self):
        """تقسيم المستخدمين لشرائح"""
        users = self.db.get_all_users()
        
        segments = {
            'high_value': 0,
            'active': 0,
            'at_risk': 0,
            'inactive': 0
        }
        
        for user in users:
            if self.is_power_user(user.id):
                segments['high_value'] += 1
            elif user.last_login and (datetime.now() - user.last_login).days < 7:
                segments['active'] += 1
            elif user.last_login and (datetime.now() - user.last_login).days < 30:
                segments['at_risk'] += 1
            else:
                segments['inactive'] += 1
        
        return segments
    
    def analyze_user_journey(self):
        """تحليل مسار المستخدم"""
        return pd.DataFrame({
            'stage': ['Visit', 'Sign Up', 'First Analysis', 'Regular User', 'Power User'],
            'count': [1000, 200, 150, 80, 25]
        })
    
    def calculate_retention_rates(self):
        """حساب معدلات الاحتفاظ"""
        cohorts = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        retention_rates = [85, 82, 88, 79, 86, 90]  # محاكاة
        
        return pd.DataFrame({
            'cohort': cohorts,
            'retention_rate': retention_rates
        })
    
    def get_revenue_data(self):
        """الحصول على بيانات الإيرادات"""
        return {
            'mrr': 12500.00,  # Monthly Recurring Revenue
            'arr': 150000.00,  # Annual Recurring Revenue
            'churn_rate': 2.5,
            'ltv': 1250.00,   # Lifetime Value
            
            'revenue_trends': pd.DataFrame({
                'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'pro_revenue': [8000, 8500, 9200, 9800, 10500, 11000],
                'enterprise_revenue': [2000, 2500, 2800, 3200, 3500, 4000],
                'total_revenue': [10000, 11000, 12000, 13000, 14000, 15000]
            }),
            
            'revenue_sources': pd.DataFrame({
                'source': ['Pro Subscriptions', 'Enterprise Subscriptions', 'Add-ons'],
                'revenue': [11000, 4000, 500]
            })
        }
    
    def calculate_ltv_analysis(self):
        """تحليل القيمة الدائمة للعميل"""
        plans = ['Free', 'Pro', 'Enterprise']
        ltv_data = []
        
        for plan in plans:
            for _ in range(50):
                ltv_data.append({
                    'plan': plan,
                    'ltv': np.random.normal(500 if plan == 'Pro' else 1200 if plan == 'Enterprise' else 0, 200)
                })
        
        return pd.DataFrame(ltv_data)
    
    def get_system_health_metrics(self):
        """الحصول على مقاييس صحة النظام"""
        return {
            'database_health': 95.5,
            'server_uptime': 99.9,
            'response_time': 450,
            'error_rate': 0.25
        }
    
    def get_real_time_metrics(self):
        """الحصول على مقاييس الوقت الحقيقي"""
        return {
            'cpu_usage': 65.5,
            'memory_usage': 72.3,
            'disk_usage': 45.8,
            'active_connections': 234
        }
    
    def get_error_logs(self):
        """الحصول على سجلات الأخطاء"""
        return [
            {
                'timestamp': '2024-01-15 14:30:25',
                'type': 'Database Connection',
                'message': 'Connection timeout',
                'user': 'user123',
                'stack_trace': 'Traceback...'
            },
            {
                'timestamp': '2024-01-15 13:45:10',
                'type': 'File Upload',
                'message': 'File size exceeded',
                'user': 'user456',
                'stack_trace': 'Traceback...'
            }
        ]
    
    def get_performance_kpis(self):
        """الحصول على مؤشرات الأداء الرئيسية"""
        return {
            'satisfaction_score': 8.7,
            'feature_adoption': 65,
            'support_tickets': 23,
            'resolution_time': 4.5,
            'system_load': 68,
            'api_calls': 12500
        }
    
    def get_performance_trends(self):
        """الحصول على اتجاهات الأداء"""
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='W')
        
        return pd.DataFrame({
            'date': dates,
            'response_time': np.random.normal(400, 50, len(dates)),
            'load_time': np.random.normal(1200, 100, len(dates)),
            'api_response_time': np.random.normal(150, 20, len(dates))
        })
    
    def get_ai_predictions(self):
        """الحصول على تنبؤات الذكاء الاصطناعي"""
        return {
            'growth_prediction': 15.2,
            'churn_risk': 12,
            'revenue_forecast': 165000.00,
            'capacity_needed': 85
        }
    
    def get_ai_recommendations(self):
        """الحصول على توصيات الذكاء الاصطناعي"""
        return [
            {
                'title': 'Optimize Database Queries',
                'impact': 'High',
                'effort': 'Medium',
                'description': 'Database response times have increased by 15% in the last month. Optimizing queries could improve performance by 25%.'
            },
            {
                'title': 'Add Bulk Operations',
                'impact': 'Medium',
                'effort': 'Low',
                'description': 'Users are requesting bulk operations for dataset management. This feature has high demand among power users.'
            },
            {
                'title': 'Improve Mobile Experience',
                'impact': 'High',
                'effort': 'High',
                'description': '35% of users access the platform from mobile devices. Mobile optimization could increase engagement by 20%.'
            }
        ]
    
    def export_admin_report(self):
        """تصدير تقرير مسؤول شامل"""
        report_data = {
            'system_stats': self.db.get_system_stats(),
            'user_analytics': self.get_usage_metrics(),
            'revenue_data': self.get_revenue_data(),
            'performance_metrics': self.get_performance_kpis(),
            'ai_insights': self.get_ai_predictions(),
            'generated_at': datetime.now().isoformat()
        }
        
        return json.dumps(report_data, indent=2, default=str)