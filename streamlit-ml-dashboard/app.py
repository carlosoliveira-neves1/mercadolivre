import sys, subprocess, datetime, decimal
import streamlit as st, pandas as pd
from auth import ensure_setup_user, require_login
from db import init_extra_tables, fetchall
from cdc_ui import cdc_header

st.set_page_config(page_title='Casa do Cigano • ML Dashboard', layout='wide')
cdc_header()

# ------------ Sanitizador (evita erro React #185) ------------
def _clean_rows(rows):
    safe = []
    for r in rows or []:
        o = {}
        for k, v in r.items():
            if isinstance(v, decimal.Decimal):
                o[k] = float(v)
            elif isinstance(v, (datetime.datetime, datetime.date)):
                o[k] = v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime.datetime) else v.isoformat()
            elif isinstance(v, (dict, list, set, tuple)):
                o[k] = str(v)
            else:
                o[k] = v
        safe.append(o)
    return safe
# --------------------------------------------------------------

# bootstrap / auth
ensure_setup_user()
init_extra_tables()
user = require_login()

# --- botão de sincronização (usa o python da venv via sys.executable)
st.sidebar.markdown('## ⚡ Atualização')
if st.sidebar.button('🔄 Atualizar agora', use_container_width=True):
    try:
        with st.spinner('Sincronizando dados do Mercado Livre...'):
            # <<< correção principal aqui >>>
            result = subprocess.run([sys.executable, 'scripts/sync_ml.py'], capture_output=True, text=True)
        if result.returncode == 0:
            st.success('Sincronização concluída com sucesso.')
            st.code(result.stdout or 'OK', language='bash')
        else:
            st.error('Falha na sincronização.')
            st.code((result.stdout or '') + '\n' + (result.stderr or ''), language='bash')
    except Exception as e:
        st.error(f'Erro ao sincronizar: {e}')

# -------------------- VISÃO GERAL --------------------
st.title('Visão Geral')

orders_raw = fetchall(
    'SELECT id, date_created, status, total_amount, buyer_id '
    'FROM orders ORDER BY date_created DESC LIMIT 500'
)
items_raw = fetchall(
    'SELECT id, title, price, available_quantity '
    'FROM items ORDER BY title LIMIT 500'
)

orders = _clean_rows(orders_raw)
items  = _clean_rows(items_raw)

tot_orders = len(orders)
tot_items  = len(items)
tot_amount = sum(float(o.get('total_amount') or 0) for o in orders)

# cards
st.markdown('<div class="cdc-cards">', unsafe_allow_html=True)
st.markdown(f'<div class="cdc-card"><h4>Pedidos (amostra 500)</h4><div class="v">{tot_orders}</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="cdc-card"><h4>Produtos (amostra)</h4><div class="v">{tot_items}</div></div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="cdc-card"><h4>Faturamento (amostra)</h4><div class="v">R$ {tot_amount:,.2f}</div></div>'
    .replace(',', 'X').replace('.', ',').replace('X','.'), unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- GRÁFICOS --------------------
st.markdown("### Indicadores gráficos")

# Filtros simples de período (para os gráficos)
colf1, colf2 = st.columns([1,1])
with colf1:
    dias = st.slider("Período (últimos N dias)", min_value=7, max_value=180, value=30, step=1)
with colf2:
    top_n = st.slider("Top produtos (por faturamento)", min_value=5, max_value=30, value=10, step=1)

# 1) Vendas por dia (somatório de total_amount)
sales_rows = fetchall("""
    SELECT DATE(date_created) as d, SUM(total_amount) as total
    FROM orders
    WHERE date_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
      AND status NOT IN ('cancelled')
    GROUP BY DATE(date_created)
    ORDER BY d
""", (dias,))

sales_df = pd.DataFrame(_clean_rows(sales_rows))
if not sales_df.empty:
    sales_df["d"] = pd.to_datetime(sales_df["d"], errors="coerce")
    sales_df["total"] = pd.to_numeric(sales_df["total"], errors="coerce").fillna(0.0)
else:
    sales_df = pd.DataFrame({"d":[], "total":[]})

# 2) Top produtos por faturamento (order_items × orders × items)
top_rows = fetchall("""
    SELECT oi.item_id, i.title,
           SUM(oi.quantity * oi.unit_price) AS revenue,
           SUM(oi.quantity) AS qty
    FROM order_items oi
    JOIN orders o   ON o.id = oi.order_id
    LEFT JOIN items i ON i.id = oi.item_id
    WHERE o.date_created >= DATE_SUB(NOW(), INTERVAL %s DAY)
      AND o.status NOT IN ('cancelled')
    GROUP BY oi.item_id, i.title
    ORDER BY revenue DESC
    LIMIT %s
""", (dias, top_n))

top_df = pd.DataFrame(_clean_rows(top_rows))
if not top_df.empty:
    for c in ["revenue","qty"]:
        if c in top_df.columns:
            top_df[c] = pd.to_numeric(top_df[c], errors="coerce").fillna(0.0)

g1, g2 = st.columns([2,1.6])

with g1:
    st.subheader("Vendas por dia (R$)")
    if sales_df.empty:
        st.info("Sem dados no período escolhido.")
    else:
        st.line_chart(sales_df.set_index("d")["total"], height=280)

with g2:
    st.subheader(f"Top {top_n} produtos (R$)")
    if top_df.empty:
        st.info("Sem dados para o período.")
    else:
        top_plot = top_df.sort_values("revenue", ascending=True)
        top_plot.index = top_plot["title"].fillna(top_plot["item_id"]).astype(str)
        st.bar_chart(top_plot["revenue"], height=280)

# -------------------- TABELAS --------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader('Pedidos recentes')
    try:
        df = pd.DataFrame(orders)
        cols = [c for c in ["id","date_created","status","total_amount","buyer_id"] if c in df.columns]
        if cols: df = df[cols]
        st.dataframe(df, use_container_width=True, height=360)
    except Exception as e:
        st.error("Falha ao renderizar pedidos.")
        st.exception(e)

with col2:
    st.subheader('Produtos (amostra)')
    try:
        df2 = pd.DataFrame(items)
        cols = [c for c in ["id","title","price","available_quantity"] if c in df2.columns]
        if cols: df2 = df2[cols]
        st.dataframe(df2, use_container_width=True, height=360)
    except Exception as e:
        st.error("Falha ao renderizar produtos.")
        st.exception(e)

st.info('Use o menu lateral para navegar: **Produtos/Estoque, Pedidos, Relatório de Alertas e Administração.**')
