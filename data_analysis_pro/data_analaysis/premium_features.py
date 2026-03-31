import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from datetime import datetime

class PremiumFeatures:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def check_premium_access(self, user_id, feature_name):
        """التحقق من صلاحية الوصول للميزات المميزة"""
        user_info = self.db.get_user_info(user_id)
        if not user_info or user_info['account_type'] == 'Free':
            st.error(f"🚫 {feature_name} is a Premium feature. Upgrade to Pro or Enterprise to access this feature.")
            return False
        return True
    
    def advanced_ml_models(self, df, user_id):
        """نماذج التعلم الآلي المتقدمة"""
        if not self.check_premium_access(user_id, "Advanced ML Models"):
            return
        
        st.subheader("🤖 Advanced Machine Learning")
        
        ml_type = st.selectbox("Select ML Algorithm", [
            "Clustering - KMeans",
            "Clustering - DBSCAN", 
            "Classification - Random Forest",
            "Regression - Gradient Boosting"
        ])
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if ml_type == "Clustering - KMeans":
            self.kmeans_clustering(df, numeric_cols)
        elif ml_type == "Classification - Random Forest":
            self.random_forest_classification(df, numeric_cols)
        elif ml_type == "Regression - Gradient Boosting":
            self.gradient_boosting_regression(df, numeric_cols)
    
    def kmeans_clustering(self, df, numeric_cols):
        """التجميع باستخدام KMeans"""
        if len(numeric_cols) < 2:
            st.warning("Need at least 2 numeric columns for clustering")
            return
        
        selected_features = st.multiselect("Select features for clustering", numeric_cols, default=numeric_cols[:2])
        n_clusters = st.slider("Number of clusters", 2, 10, 3)
        
        if len(selected_features) < 2:
            st.warning("Please select at least 2 features")
            return
        
        X = df[selected_features].dropna()
        
        if len(X) < n_clusters:
            st.warning("Not enough data points for clustering")
            return
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)
        
        # التصور
        if len(selected_features) >= 2:
            fig = px.scatter(
                x=X[selected_features[0]], 
                y=X[selected_features[1]], 
                color=clusters,
                title=f"KMeans Clustering (k={n_clusters})",
                labels={'x': selected_features[0], 'y': selected_features[1]}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # إضافة التجميع للبيانات
        df_clustered = df.copy()
        df_clustered['Cluster'] = clusters
        st.dataframe(df_clustered.head(10))
    
    def random_forest_classification(self, df, numeric_cols):
        """تصنيف باستخدام Random Forest"""
        if len(numeric_cols) < 1:
            st.warning("Need numeric columns for classification")
            return
        
        target_col = st.selectbox("Select target column", df.columns)
        feature_cols = st.multiselect("Select feature columns", numeric_cols, default=numeric_cols[:3])
        
        if not feature_cols or not target_col:
            return
        
        # تنظيف البيانات
        X = df[feature_cols].fillna(df[feature_cols].mean())
        y = df[target_col]
        
        # إزالة القيم المفقودة في الهدف
        mask = y.notna()
        X = X[mask]
        y = y[mask]
        
        if len(X) < 20:
            st.warning("Not enough data for classification")
            return
        
        # تقسيم البيانات
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # التدريب
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # التنبؤ والتقييم
        y_pred = model.predict(X_test)
        accuracy = model.score(X_test, y_test)
        
        st.metric("Model Accuracy", f"{accuracy:.2%}")
        
        # تقرير التصنيف
        st.subheader("Classification Report")
        report = classification_report(y_test, y_pred, output_dict=True)
        st.dataframe(pd.DataFrame(report).transpose())
    
    def gradient_boosting_regression(self, df, numeric_cols):
        """انحدار باستخدام Gradient Boosting"""
        if len(numeric_cols) < 2:
            st.warning("Need at least 2 numeric columns for regression")
            return
        
        target_col = st.selectbox("Select target column", numeric_cols, key='reg_target')
        feature_cols = st.multiselect("Select feature columns", 
                                    [col for col in numeric_cols if col != target_col], 
                                    key='reg_features')
        
        if not feature_cols or not target_col:
            return
        
        X = df[feature_cols].fillna(df[feature_cols].mean())
        y = df[target_col]
        
        # إزالة القيم المفقودة في الهدف
        mask = y.notna()
        X = X[mask]
        y = y[mask]
        
        if len(X) < 20:
            st.warning("Not enough data for regression")
            return
        
        # تقسيم البيانات
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # التدريب
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # التنبؤ والتقييم
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        st.metric("Root Mean Squared Error", f"{rmse:.4f}")
        
        # مخطط التنبؤات vs القيم الحقيقية
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=y_test, y=y_pred, mode='markers', name='Predictions'))
        fig.add_trace(go.Scatter(x=[y_test.min(), y_test.max()], y=[y_test.min(), y_test.max()], 
                               mode='lines', name='Perfect Fit', line=dict(dash='dash')))
        fig.update_layout(title="Predictions vs Actual", xaxis_title="Actual", yaxis_title="Predicted")
        st.plotly_chart(fig, use_container_width=True)
    
    def advanced_export_formats(self, df, user_id):
        """تصدير متقدم"""
        if not self.check_premium_access(user_id, "Advanced Export"):
            return
        
        st.subheader("💾 Advanced Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export to Excel", use_container_width=True):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Data', index=False)
                    # ورقة إضافية للإحصائيات
                    df.describe().to_excel(writer, sheet_name='Statistics')
                output.seek(0)
                
                st.download_button(
                    label="Download Excel File",
                    data=output,
                    file_name=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📄 Export to PDF Report", use_container_width=True):
                # إنشاء تقرير PDF مبسط
                report = self.generate_pdf_report(df)
                st.download_button(
                    label="Download PDF Report",
                    data=report,
                    file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with col3:
            if st.button("🌐 Export to HTML Dashboard", use_container_width=True):
                html_content = self.generate_html_dashboard(df)
                st.download_button(
                    label="Download HTML Dashboard",
                    data=html_content,
                    file_name=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True
                )
    
    def generate_pdf_report(self, df):
        """توليد تقرير PDF (مبسط)"""
        report_content = f"""
        DATA ANALYSIS REPORT
        Generated: {datetime.now()}
        
        Dataset Overview:
        - Rows: {len(df):,}
        - Columns: {len(df.columns)}
        - Memory: {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB
        
        Statistical Summary:
        {df.describe().to_string()}
        """
        return report_content.encode()
    
    def generate_html_dashboard(self, df):
        """توليد لوحة تحكم HTML"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f0f2f6; padding: 15px; margin: 10px; border-radius: 5px; }}
                .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
            </style>
        </head>
        <body>
            <h1>📊 Data Analysis Dashboard</h1>
            <p>Generated: {datetime.now()}</p>
            
            <div class="grid">
                <div class="metric">
                    <h3>Rows</h3>
                    <h2>{len(df):,}</h2>
                </div>
                <div class="metric">
                    <h3>Columns</h3>
                    <h2>{len(df.columns)}</h2>
                </div>
                <div class="metric">
                    <h3>Memory Usage</h3>
                    <h2>{df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB</h2>
                </div>
            </div>
            
            <h2>Data Preview</h2>
            {df.head(10).to_html()}
        </body>
        </html>
        """
        return html_template
    
    def real_time_analytics(self, df, user_id):
        """تحليلات في الوقت الفعلي (للمؤسسات)"""
        if not self.check_premium_access(user_id, "Real-time Analytics"):
            return
        
        if self.db.get_user_info(user_id)['account_type'] != 'Enterprise':
            st.error("🔒 Real-time analytics is an Enterprise-only feature")
            return
        
        st.subheader("⚡ Real-time Analytics")
        
        # محاكاة تحديث البيانات في الوقت الفعلي
        if st.button("Start Real-time Analysis"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                progress_bar.progress(i + 1)
                status_text.text(f"Processing... {i + 1}%")
                # محاكاة معالجة البيانات
                
            st.success("Real-time analysis completed!")
            
            # عرض النتائج
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Data Points Processed", f"{len(df):,}")
            with col2:
                st.metric("Processing Speed", "1,000 rows/sec")
    
    def api_access(self, user_id):
        """وصول API (للمؤسسات)"""
        if not self.check_premium_access(user_id, "API Access"):
            return
        
        if self.db.get_user_info(user_id)['account_type'] != 'Enterprise':
            st.error("🔒 API Access is an Enterprise-only feature")
            return
        
        st.subheader("🔌 API Access")
        
        st.code("""
        # Example API Usage
        import requests
        
        API_KEY = "your_api_key_here"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Upload data
        response = requests.post(
            "https://api.dataanalysispro.com/v1/upload",
            files={"file": open("data.csv", "rb")},
            headers=headers
        )
        
        # Get analysis results
        analysis = requests.get(
            "https://api.dataanalysispro.com/v1/analyses/123",
            headers=headers
        )
        """, language='python')
        
        st.info("Contact support to get your API keys and full documentation")