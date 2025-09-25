# pages/2_Produtos_Estoque.py
import streamlit as st, pandas as pd
from export import to_xlsx_bytes
from auth import require_login
from db import fetchall
from cdc_ui import cdc_header

st.set_page_config(layout='wide')
cdc_header()
require_login()

st.header('Produtos / Estoque')

# Filtros
col1, col2, col3 = st.columns([2,1,1])
q = col1.text_input("Buscar (título ou ID)")
dini = col2.date_input("Sincronizado a partir de", value=None)
dfim = col3.date_input("Sincronizado até", value=None)

sql = """
SELECT
  i.id,
  i.title,
  i.price,
  i.currency_id,
  i.available_quantity,
  i.status,
  i.last_sync_at,
  COALESCE(sl.min_qty,0) AS min_qty,
  COALESCE(sl.max_qty,0) AS max_qty
FROM items i
LEFT JOIN stock_limits sl
  ON sl.product_id COLLATE utf8mb4_unicode_ci = i.id COLLATE utf8mb4_unicode_ci
WHERE 1=1
"""
params = []

if q:
    sql += " AND (i.title COLLATE utf8mb4_unicode_ci LIKE %s OR i.id COLLATE utf8mb4_unicode_ci LIKE %s)"
    params += [f"%{q}%", f"%{q}%"]

if dini:
    sql += " AND i.last_sync_at >= %s"
    params.append(f"{dini} 00:00:00")

if dfim:
    sql += " AND i.last_sync_at <= %s"
    params.append(f"{dfim} 23:59:59")

sql += " ORDER BY i.title"

rows = fetchall(sql, tuple(params))
df = pd.DataFrame(rows)

st.download_button(
    "Exportar Produtos/Estoque (Excel)",
    data=to_xlsx_bytes(df, "Produtos"),
    file_name="produtos_estoque.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.dataframe(df, use_container_width=True, height=650)
