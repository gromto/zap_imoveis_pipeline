import streamlit as st
import pydeck as pdk
import math
import pandas as pd
import json
import base64
from services.queries import load_geojson, load_pois, load_icon


def render():

    # =========================
    # CSS (CRITICAL FIX)
    # =========================
    st.markdown("""
    <style>

    /* MAP RESPECTS SIDEBAR */
    [data-testid="stDeckGlJsonChart"] {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 300px;
        right: 0;
    }

    /* FLOATING CONTROLS */
    div[data-testid="stSlider"],
    div[data-testid="stCheckbox"] {
        position: fixed !important;
        right: 20px;
        z-index: 999;

        background: rgba(20,20,20,0.85);
        backdrop-filter: blur(10px);

        padding: 10px 12px;
        border-radius: 10px;

        width: 230px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }

    div[data-testid="stSlider"] {
        bottom: 80px;
    }

    div[data-testid="stCheckbox"] {
        bottom: 20px;
    }

    label {
        color: white !important;
        font-size: 12px;
    }

    </style>
    """, unsafe_allow_html=True)

    # =========================
    # DATA
    # =========================

    geojson = load_geojson()
    pois = pd.DataFrame(load_pois())
    icon_url = load_icon()

    pois["icon"] = pois.apply(lambda _: {
        "url": icon_url,
        "width": 128,
        "height": 128,
        "anchorY": 128
    }, axis=1)

    # =========================
    # CONTROLS
    # =========================

    cap = st.slider("Max (R$/m²)", 5000, 30000, 15000, key="map_cap")
    show_metro = st.checkbox("🚇 Metro", False, key="map_metro")

    # =========================
    # COLOR LOGIC
    # =========================

    def get_color(v):
        v = max(min(v, cap), 2000)
        norm = (math.log(v + 1) - math.log(2001)) / (math.log(cap + 1) - math.log(2001) + 1e-9)

        if norm < 0.5:
            return [int(255 * norm * 2), int(255 * norm * 2), int(255 * (1 - norm * 2)), 160]
        return [255, int(255 * (1 - (norm - 0.5) * 2)), 0, 160]

    for f in geojson["features"]:
        f["properties"]["color"] = get_color(f["properties"]["value"])

    # =========================
    # TOOLTIPS
    # =========================

    pois["tooltip_html"] = pois["name"].apply(
    lambda name: f"""
    <div style="font-size:14px; font-weight:bold;">
        🚇 {name}
    </div>
    """
    )   

    for f in geojson["features"]:
        p = f["properties"]

        p["tooltip_html"] = f"""
        <div style="line-height:1.6; font-size:13px;">

            <b>{p['n']} anúncios</b><br/>

            <div style="margin-top:6px;">
                📍 {p['top_endereco']}<br/>
                <span style="opacity:0.7;">{p['top_bairro']}</span>
            </div>

            <div style="margin-top:8px;">
                💰 Preço mediano: R$ {p['median_price']}<br/>
                📐 Área mediana: {p['median_area']} m²
            </div>

            <div style="margin-top:8px;">
                <b>Configuração (média)</b><br/>
                🛏️ {p['avg_quartos']}<br/>
                🚽 {p['avg_banheiros']}<br/>
                🚗 {p['avg_garagens']}
            </div>

            <div style="margin-top:8px;">
                💵 Preço/m²: R$ {p['avg_price_m2']}
            </div>

        </div>
        """

    tooltip = {
    "html": "{tooltip_html}",
    "style": {
        "backgroundColor": "#111",
        "color": "white",
        "borderRadius": "8px",
        "padding": "10px",
    },
    }

    # =========================
    # LAYERS
    # =========================

    layer = pdk.Layer(
            "GeoJsonLayer",
            geojson,
            pickable=True,
            filled=True,
            stroked=True,
            get_line_color=[255, 255, 255, 60],
            line_width_min_pixels=1,
            auto_highlight=True,
            highlight_color=[255, 255, 255, 120],
            get_fill_color="properties.color",
            tooltip=tooltip,
        )


    metro_layer = pdk.Layer(
    "IconLayer",
    data=pois,
    get_position='[lon, lat]',
    get_icon="icon",

    get_size=40,          
    size_scale=1,         

    size_min_pixels=25,   
    size_max_pixels=25,  

    pickable=True,
    )

    # =========================
    # MAP
    # =========================

    layers = [layer]

    if show_metro:
        layers.append(metro_layer)


    deck = pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=-22.8983,
            longitude=-43.4619,
            zoom=10.5,
        ),
        tooltip={"html": "{tooltip_html}"},
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    )

    st.pydeck_chart(deck, width="stretch")