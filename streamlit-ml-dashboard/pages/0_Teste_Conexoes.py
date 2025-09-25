# streamlit-ml-dashboard/pages/0_Teste_Conexoes.py
import os
import time
import json
import requests
import mysql.connector
import streamlit as st

st.set_page_config(layout="wide")
st.title("🔎 Teste de Conexões (MySQL & Mercado Livre)")

# Util
def ok(msg): st.success(f"✅ {msg}")
def fail(msg, err=None):
    st.error(f"❌ {msg}")
    if err:
        st.code(str(err))

# -------- MySQL --------
st.subheader("MySQL")
try:
    cfg = dict(
        host=st.secrets["MYSQL_HOST"],
        port=int(st.secrets.get("MYSQL_PORT", 3306)),
        user=st.secrets["MYSQL_USER"],
        password=st.secrets["MYSQL_PASSWORD"],
        database=st.secrets["MYSQL_DB"],
        autocommit=True,
        connection_timeout=10,
    )
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    cur.execute("SELECT VERSION()")
    version = cur.fetchone()[0]
    cur.execute("SELECT 1")
    cur.fetchone()
    cur.close(); conn.close()
    ok(f"Conectou no MySQL ({version}) e SELECT 1 OK.")
except Exception as e:
    fail("Falha ao conectar no MySQL.", e)

st.divider()

# -------- Mercado Livre --------
st.subheader("Mercado Livre (OAuth + /users/me)")
try:
    client_id = st.secrets["ML_CLIENT_ID"]
    client_secret = st.secrets["ML_CLIENT_SECRET"]
    refresh_token = st.secrets["ML_REFRESH_TOKEN"]

    # refresh token
    t0 = time.time()
    resp = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data=dict(
            grant_type="refresh_token",
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        ),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in")
    dt = time.time() - t0
    # não exibir token inteiro
    token_preview = (access_token[:12] + "…") if access_token else "N/D"
    ok(f"Refresh token OK em {dt:.2f}s • access_token: {token_preview} • expires_in: {expires_in}s")

    # /users/me
    me = requests.get(
        "https://api.mercadolibre.com/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    me.raise_for_status()
    me_json = me.json()
    st.json({"users/me": {"id": me_json.get("id"), "nickname": me_json.get("nickname")}})
    ok("GET /users/me OK.")
except requests.HTTPError as e:
    # mostra corpo de erro da API para facilitar
    try:
        st.code(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception:
        pass
    fail("Erro HTTP na integração Mercado Livre.", e)
except Exception as e:
    fail("Falha geral na integração Mercado Livre.", e)

st.info("Se ambos os blocos acima estiverem verdes, suas credenciais e rede estão OK.")
