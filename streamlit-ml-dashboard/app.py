# streamlit-ml-dashboard/app.py
import os
import re
import sys
import subprocess
import pandas as pd
import streamlit as st

from auth import ensure_setup_user, require_login
from db import init_extra_tables, fetchall
from cdc_ui import cdc_header

# -----------------------------------------------------------------------------
# Config & Header
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Casa do Cigano • ML Dashboard", layout="wide")
cdc_header()

# -----------------------------------------------------------------------------
# Setup / Login
# -----------------------------------------------------------------------------
ensure_setup_user()     # cria usuário admin se não existir
init_extra_tables()     # garante tabelas extras (users, stock_prefs, etc.)
user = require_login()  # bloqueia acesso sem login

# -----------------------------------------------------------------------------
# Util: resolver caminho do scripts/sync_ml.py (local vs Streamlit Cloud)
# -----------------------------------------------------------------------------
def resolve_sync_path() -> str:
    """
    - Local:      streamlit run app.py dentro de streamlit-ml-dashboard  -> 'scripts/sync_ml.py'
    - Cloud:      cwd é a raiz do repositório                           -> 'streamlit-ml-dashboard/scripts/sync_ml.py'
    """
    local_path = os.path.join("scripts", "sync_ml.py")
    repo_path  = os.path.join("streamlit-ml-dashboard", "scripts", "sync_ml.py")
    if os.path.exists(local_path):
        return local_path
    if os.path.exists(repo_path):
        return repo_path
    return repo_path  # fallback

# -----------------------------------------------------------------------------
# Sidebar: Atualização manual
# -----------------------------------------------------------------------------
st.sidebar.markdown("## ⚡ Atualização")
if st.sidebar.button("🔄 Atualizar agora"):
    sync_path = resolve_sync_path()
    try:
        with st.spinner(f"Sincronizando dados do Mercado Livre...\n(script: {sync_path})"):
            # Usa o MESMO interpretador do app (evita 'No module named requests' na Cloud)
            result = subprocess.run(
                [sys.executable, sync_path],
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

# -----------------------------------------------------------------------------
# Visão Geral
# -----------------------------------------------------------------------------
st.title("Visão Geral")

# -------- Pedidos (amostra) com normalização do ID (16 dígitos) --------
orders = fetchall("""
    SELECT id, date_created, status, total_amount
    FROM orders
    ORDER BY date_created DESC
    LIMIT 500
""")

def clean_order_id(v: str) -> str:
    s = re.sub(r"\D", "", str(v or ""))
    return s[:16] if len(s) >= 16 else s

orders_df = pd.DataFrame(orders)
if not orders_df.empty and "id" in orders_df.columns:
    orders_df.insert(0, "order_id", orders_df.pop("id").map(clean_order_id))
    orders_df.rename(columns={"order_id": "id"}, inplace=True)

# -------- Produtos (amostra) --------
items = fetchall("""
    SELECT id, title, price, available_quantity
    FROM items
    ORDER BY title
    LIMIT 500
""")

# KPIs
tot_orders = len(orders_df)
tot_items  = len(items)
tot_amount = 0.0
if not orders_df.empty and "total_amount" in orders_df.columns:
    tot_amount = float(pd.to_numeric(orders_df["total_amount"], errors="coerce").fillna(0).sum())

# Cards
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
    f'<div class="cdc-card"><h4>Faturamento (amostra)</h4><div class="v">R$ {tot_amount:,.2f}</div></div>'
    .replace(',', 'X').replace('.', ',').replace('X','.'),
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# Tabelas rápidas
col1, col2 = st.columns(2)
with col1:
    st.subheader("Pedidos recentes")
    st.dataframe(orders_df, use_container_width=True, height=360)
with col2:
    st.subheader("Produtos (amostra)")
    st.dataframe(pd.DataFrame(items), use_container_width=True, height=360)

st.info(
    "Use o menu **Pages** (à esquerda) para acessar **Produtos/Estoque**, **Pedidos**, "
    "**Relatório de Alertas** e **Administração**."
)
