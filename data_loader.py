import os
import pandas as pd
import streamlit as st

@st.cache_data
def load_data(sales_path, stock_path):
    def load_file(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.xlsx', '.xls']:
            return pd.read_excel(path)
        elif ext == '.csv':
            try:
                return pd.read_csv(path, encoding='utf-8')
            except UnicodeDecodeError:
                return pd.read_csv(path, encoding='latin1')
        else:
            st.error(f"Format de fichier non supporté : {ext}")
            return pd.DataFrame()

    sales = load_file(sales_path)
    stock = load_file(stock_path)

    if 'Date_Time' in sales.columns:
        sales['Date_Time'] = pd.to_datetime(sales['Date_Time'], errors='coerce')

    if 'Date_Stamp' in stock.columns:
        stock['Date_Stamp'] = pd.to_datetime(stock['Date_Stamp'], errors='coerce')
        

    sales['Product_Code'] = sales['Product_Code'].astype(str).str.replace(r'\.0$', '', regex=True)
    stock['Product_Code'] = stock['Product_Code'].astype(str).str.replace(r'\.0$', '', regex=True)
    return sales, stock

