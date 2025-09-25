import io, pandas as pd
from db import fetchall

def export_orders_df():
    return pd.DataFrame(fetchall('SELECT id, date_created, status, total_amount FROM orders ORDER BY date_created DESC'))

def export_items_df():
    return pd.DataFrame(fetchall('SELECT id, title, price, currency_id, available_quantity, status FROM items ORDER BY title'))

def to_xlsx_bytes(df, sheet='Planilha'):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    buf.seek(0); return buf
