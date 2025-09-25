import streamlit as st, pandas as pd
from db import fetchall, execute
from auth import require_admin
from cdc_ui import cdc_header

st.set_page_config(layout='wide'); cdc_header(); admin=require_admin()
st.header('Administração • Estoque mínimo e máximo por produto')
items = fetchall('SELECT id, title, available_quantity FROM items ORDER BY title LIMIT 5000')
limits = {r['product_id']: r for r in fetchall('SELECT product_id,min_qty,max_qty FROM stock_limits')}
rows=[]
for it in items:
    lim = limits.get(it['id'], {'min_qty':0,'max_qty':0})
    rows.append({'product_id':it['id'],'title':it['title'],'available':it['available_quantity'],'min_qty':lim['min_qty'],'max_qty':lim['max_qty']})
df=pd.DataFrame(rows)
st.caption('Edite os mínimos e máximos e clique em **Salvar**.')
edited = st.data_editor(df, use_container_width=True, num_rows='dynamic', key='editor')
if st.button('Salvar'):
    recs = edited[['product_id','min_qty','max_qty']].fillna(0).to_dict(orient='records')
    for r in recs:
        execute("""
        INSERT INTO stock_limits (product_id,min_qty,max_qty) VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE min_qty=VALUES(min_qty), max_qty=VALUES(max_qty)
        """, (r['product_id'], int(r['min_qty']), int(r['max_qty'])))
    st.success('Limites salvos com sucesso.')
