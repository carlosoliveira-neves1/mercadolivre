import streamlit as st
from db import fetchall, execute
from auth import require_admin
from passlib.hash import bcrypt
from cdc_ui import cdc_header

st.set_page_config(layout='wide'); cdc_header(); admin=require_admin()
st.header('Administração • Usuários')
tab1, tab2 = st.tabs(['Usuários','Criar usuário'])
with tab1:
    rows=fetchall('SELECT id, username, role, active, created_at FROM users ORDER BY id')
    st.dataframe(rows, use_container_width=True)
    col1,col2,col3=st.columns(3)
    uid = col1.number_input('ID do usuário', min_value=1, step=1)
    if col2.button('Inativar'): execute('UPDATE users SET active=0 WHERE id=%s',(uid,)); st.success('Usuário inativado.')
    if col3.button('Ativar'):   execute('UPDATE users SET active=1 WHERE id=%s',(uid,)); st.success('Usuário ativado.')
with tab2:
    with st.form('novo_user'):
        u=st.text_input('Usuário'); p=st.text_input('Senha', type='password'); role=st.selectbox('Papel',['viewer','admin']); ok=st.form_submit_button('Criar')
    if ok:
        if not u or not p: st.error('Preencha os campos.');
        else:
            try:
                execute('INSERT INTO users (username,password_hash,role) VALUES (%s,%s,%s)', (u, bcrypt.hash(p), role))
                st.success('Usuário criado.')
            except Exception as e:
                st.error(f'Erro: {e}')
