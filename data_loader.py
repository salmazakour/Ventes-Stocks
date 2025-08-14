
import os
import io
import pandas as pd
import streamlit as st

# Convert uploaded files to bytes so caching can hash them reliably
@st.cache_data
def load_data(sales_file, stock_file):
    def read_any(file):
        if file is None:
            return pd.DataFrame()

        # If the user passed a local path string (useful for local dev)
        if isinstance(file, str):
            filename = file
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.xlsx', '.xls']:
                # for .xlsx we prefer openpyxl
                engine = 'openpyxl' if ext == '.xlsx' else None
                return pd.read_excel(filename, engine=engine)
            elif ext == '.csv':
                try:
                    return pd.read_csv(filename, encoding='utf-8', low_memory=False)
                except UnicodeDecodeError:
                    return pd.read_csv(filename, encoding='latin1', low_memory=False)
            else:
                st.error(f"Format non supporté (local path): {ext}")
                return pd.DataFrame()

        # Otherwise assume Streamlit UploadedFile or file-like object
        # Make sure we read bytes and create a fresh BytesIO
        try:
            # move pointer to start and read bytes
            file.seek(0)
        except Exception:
            pass
        content = file.read()
        if content is None:
            return pd.DataFrame()

        filename = getattr(file, "name", "uploaded")
        ext = os.path.splitext(filename)[1].lower()
        bio = io.BytesIO(content)

        if ext in ['.xlsx', '.xls']:
            # require openpyxl for .xlsx; .xls may work with xlrd depending on server
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
            try:
                return pd.read_excel(bio, engine=engine)
            except Exception as e:
                st.error(f"Erreur lecture Excel ({filename}): {e}")
                return pd.DataFrame()

        elif ext == '.csv':
            # try utf-8 then fallback
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('latin1')
                except Exception as e:
                    st.error(f"Erreur décodage CSV ({filename}): {e}")
                    return pd.DataFrame()
            return pd.read_csv(io.StringIO(text), low_memory=False)

        else:
            st.error(f"Format de fichier non supporté : {ext}")
            return pd.DataFrame()

    sales = read_any(sales_file)
    stock = read_any(stock_file)

    # Defensive: if columns exist -> normalize them
    if 'Date_Time' in sales.columns:
        sales['Date_Time'] = pd.to_datetime(sales['Date_Time'], errors='coerce')

    if 'Date_Stamp' in stock.columns:
        stock['Date_Stamp'] = pd.to_datetime(stock['Date_Stamp'], errors='coerce')

    if 'Product_Code' in sales.columns:
        sales['Product_Code'] = sales['Product_Code'].astype(str).str.replace(r'\.0$', '', regex=True)

    if 'Product_Code' in stock.columns:
        stock['Product_Code'] = stock['Product_Code'].astype(str).str.replace(r'\.0$', '', regex=True)

    return sales, stock


