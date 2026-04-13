import streamlit as st

st.set_page_config(layout="wide")

# =========================
# SIDEBAR NAV
# =========================

st.sidebar.markdown("""
<div style="
    padding: 16px 14px;
    border-radius: 14px;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
    margin-bottom: 12px;
">
    <div style="font-size: 1rem; font-weight: 600; line-height: 1.3;">
        🏠 Mapa de calor imobiliário<br>
    <div style="font-size: 0.85rem; opacity: 0.7;">
        Rio de Janeiro - Abr/2026
    </div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    ["🗺️ Map", "📊 Dashboard"],
    key="main_nav"
)

# =========================
# ROUTING (SAFE IMPORTS)
# =========================

if page == "🗺️ Map":
    from views import map as map_page
    map_page.render()

elif page == "📊 Dashboard":
    from views import dashboard as dashboard_page
    dashboard_page.render()