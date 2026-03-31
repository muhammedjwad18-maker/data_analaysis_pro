import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import streamlit as st
from plotly.subplots import make_subplots

class AdvancedVisualizer:
    def __init__(self):
        self.color_palette = px.colors.qualitative.Plotly
    
    def interactive_scatter(self, df):
        """مخطط مبعثر تفاعلي"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            st.warning("Need at least 2 numeric columns for scatter plot")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_axis = st.selectbox("X Axis", numeric_cols, index=0, key='scatter_x')
        with col2:
            y_axis = st.selectbox("Y Axis", numeric_cols, index=1 if len(numeric_cols) > 1 else 0, key='scatter_y')
        with col3:
            color_by = st.selectbox("Color By", [None] + df.columns.tolist(), key='scatter_color')
        
        # إنشاء المخطط
        if color_by:
            fig = px.scatter(df, x=x_axis, y=y_axis, color=color_by,
                           title=f"{y_axis} vs {x_axis}", hover_data=df.columns.tolist()[:3])
        else:
            fig = px.scatter(df, x=x_axis, y=y_axis,
                           title=f"{y_axis} vs {x_axis}", hover_data=df.columns.tolist()[:3])
        
        st.plotly_chart(fig, use_container_width=True)
    
    def correlation_heatmap(self, df):
        """خريطة حرارة الارتباط"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            st.warning("Need at least 2 numeric columns for correlation heatmap")
            return
        
        corr_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmin=-1,
            zmax=1,
            hoverongaps=False,
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Correlation Heatmap",
            width=800,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # عرض قيم الارتباط
        with st.expander("Show Correlation Values"):
            st.dataframe(corr_matrix.style.background_gradient(cmap='RdBu_r', vmin=-1, vmax=1))
    
    def scatter_3d(self, df):
        """مخطط مبعثر ثلاثي الأبعاد"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 3:
            st.warning("Need at least 3 numeric columns for 3D scatter plot")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            x_axis = st.selectbox("X Axis 3D", numeric_cols, index=0, key='x_3d')
        with col2:
            y_axis = st.selectbox("Y Axis 3D", numeric_cols, index=1, key='y_3d')
        with col3:
            z_axis = st.selectbox("Z Axis 3D", numeric_cols, index=2, key='z_3d')
        with col4:
            color_3d = st.selectbox("Color 3D", [None] + df.columns.tolist(), key='color_3d')
        
        if color_3d:
            fig = px.scatter_3d(df, x=x_axis, y=y_axis, z=z_axis, color=color_3d)
        else:
            fig = px.scatter_3d(df, x=x_axis, y=y_axis, z=z_axis)
        
        fig.update_layout(title="3D Scatter Plot")
        st.plotly_chart(fig, use_container_width=True)
    
    def time_series_analysis(self, df):
        """تحليل السلاسل الزمنية"""
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not date_cols:
            st.warning("No datetime columns found for time series analysis")
            # البحث عن أعمدة يمكن تحويلها لتواريخ
            potential_date_cols = []
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['date', 'time', 'year', 'month', 'day']):
                    potential_date_cols.append(col)
            
            if potential_date_cols:
                st.info(f"Potential date columns: {', '.join(potential_date_cols)}")
                selected_col = st.selectbox("Select potential date column", potential_date_cols)
                if st.button("Convert to datetime"):
                    try:
                        df[selected_col] = pd.to_datetime(df[selected_col])
                        st.success("Column converted to datetime!")
                        st.rerun()
                    except:
                        st.error("Could not convert column to datetime")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            date_col = st.selectbox("Date Column", date_cols)
        with col2:
            value_col = st.selectbox("Value Column", numeric_cols)
        
        # إعداد البيانات
        ts_df = df[[date_col, value_col]].copy()
        ts_df = ts_df.sort_values(date_col)
        
        # مخطط السلاسل الزمنية
        fig = px.line(ts_df, x=date_col, y=value_col, title=f"Time Series: {value_col}")
        
        # إضافة متوسط متحرك
        if st.checkbox("Show Moving Average"):
            window = st.slider("Moving Average Window", 3, 50, 7)
            ts_df['moving_avg'] = ts_df[value_col].rolling(window=window).mean()
            fig.add_scatter(x=ts_df[date_col], y=ts_df['moving_avg'], 
                          name=f'Moving Average ({window} days)')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def basic_charts(self, df, chart_type):
        """المخططات الأساسية"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if chart_type == "Histogram":
            if numeric_cols:
                col = st.selectbox("Select Column", numeric_cols, key='hist_col')
                bins = st.slider("Number of Bins", 5, 100, 20, key='hist_bins')
                fig = px.histogram(df, x=col, nbins=bins, title=f"Histogram of {col}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No numeric columns for histogram")
        
        elif chart_type == "Bar Chart":
            x_col = st.selectbox("X Axis (Categorical)", categorical_cols if categorical_cols else df.columns, key='bar_x')
            y_col = st.selectbox("Y Axis (Numeric)", numeric_cols, key='bar_y')
            
            if categorical_cols:
                fig = px.bar(df, x=x_col, y=y_col, title=f"Bar Chart: {y_col} by {x_col}")
            else:
                # إذا لم توجد أعمدة فئوية، استخدم التجميع
                agg_df = df.groupby(x_col)[y_col].mean().reset_index()
                fig = px.bar(agg_df, x=x_col, y=y_col, title=f"Bar Chart: Average {y_col} by {x_col}")
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Box Plot":
            if numeric_cols:
                col = st.selectbox("Select Column for Box Plot", numeric_cols, key='box_col')
                group_by = st.selectbox("Group By (Optional)", [None] + categorical_cols, key='box_group')
                
                if group_by:
                    fig = px.box(df, x=group_by, y=col, title=f"Box Plot of {col} by {group_by}")
                else:
                    fig = px.box(df, y=col, title=f"Box Plot of {col}")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No numeric columns for box plot")
        
        elif chart_type == "Violin Plot":
            if numeric_cols:
                col = st.selectbox("Select Column for Violin Plot", numeric_cols, key='violin_col')
                fig = px.violin(df, y=col, title=f"Violin Plot of {col}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No numeric columns for violin plot")
        
        elif chart_type == "Pair Plot":
            if len(numeric_cols) >= 2:
                selected_cols = st.multiselect("Select columns for pair plot", numeric_cols, default=numeric_cols[:3], key='pair_cols')
                if len(selected_cols) >= 2:
                    fig = px.scatter_matrix(df[selected_cols], title="Pair Plot")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Select at least 2 columns for pair plot")
            else:
                st.warning("Need at least 2 numeric columns for pair plot")