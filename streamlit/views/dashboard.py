import streamlit as st
import pandas as pd
import plotly.express as px
from services.queries import load_data


def render():

    # =========================
    # PAGE CONFIG
    # =========================
    st.set_page_config(layout="wide")

    # =========================
    # CSS
    # =========================

    st.markdown("""
    <style>

    [data-testid="stMetricLabel"] {
        display: block !important;
        color: #b6becf !important; 
        font-size: 0.9rem !important;
        opacity: 1 !important;
    }

    [data-testid="stMetricValue"] {
        color: #4c5e85 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # =========================
    # DATA
    # =========================
    @st.cache_data
    def get_df():
        return pd.DataFrame(load_data())

    df = get_df()

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.header("Filtros")

    zonas = sorted(df["zona_corrigida"].dropna().unique())

    selected_zonas = st.sidebar.multiselect(
        "Zona",
        zonas,
        default=zonas
    )

    bairros = sorted(
        df[df["zona_corrigida"].isin(selected_zonas)]["bairro"]
        .dropna()
        .unique()
    )

    selected_bairros = st.sidebar.multiselect(
        "Bairro",
        bairros,
        default=bairros
    )

    # =========================
    # FILTER
    # =========================
    df = df[
        (df["zona_corrigida"].isin(selected_zonas)) &
        (df["bairro"].isin(selected_bairros))
    ]

    if df.empty:
        st.warning("No data")
        return

    # =========================
    # KPIs
    # =========================

    c1, c2, c3 = st.columns(3)

    c1.metric("Preço médio m²", f"R$ {int(df['avg_preco_m2'].mean()):,}")
    c2.metric("Preço mediano", f"R$ {int(df['median_preco'].median()):,}")
    c3.metric("Anúncios", f"{int(df['total_anuncios'].sum()):,}")

    # =========================
    # DISTRIBUTION
    # =========================
    fig = px.histogram(
        df,
        x="avg_preco_m2",
        labels={
            "avg_preco_m2": "Preço médio por m²",
            "count": "Número de ruas"
        },
        nbins=50
    )

    fig.update_layout(
        yaxis_title="Número de ruas",
        margin=dict(l=10, r=10, t=20, b=10),
        height=280
    )

    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # FORMATTERS
    # =========================    

    def format_br_int(x):
        if pd.isna(x):
            return ""
        return f"{int(x):,}".replace(",", ".")

    def format_br_float(x):
        if pd.isna(x):
            return ""
        return f"{x:.2f}".replace(".", ",")

    def format_currency(x):
        if pd.isna(x):
            return ""
        return f"R$ {int(x):,}".replace(",", ".")

    # =========================
    # TABLE
    # =========================
    styled_df = df.style.format({
        "avg_preco_m2": "R$ {:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "median_preco": "R$ {:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "median_area": "{:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "avg_quartos": "{:.2f}".replace(".", ","),
        "avg_banheiros": "{:.2f}".replace(".", ","),
        "avg_garagens": "{:.2f}".replace(".", ","),
        "total_anuncios": "{:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
    })

    df = df.rename(columns={
    "endereco": "Rua",
    "bairro": "Bairro",
    "zona_corrigida": "Zona",
    "total_anuncios": "Anúncios",
    "avg_preco_m2": "Preço médio m²",
    "median_preco": "Preço mediano",
    "median_area": "Área mediana (m²)",
    "avg_quartos": "Quartos",
    "avg_banheiros": "Banheiros",
    "avg_garagens": "Garagens",
    })

    styled_df = df.style.format({
    "Preço médio m² (R$)": format_currency,
    "Preço mediano (R$)": format_currency,
    "Área mediana (m²)": format_br_int,
    "Quartos": format_br_float,
    "Banheiros": format_br_float,
    "Garagens": format_br_float,
    "Anúncios": format_br_int,
    })

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=260
    )