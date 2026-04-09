import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine, text
import math
import pandas as pd
import json
import base64

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(layout="wide")

# =========================
# CSS (FULLSCREEN + FLOATING SLIDERS)
# =========================

st.markdown("""
<style>

/* FULLSCREEN MAP */
[data-testid="stDeckGlJsonChart"] {
    position: fixed;
    inset: 0;
}

/* WRAPPER DE TODOS OS CONTROLES */
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

/* POSIÇÕES FIXAS (ESTÁVEIS) */
div[data-testid="stSlider"]:has(label:contains("Min")) {
    bottom: 110px;
}

div[data-testid="stSlider"]:has(label:contains("Max")) {
    bottom: 60px;
}

div[data-testid="stCheckbox"] {
    bottom: 20px;
}

/* TEXTO */
label {
    color: white !important;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# DB
# =========================

@st.cache_data
def load_geojson():
    with open("data.geojson", "r", encoding="utf-8") as f:
        return json.load(f)

geojson = load_geojson()

def load_pois():
    with open("poi.json", "r", encoding="utf-8") as f:
        return json.load(f)


pois = pd.DataFrame(load_pois())

def load_icon(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    

icon_url = load_icon("metro_icon.png")

pois["icon"] = pois.apply(lambda _: {
    "url": icon_url,
    "width": 128,
    "height": 128,
    "anchorY": 128
}, axis=1)

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

        <b>{p['n']} imóveis</b><br/>

        <div style="margin-top:6px;">
            📍 {p['top_endereco']}<br/>
            <span style="opacity:0.7;">{p['top_bairro']}</span>
        </div>

        <div style="margin-top:8px;">
            💰 Preço mediano: {p['median_price']}<br/>
            📐 Área mediana: {p['median_area']}
        </div>

        <div style="margin-top:8px;">
            <b>Configuração (média)</b><br/>
            🛏️ {p['avg_quartos']}<br/>
            🚽 {p['avg_banheiros']}<br/>
            🚗 {p['avg_garagens']}
        </div>

        <div style="margin-top:8px;">
            💵 Preço/m²: {p['avg_price_m2']}
        </div>

    </div>
    """

# =========================
# SLIDERS (NORMAL)
# =========================

cap = st.slider("Max (R$/m²)", 5000, 30000, 15000)
show_metro = st.checkbox("🚇 Metro", value=True)

# =========================
# COLOR FUNCTION (ORIGINAL)
# =========================

floor = 2000

def get_color(v):

    v = max(v, floor)
    v = min(v, cap)

    v_log = math.log(v + 1)
    min_v = math.log(floor + 1)
    max_v = math.log(cap + 1)

    norm = (v_log - min_v) / (max_v - min_v + 1e-9)

    if norm < 0.5:
        r = int(255 * (norm * 2))
        g = int(255 * (norm * 2))
        b = int(255 * (1 - norm * 2))
    else:
        r = 255
        g = int(255 * (1 - (norm - 0.5) * 2))
        b = 0

    return [r, g, b, 160]

# =========================
# APPLY COLORS
# =========================

for f in geojson["features"]:
    props = f["properties"]

    props["color"] = get_color(props["value"])

# =========================
# MAP LAYER
# =========================

layer = pdk.Layer(
    "GeoJsonLayer",
    geojson,
    pickable=True,
    filled=True,
    stroked=True,
    get_fill_color="properties.color",
    get_line_color=[255, 255, 255, 60],
    line_width_min_pixels=1,
    auto_highlight=True,
    transitions=None,
    highlight_color=[255, 255, 255, 120],
)

# =========================
# POI LAYER
# =========================

metro_layer = pdk.Layer(
    "IconLayer",
    data=pois,
    get_position='[lon, lat]',
    get_icon="icon",

    get_size=40,          # 👈 AUMENTA ISSO
    size_scale=1,         # 👈 DIMINUI ISSO

    size_min_pixels=25,   # 👈 aumenta mínimo
    size_max_pixels=25,   # 👈 aumenta máximo

    pickable=True,
)


# =========================
# TOOLTIP
# =========================

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
    tooltip=tooltip,
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
)

st.pydeck_chart(deck, width="stretch")