# streamlit-ml-dashboard/app.py
import os
import subprocess
import pandas as pd
import streamlit as st

from auth import ensure_setup_user, require_login
from db import init_extra_tables, fetchall
from cdc_ui import cdc_header

# -----------------------------
# Config & Header
# -----------------------------
st.set_page_config(page_title="Casa do Cigano • ML Dashboard", layout="wide")
cdc_header()

# -----------------------------
# Setup / Login
# -----------------------------
ensure_setup_user()
init_extra_tables()
user = require_login()

# -----------------------------
# Util: resolver caminho do sync
# -----------------------------
def resolve_sync_path() -> str:
    """
    Resolve o caminho do scripts/sync_ml.py em dois cenários:
    - Local (quando você roda "streamlit run app.py" dentro de streamlit-ml-dashboard)
      -> usar "scripts/sync_ml.py"
    - Streamlit Cloud (cwd é a raiz do repositório)
      -> usar "streamlit-ml-dashboard/scripts/sync_ml.py"
    """
    local_path = os.path.join("scripts", "sync_ml.py")
    repo_path = os.path.join("streamlit-ml-dashboard", "scripts", "sync_ml.py")

    if os.path.exists(local_path):
        return local_path
    if os.path.exists(repo_path):
        return repo_path
    # fallback: devolve o repo_path (Cloud)
    return repo_path

# -----------------------------
# Sidebar: Atualização manual
# -----------------------------
st.sidebar.markdown("## ⚡ Atualização")
if st.sidebar.button("🔄 Atualizar agora"):
    sync_path = resolve_sync_path()
    try:
        with st.spinner(f"Sincronizando dados do Mercado Livre...\n(script: {sync_path})"):
            result = subprocess.run(
                ["python", sync_path],
                capture_output=True,
                text=True
            )
        if result.returncode == 0:
            st.success("✅ Sincronização concluída com sucesso.")
            st.code(result.stdout or "OK", language="bash")
            if result.stderr:
                st.caption("Stderr:")
                st.code(result.stderr, language="bash")
        else:
            st.error("❌ Falha na sincronização.")
            st.code((result.stdout or "") + "\n" + (result.stderr or ""), language="bash")
    except Exception as e:
        st.error(f"Erro ao executar o coletor: {e}")

# -----------------------------
# Visão Geral
# -----------------------------
st.title("Visão Geral")

# Pedidos e Itens (amostras)
orders = fetchall("""
    SELECT id, date_created, status, total_amount
    FROM orders
    ORDER BY date_created DESC
    LIMIT 500
""")
items  = fetchall("""
    SELECT id, title, price, available_quantity
    FROM items
    ORDER BY title
    LIMIT 500
""")

# KPIs
tot_orders = len(orders)
tot_items  = len(items)
tot_amount = sum(float(o["total_amount"] or 0) for o in orders)

st.markdown('<div class="cdc-cards">', unsafe_allow_html=True)
st.markdown(
    f'<div class="cdc-card"><h4>Pedidos (amostra 500)</h4><div class="v">{tot_orders}</div></div>',
    unsafe_allow_html=True
)
st.markdown(
    f'<div class="cdc-card"><h4>Produtos (amostra)</h4><div class="v">{tot_items}</div></div>',
    unsafe_allow_html=True
)
st.markdown(
    f'<div class="cdc-card"><h4>Faturamento (amostra)</h4><div class="v">R$ {tot_amount:,.2f}</div></div>'.replace(',', 'X').replace('.', ',').replace('X','.'),
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# Duas colunas com tabelas
col1, col2 = st.columns(2)
with col1:
    st.subheader("Pedidos recentes")
    st.dataframe(pd.DataFrame(orders), use_container_width=True, height=360)

with col2:
    st.subheader("Produtos (amostra)")
    st.dataframe(pd.DataFrame(items), use_container_width=True, height=360)

st.info(
    "Use o menu **Pages** (seta ou ícone de páginas no topo) para acessar: "
    "**Produtos/Estoque**, **Pedidos**, **Relatório de Alertas** e **Administração**."
)
