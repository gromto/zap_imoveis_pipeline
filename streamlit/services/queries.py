import json
import pandas as pd
import base64
import streamlit as st


@st.cache_data
def load_geojson():
    with open("data/data.geojson", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_data():
    with open("data/data.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_pois():
    with open("data/poi.json", "r", encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))


@st.cache_data
def load_icon():
    with open("data/metro_icon.png", "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")