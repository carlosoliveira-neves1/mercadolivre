import streamlit as st
from pathlib import Path

# ====== estilos (tema claro + componentes) ======
def _inject_styles():
    st.markdown(
        """
        <style>
          :root{
            --cdc-primary:#F59E0B;       /* amber */
            --cdc-text:#0F172A;          /* slate-900 */
            --cdc-muted:#64748B;         /* slate-500 */
            --cdc-bg:#F8FAFC;            /* slate-50 */
            --cdc-card:#FFFFFF;          /* white */
            --cdc-border:#E2E8F0;        /* slate-200 */
            --cdc-success:#16A34A;       /* green-600 */
            --cdc-danger:#DC2626;        /* red-600 */
          }

          /* fundo claro */
          .stApp { background-color: var(--cdc-bg); color: var(--cdc-text); }

          /* topbar */
          .cdc-topbar{
            display:flex; align-items:center; gap:14px;
            padding:14px 18px; margin:-20px -15px 18px -15px;
            background:var(--cdc-card);
            border-bottom:1px solid var(--cdc-border);
            position:sticky; top:0; z-index:50;
          }
          .cdc-title{ font-size:18px; font-weight:800; letter-spacing:.2px; color:var(--cdc-text) }
          .cdc-sub{ color:var(--cdc-muted); font-size:13px; margin-top:-2px }
          .cdc-badge{
            background:rgba(245,158,11,.12); color:#92400E;
            border:1px solid rgba(245,158,11,.35);
            font-size:11px; padding:2px 8px; border-radius:999px; margin-left:6px;
          }

          /* grid de métricas */
          .cdc-cards { display:grid; gap:14px; grid-template-columns:repeat(3,1fr); margin:8px 0 18px 0 }
          .cdc-card{
            background:var(--cdc-card); border:1px solid var(--cdc-border);
            border-radius:14px; padding:16px 18px;
            box-shadow:0 1px 2px rgba(16,24,40,.04);
          }
          .cdc-card h4{ margin:0; font-size:13px; color:var(--cdc-muted); display:flex; align-items:center; gap:6px }
          .cdc-card .v{ margin-top:6px; font-weight:800; font-size:26px; color:var(--cdc-text) }
          .cdc-card .fine{ font-size:12px; color:var(--cdc-muted); margin-top:4px }

          /* tooltip */
          .cdc-help{
            display:inline-flex; align-items:center; justify-content:center;
            width:16px; height:16px; border-radius:999px;
            border:1px solid var(--cdc-border); color:var(--cdc-muted);
            font-size:11px; cursor:help; position:relative;
          }
          .cdc-help[data-tip]:hover:after{
            content:attr(data-tip);
            position:absolute; bottom:120%; left:50%; transform:translateX(-50%);
            background:#111827; color:#fff; padding:8px 10px; border-radius:8px;
            font-size:12px; max-width:280px; white-space:normal; box-shadow:0 6px 30px rgba(0,0,0,.25);
          }

          /* sidebar e botões */
          section[data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right:1px solid var(--cdc-border);
          }
          .stButton>button{
            background:var(--cdc-primary) !important; color:#111827 !important;
            border:1px solid rgba(245,158,11,.6);
            box-shadow:0 1px 1px rgba(0,0,0,.03);
          }
          .stButton>button:hover{ filter:saturate(1.05) brightness(1.02); }

          /* tabelas */
          .stDataFrame, .stDataEditor{ background:var(--cdc-card) !important; border-radius:12px; }

          /* avisos */
          .cdc-success{
            background:#ECFDF5; border:1px solid #10B981; color:#065F46;
            padding:10px 12px; border-radius:12px; font-size:14px;
          }
          .cdc-danger{
            background:#FEF2F2; border:1px solid #EF4444; color:#991B1B;
            padding:10px 12px; border-radius:12px; font-size:14px;
          }
        </style>
        """,
        unsafe_allow_html=True
    )

def cdc_header():
    _inject_styles()

    # barra superior com logo + título
    st.markdown('<div class="cdc-topbar">', unsafe_allow_html=True)

    cols = st.columns([1,7])
    with cols[0]:
        logo_path = Path("assets/logo.png")
        if logo_path.exists():
            st.image(str(logo_path), width=140)
        else:
            st.markdown("<div style='font-weight:800;color:#334155;padding:8px 0;'>Casa do Cigano</div>", unsafe_allow_html=True)

    with cols[1]:
        st.markdown(
            """
            <div>
              <div class="cdc-title">Casa do Cigano <span class="cdc-badge">Integrador de Marketplaces</span></div>
              <div class="cdc-sub">Pedidos • Produtos • Estoque • Pagamentos</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

def cdc_card(title: str, value: str, help_text: str = "", fine: str = ""):
    """Card de métrica com tooltip opcional e linha fina."""
    tip = f'<span class="cdc-help" data-tip="{help_text}">?</span>' if help_text else ""
    fine_html = f'<div class="fine">{fine}</div>' if fine else ""
    st.markdown(
        f"""
        <div class="cdc-card">
          <h4>{title} {tip}</h4>
          <div class="v">{value}</div>
          {fine_html}
        </div>
        """,
        unsafe_allow_html=True
    )
