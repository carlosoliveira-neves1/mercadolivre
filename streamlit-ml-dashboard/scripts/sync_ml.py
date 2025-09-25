import os, json, requests, mysql.connector

def read_secrets_toml():
    paths=[os.path.join(os.getcwd(),'.streamlit','secrets.toml'), os.path.join(os.path.expanduser('~'),'.streamlit','secrets.toml')]
    try:
        import tomllib
        for p in paths:
            if os.path.isfile(p):
                with open(p,'rb') as f: return tomllib.load(f)
    except Exception:
        try:
            import tomli
            for p in paths:
                if os.path.isfile(p):
                    with open(p,'rb') as f: return tomli.load(f)
        except Exception:
            pass
    return {}

SECRETS = read_secrets_toml()
def get_secret(name, default=None): return os.environ.get(name) or SECRETS.get(name, default)

MYSQL = dict(host=get_secret('MYSQL_HOST'), port=int(get_secret('MYSQL_PORT',3306)), user=get_secret('MYSQL_USER'), password=get_secret('MYSQL_PASSWORD'), database=get_secret('MYSQL_DB'), autocommit=True)
ML_CLIENT_ID = get_secret('ML_CLIENT_ID'); ML_CLIENT_SECRET = get_secret('ML_CLIENT_SECRET'); ML_REFRESH_TOKEN = get_secret('ML_REFRESH_TOKEN')

def assert_configs():
    missing=[k for k,v in {'MYSQL_HOST':MYSQL['host'],'MYSQL_USER':MYSQL['user'],'MYSQL_PASSWORD':MYSQL['password'],'MYSQL_DB':MYSQL['database'],'ML_CLIENT_ID':ML_CLIENT_ID,'ML_CLIENT_SECRET':ML_CLIENT_SECRET,'ML_REFRESH_TOKEN':ML_REFRESH_TOKEN}.items() if not v]
    if missing: raise RuntimeError('Config ausente: '+', '.join(missing)+'\n→ Preencha .streamlit/secrets.toml ou defina variáveis de ambiente.')

def get_conn(): return mysql.connector.connect(**MYSQL)

def upsert_order(cur, o):
    cur.execute("""
        INSERT INTO orders (id, date_created, status, total_amount, buyer_id, raw, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,NOW())
        ON DUPLICATE KEY UPDATE status=VALUES(status), total_amount=VALUES(total_amount), raw=VALUES(raw), updated_at=NOW()
    """, (o['id'], (o.get('date_created') or '').replace('T',' ').replace('Z',''), o.get('status'), o.get('total_amount'), (o.get('buyer') or {}).get('id'), json.dumps(o, ensure_ascii=False)))
    for it in (o.get('order_items') or []):
        item_id=((it.get('item') or {}).get('id'))
        cur.execute("""
            INSERT INTO order_items (order_id, item_id, quantity, unit_price)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE quantity=VALUES(quantity), unit_price=VALUES(unit_price)
        """, (o['id'], item_id, it.get('quantity',0), it.get('unit_price',0.0)))

def upsert_item(cur, r):
    cur.execute("""
        INSERT INTO items (id, title, price, currency_id, available_quantity, status, permalink, last_sync_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())
        ON DUPLICATE KEY UPDATE title=VALUES(title), price=VALUES(price), currency_id=VALUES(currency_id),
            available_quantity=VALUES(available_quantity), status=VALUES(status), permalink=VALUES(permalink), last_sync_at=NOW()
    """, (r['id'], r.get('title'), r.get('price'), r.get('currency_id'), r.get('available_quantity'), r.get('status'), r.get('permalink')))

def refresh_token():
    resp=requests.post('https://api.mercadolibre.com/oauth/token', data=dict(grant_type='refresh_token', client_id=ML_CLIENT_ID, client_secret=ML_CLIENT_SECRET, refresh_token=ML_REFRESH_TOKEN), headers={'Content-Type':'application/x-www-form-urlencoded'}, timeout=60)
    resp.raise_for_status(); return resp.json()['access_token']

def chunks(lst,n):
    for i in range(0,len(lst),n): yield lst[i:i+n]

def run():
    assert_configs()
    token=refresh_token()
    me=requests.get('https://api.mercadolibre.com/users/me', headers={'Authorization': f'Bearer {token}'}, timeout=60).json()
    seller_id=me['id']; print(f"[ML] seller_id: {seller_id}")
    conn=get_conn(); cur=conn.cursor()
    offset=0; limit=50; total_gravados=0
    while True:
        url=f'https://api.mercadolibre.com/orders/search?seller={seller_id}&sort=date_desc&offset={offset}&limit={limit}'
        resp=requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=60); resp.raise_for_status(); data=resp.json()
        results=data.get('results',[])
        for o in results: upsert_order(cur,o)
        conn.commit(); paging=data.get('paging') or {}; total=int(paging.get('total') or 0)
        total_gravados+=len(results); print(f"[ML] Orders page: +{len(results)} (offset {offset}) / total {total}")
        offset+=limit
        if offset>=total or not results: break
    print(f"[ML] Orders gravados: {total_gravados}")

    offset=0; limit=100; all_ids=[]
    while True:
        url_ids=f'https://api.mercadolibre.com/users/{seller_id}/items/search?offset={offset}&limit={limit}'
        resp_ids=requests.get(url_ids, headers={'Authorization': f'Bearer {token}'}, timeout=60)
        if resp_ids.status_code==403: print('[ML] 403 ao listar itens do vendedor. Verifique escopos/permissões.'); break
        resp_ids.raise_for_status(); data_ids=resp_ids.json(); results_ids=data_ids.get('results',[])
        if not results_ids: break
        all_ids.extend(results_ids); print(f"[ML] Items IDs page: +{len(results_ids)} (offset {offset})")
        offset+=limit
        if len(results_ids)<limit: break

    count=0
    for batch in chunks(all_ids,20):
        ids_str=','.join(batch)
        url_det=f'https://api.mercadolibre.com/items?ids={ids_str}'
        resp_det=requests.get(url_det, headers={'Authorization': f'Bearer {token}'}, timeout=60)
        if resp_det.status_code==403: print('[ML] 403 ao buscar detalhes dos itens. Pulando lote.'); continue
        resp_det.raise_for_status()
        for wrap in resp_det.json():
            body=wrap.get('body') or {}
            if body.get('id'):
                upsert_item(cur, body); count+=1
        conn.commit()

    cur.close(); conn.close(); print(f"[ML] Itens gravados: {count}")

if __name__=='__main__': run()
