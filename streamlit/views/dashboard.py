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
    st.sidebar.header("Filters")

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

    c1.metric("Avg Price/m²", f"R$ {int(df['avg_preco_m2'].mean()):,}")
    c2.metric("Median Price", f"R$ {int(df['median_preco'].median()):,}")
    c3.metric("Listings", f"{int(df['total_anuncios'].sum()):,}")

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
    # TABLE
    # =========================
    st.dataframe(
        df,
        use_container_width=True,
        height=260 
    )