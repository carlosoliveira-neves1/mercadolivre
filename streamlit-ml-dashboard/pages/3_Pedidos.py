# pages/3_Pedidos.py
import streamlit as st
import pandas as pd
from db import fetchall
from export import to_xlsx_bytes
from auth import require_login
from cdc_ui import cdc_header

st.set_page_config(layout='wide')
cdc_header()
require_login()

st.header('Pedidos')

# ----------------------------------
# Filtros
# ----------------------------------
row1 = st.columns([1,1,1,1.2])
dini = row1[0].date_input("De (data do pedido)", value=None)
dfim = row1[1].date_input("Até (data do pedido)", value=None)

status = row1[2].selectbox(
    "Status",
    ["Todos", "paid", "cancelled", "delivered", "to_be_agreed", "partially_paid", "payment_required"]
)

order_id_search = row1[3].text_input("ID do pedido (opcional)")

row2 = st.columns([1,1,1])
somente_pagos = row2[0].checkbox(
    "Somente pagos (atalho)",
    value=False,
    help="Marca esse atalho para filtrar apenas pedidos com status 'paid'."
)
min_val = row2[1].number_input(
    "Valor mínimo (R$)", min_value=0.0, value=0.0, step=10.0,
    help="Deixe 0 para não aplicar mínimo."
)
max_val = row2[2].number_input(
    "Valor máximo (R$)", min_value=0.0, value=0.0, step=10.0,
    help="Deixe 0 para não aplicar máximo."
)

# ----------------------------------
# Monta consulta
#  - order_id sai como texto (16 dígitos, sem '#')
# ----------------------------------
sql = """
SELECT
  CAST(id AS CHAR)   AS order_id,
  date_created,
  status,
  total_amount,
  buyer_id
FROM orders
WHERE 1=1
"""
params = []

# datas
if dini:
    sql += " AND date_created >= %s"
    params.append(f"{dini} 00:00:00")
if dfim:
    sql += " AND date_created <= %s"
    params.append(f"{dfim} 23:59:59")

# status (atalho tem prioridade)
if somente_pagos:
    sql += " AND status = %s"
    params.append("paid")
elif status != "Todos":
    sql += " AND status = %s"
    params.append(status)

# id do pedido (texto, sem '#')
if order_id_search.strip():
    sql += " AND CAST(id AS CHAR) LIKE %s"
    params.append(f"%{order_id_search.strip()}%")

# filtros por valor
if min_val and float(min_val) > 0:
    sql += " AND total_amount >= %s"
    params.append(float(min_val))
if max_val and float(max_val) > 0:
    sql += " AND total_amount <= %s"
    params.append(float(max_val))

sql += " ORDER BY date_created DESC"

rows = fetchall(sql, tuple(params))
df = pd.DataFrame(rows)

# Garante que o ID apareça como texto (evita notação científica)
if not df.empty:
    df["order_id"] = df["order_id"].astype(str)

# ----------------------------------
# Métricas rápidas
# ----------------------------------
colm1, colm2, colm3 = st.columns(3)
colm1.metric("Qtde. de pedidos", len(df))
total_sum = float(df['total_amount'].fillna(0).sum()) if len(df) else 0.0
colm2.metric("Faturamento (soma)", f"R$ {total_sum:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
ticket = (total_sum / len(df)) if len(df) else 0.0
colm3.metric("Ticket médio", f"R$ {ticket:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))

# ----------------------------------
# Exportar e tabela
# ----------------------------------
st.download_button(
    "Exportar Pedidos (Excel)",
    data=to_xlsx_bytes(df, "Pedidos"),
    file_name="pedidos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# Reordena para mostrar o ID primeiro
cols = ["order_id", "date_created", "status", "total_amount", "buyer_id"]
cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
st.dataframe(df[cols], use_container_width=True, height=650)
