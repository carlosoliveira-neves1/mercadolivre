import mysql.connector, streamlit as st

def get_conn():
    cfg=dict(host=st.secrets.get('MYSQL_HOST'), port=int(st.secrets.get('MYSQL_PORT',3306)),
             user=st.secrets.get('MYSQL_USER'), password=st.secrets.get('MYSQL_PASSWORD'),
             database=st.secrets.get('MYSQL_DB'), autocommit=True)
    return mysql.connector.connect(**cfg)

def fetchall(sql, params=None):
    conn=get_conn(); cur=conn.cursor(dictionary=True)
    cur.execute(sql, params or ()); rows=cur.fetchall()
    cur.close(); conn.close(); return rows

def execute(sql, params=None, many=False):
    conn=get_conn(); cur=conn.cursor()
    cur.executemany(sql, params) if many and isinstance(params,list) else cur.execute(sql, params or ())
    conn.commit(); cur.close(); conn.close()

def init_extra_tables():
    execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INT PRIMARY KEY AUTO_INCREMENT,
      username VARCHAR(80) UNIQUE,
      password_hash VARCHAR(255),
      role ENUM('admin','viewer') DEFAULT 'viewer',
      active TINYINT DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    execute("""
    CREATE TABLE IF NOT EXISTS stock_limits (
      product_id VARCHAR(30) PRIMARY KEY,
      min_qty INT DEFAULT 0,
      max_qty INT DEFAULT 0,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
