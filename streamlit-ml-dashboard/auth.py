import streamlit as st
from passlib.hash import bcrypt
from db import fetchall, execute, init_extra_tables

def ensure_setup_user():
    init_extra_tables()
    cnt=fetchall('SELECT COUNT(*) n FROM users')[0]['n']
    if cnt==0:
        st.info('Nenhum usuário encontrado. Crie o administrador inicial:')
        with st.form('create_admin'):
            u=st.text_input('Usuário (admin)')
            p=st.text_input('Senha', type='password')
            ok=st.form_submit_button('Criar admin')
        if ok:
            if not u or not p: st.error('Preencha usuário e senha.'); st.stop()
            execute('INSERT INTO users (username, password_hash, role) VALUES (%s,%s,\'admin\')', (u, bcrypt.hash(p)))
            st.success('Administrador criado. Faça login.'); st.stop()

def login_form():
    st.sidebar.header('Login')
    u=st.sidebar.text_input('Usuário'); p=st.sidebar.text_input('Senha', type='password')
    if st.sidebar.button('Entrar'):
        rows=fetchall('SELECT * FROM users WHERE username=%s AND active=1', (u,))
        if not rows: st.sidebar.error('Usuário não encontrado ou inativo.'); return None
        row=rows[0]
        if bcrypt.verify(p, row['password_hash']):
            st.session_state['user']={'id':row['id'],'username':row['username'],'role':row['role']}
            st.sidebar.success(f"Bem-vindo, {row['username']}"); return st.session_state['user']
        else: st.sidebar.error('Senha incorreta.')
    return None

def require_login():
    if 'user' not in st.session_state:
        login_form()
        if 'user' not in st.session_state: st.stop()
    return st.session_state['user']

def require_admin():
    u=require_login()
    if u['role']!='admin': st.error('Acesso restrito ao administrador.'); st.stop()
    return u
