# pages/6_Relatorio_Alertas.py
import streamlit as st, pandas as pd
from auth import require_login
from db import fetchall
from cdc_ui import cdc_header

st.set_page_config(layout='wide')
cdc_header()
require_login()

st.header('Relatório de Alertas de Estoque')

# Filtros
col1, col2, col3 = st.columns([1,1,2])
status_filter = col1.selectbox('Filtrar por status', [
    'Todos','ABAIXO do mínimo','Próximo do mínimo','Próximo do máximo','ACIMA do máximo','OK'
])
dini = col2.date_input("Sincronizado a partir de", value=None)
dfim = col3.date_input("Sincronizado até", value=None)

# Busca itens + limites (força a mesma collation no JOIN)
sql = """
SELECT
  i.id,
  i.title,
  i.available_quantity,
  i.last_sync_at,
  COALESCE(sl.min_qty,0) AS min_qty,
  COALESCE(sl.max_qty,0) AS max_qty
FROM items i
LEFT JOIN stock_limits sl
  ON sl.product_id COLLATE utf8mb4_unicode_ci = i.id COLLATE utf8mb4_unicode_ci
WHERE 1=1
"""
params = []
if dini:
    sql += " AND i.last_sync_at >= %s"
    params.append(f"{dini} 00:00:00")
if dfim:
    sql += " AND i.last_sync_at <= %s"
    params.append(f"{dfim} 23:59:59")

rows = fetchall(sql, tuple(params))

# Calcula status
out = []
for r in rows:
    avail = r['available_quantity'] or 0
    minq  = r['min_qty'] or 0
    maxq  = r['max_qty'] or 0
    faixa = max(1, maxq - minq) if maxq > minq else 1
    near  = max(1, int(0.1 * faixa))

    status = 'OK'
    if maxq and avail >= maxq:
        status = 'ACIMA do máximo'
    elif minq and avail <= minq:
        status = 'ABAIXO do mínimo'
    elif minq and avail <= (minq + near):
        status = 'Próximo do mínimo'
    elif maxq and avail >= (maxq - near):
        status = 'Próximo do máximo'

    out.append({
        'product_id': r['id'],
        'title': r['title'],
        'available': avail,
        'min_qty': minq,
        'max_qty': maxq,
        'status': status,
        'last_sync_at': r['last_sync_at'],
    })

df = pd.DataFrame(out)
if status_filter != 'Todos':
    df = df[df['status'] == status_filter]

st.dataframe(df.sort_values(['status','title']), use_container_width=True, height=680)
