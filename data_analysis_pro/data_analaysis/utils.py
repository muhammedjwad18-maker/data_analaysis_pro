import pandas as pd
import numpy as np
import re
from pathlib import Path
import streamlit as st
from scipy import stats

class FileProcessor:
    def __init__(self):
        self.supported_types = {
            'csv': pd.read_csv,
            'xlsx': pd.read_excel, 
            'json': pd.read_json,
            'parquet': pd.read_parquet
        }
    
    def process_uploaded_file(self, uploaded_file):
        """معالجة الملف المرفوع"""
        try:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type not in self.supported_types:
                st.error(f"Unsupported file type: {file_type}")
                return None
            
            # قراءة الملف
            if file_type == 'csv':
                df = pd.read_csv(uploaded_file, encoding_errors='ignore')
            elif file_type == 'xlsx':
                df = pd.read_excel(uploaded_file)
            elif file_type == 'json':
                df = pd.read_json(uploaded_file)
            elif file_type == 'parquet':
                df = pd.read_parquet(uploaded_file)
            
            # التنظيف الأساسي
            df = self.clean_dataframe(df)
            
            return df
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None
    
    def clean_dataframe(self, df):
        """تنظيف DataFrame الأساسي"""
        # إزالة الأعمدة الفارغة بالكامل
        df = df.dropna(axis=1, how='all')
        
        # تحويل أسماء الأعمدة إلى صيغة قياسية
        df.columns = [self.clean_column_name(col) for col in df.columns]
        
        return df
    
    def clean_column_name(self, name):
        """تنظيف اسم العمود"""
        if not isinstance(name, str):
            name = str(name)
        
        # إزالة المسافات الزائدة والرموز الخاصة
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name.strip())
        
        return name.lower()

class DataCleaner:
    def __init__(self):
        pass
    
    def handle_missing_values(self, df, strategy='mean'):
        """معالجة القيم المفقودة"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if strategy == 'mean':
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        elif strategy == 'median':
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        elif strategy == 'drop':
            df = df.dropna()
        
        return df
    
    def remove_duplicates(self, df):
        """إزالة التكرارات"""
        return df.drop_duplicates()
    
    def detect_anomalies(self, df, threshold=3):
        """كشف الشذوذ باستخدام Z-score"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            anomalies = z_scores > threshold
            df[f'{col}_anomaly'] = anomalies
        
        return df