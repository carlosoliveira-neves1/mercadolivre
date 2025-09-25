# Casa do Cigano • Dashboard Mercado Livre (Streamlit)

Este projeto é um dashboard em Streamlit que se conecta à API do Mercado Livre.

## Funcionalidades
- Consulta produtos, estoque, pedidos e vendas.
- Sincronização automática a cada 30 minutos (GitHub Actions).
- Botão "Atualizar agora" para sincronização manual.
- Administração de usuários e limites de estoque.
- Exporta relatórios para Excel.

## Como rodar
1) Copie `.streamlit/secrets.template.toml` para `.streamlit/secrets.toml` e preencha.
2) Crie venv e instale:
   - `py -3.11 -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
   - `pip install -r requirements.txt`
3) `streamlit run app.py`

## GitHub Actions
Configure os secrets: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, ML_CLIENT_ID, ML_CLIENT_SECRET, ML_REFRESH_TOKEN.
