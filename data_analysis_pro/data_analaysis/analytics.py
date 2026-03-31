import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import streamlit as st
import plotly.express as px
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class ML_Analytics:
    def __init__(self):
        self.scaler = StandardScaler()
    
    def detect_outliers(self, df):
        """كشف القيم الشاذة"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            st.warning("No numeric columns for outlier detection")
            return
        
        selected_cols = st.multiselect("Select columns for outlier detection", 
                                     numeric_cols, 
                                     default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols,
                                     key='outlier_cols')
        
        if not selected_cols:
            return
        
        try:
            # استخدام Isolation Forest
            clf = IsolationForest(contamination=0.1, random_state=42)
            outlier_labels = clf.fit_predict(df[selected_cols].dropna())
            
            # إضافة علامات القيم الشاذة
            result_df = df[selected_cols].copy()
            result_df['is_outlier'] = outlier_labels
            result_df['is_outlier'] = result_df['is_outlier'].map({1: 'Normal', -1: 'Outlier'})
            
            # عرض النتائج
            outlier_count = (outlier_labels == -1).sum()
            st.info(f"Detected {outlier_count} outliers ({outlier_count/len(df)*100:.2f}%)")
            
            # التصور
            if len(selected_cols) >= 2:
                fig = px.scatter(result_df, x=selected_cols[0], y=selected_cols[1], 
                               color='is_outlier', title="Outlier Detection")
                st.plotly_chart(fig, use_container_width=True)
            
            # عرض القيم الشاذة
            with st.expander("Show Outlier Data"):
                outliers = df[outlier_labels == -1]
                st.dataframe(outliers)
        
        except Exception as e:
            st.error(f"Error in outlier detection: {e}")
    
    def trend_analysis(self, df):
        """تحليل الاتجاهات"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            st.warning("No numeric columns for trend analysis")
            return
        
        selected_col = st.selectbox("Select column for trend analysis", numeric_cols, key='trend_col')
        
        # حساب الاتجاه باستخدام الانحدار الخطي
        y = df[selected_col].dropna().values
        x = np.arange(len(y))
        
        if len(y) < 2:
            st.warning("Not enough data points for trend analysis")
            return
        
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # عرض النتائج
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Slope", f"{slope:.4f}")
            with col2:
                st.metric("R-squared", f"{r_value**2:.4f}")
            with col3:
                st.metric("P-value", f"{p_value:.4f}")
            with col4:
                direction = "Increasing" if slope > 0 else "Decreasing" if slope < 0 else "Stable"
                st.metric("Trend", direction)
            
            # مخطط الاتجاه
            trend_line = intercept + slope * x
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Actual'))
            fig.add_trace(go.Scatter(x=x, y=trend_line, mode='lines', name='Trend'))
            
            fig.update_layout(title=f"Trend Analysis: {selected_col}")
            st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error in trend analysis: {e}")
    
    def statistical_tests(self, df):
        """الاختبارات الإحصائية"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            st.warning("Need at least 2 numeric columns for statistical tests")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_type = st.selectbox(
                "Statistical Test",
                ["T-Test", "Normality Test", "Correlation Test"],
                key='stat_test'
            )
        
        with col2:
            if test_type == "T-Test":
                col_a = st.selectbox("Group A", numeric_cols, key='ttest_a')
                col_b = st.selectbox("Group B", numeric_cols, key='ttest_b')
                
                if st.button("Run T-Test", key='run_ttest'):
                    t_stat, p_value = stats.ttest_ind(df[col_a].dropna(), df[col_b].dropna())
                    
                    st.write(f"**T-Test Results:**")
                    st.write(f"T-statistic: {t_stat:.4f}")
                    st.write(f"P-value: {p_value:.4f}")
                    st.write(f"Significant: {'Yes' if p_value < 0.05 else 'No'}")
            
            elif test_type == "Normality Test":
                col_norm = st.selectbox("Select Column", numeric_cols, key='normality')
                
                if st.button("Run Normality Test", key='run_normality'):
                    stat, p_value = stats.normaltest(df[col_norm].dropna())
                    
                    st.write(f"**Normality Test (D'Agostino):**")
                    st.write(f"Statistic: {stat:.4f}")
                    st.write(f"P-value: {p_value:.4f}")
                    st.write(f"Normal: {'Yes' if p_value > 0.05 else 'No'}")
    
    def automl_analysis(self, df):
        """تحليل تلقائي باستخدام AutoML"""
        report = {
            "Data Overview": {
                "Shape": f"{df.shape}",
                "Total Rows": f"{len(df):,}",
                "Total Columns": f"{len(df.columns)}",
                "Memory Usage": f"{df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB"
            },
            "Data Quality": {
                "Missing Values": f"{df.isnull().sum().sum()}",
                "Duplicate Rows": f"{df.duplicated().sum()}",
                "Complete Cases": f"{(~df.isnull().any(axis=1)).sum()}"
            },
            "Patterns & Insights": {},
            "Recommendations": [
                "Consider exploring different chart types for your data",
                "Check for outliers in numerical columns",
                "Review data types for optimal analysis"
            ]
        }
        
        # جودة البيانات
        missing_percent = (df.isnull().sum() / len(df) * 100).round(2)
        high_missing = missing_percent[missing_percent > 20]
        
        report["Data Quality"]["High Missing Columns"] = list(high_missing.index) if len(high_missing) > 0 else "None"
        
        # الأنماط والرؤى
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            correlations = df[numeric_cols].corr().unstack().sort_values(ascending=False)
            high_corr = correlations[(correlations.abs() > 0.8) & (correlations.abs() < 1.0)]
            
            if len(high_corr) > 0:
                report["Patterns & Insights"]["High Correlations"] = dict(high_corr.head(5))
            else:
                report["Patterns & Insights"]["High Correlations"] = "None"
        
        # التوصيات الإضافية
        if df.duplicated().sum() > 0:
            report["Recommendations"].append(f"Remove {df.duplicated().sum()} duplicate rows")
        
        if len(high_missing) > 0:
            report["Recommendations"].append(f"Consider removing or imputing {len(high_missing)} columns with high missing values")
        
        return report