import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster
import plotly.express as px

# --- CONFIG ---
st.set_page_config(page_title="Mapa y Análisis de Precios", layout="wide")
st.title("🏘️ Dashboard de Inmuebles en Alquiler")

# --- CARGA DE DATA ---
@st.cache_data
def load_data():
    df = pd.read_excel("data.csv")
    df = df.dropna(subset=['lat', 'lon'])
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df['Precio_Soles'] = pd.to_numeric(df['Precio_Soles'], errors='coerce')
    return df.dropna(subset=['Precio_Soles'])

df = load_data()

# --- ASIGNACIÓN DE DISTRITO USANDO GEOPY ---
@st.cache_data
def asignar_distrito(df):
    geolocator = Nominatim(user_agent="geoapiExercises")
    distritos = []

    for lat, lon in zip(df['lat'], df['lon']):
        try:
            location = geolocator.reverse((lat, lon), language='es')
            distrito = location.raw['address'].get('suburb') or location.raw['address'].get('city_district') or location.raw['address'].get('town') or 'Desconocido'
        except:
            distrito = 'Desconocido'
        distritos.append(distrito)

    df['Distrito'] = distritos
    return df

with st.spinner("🧭 Asignando distritos..."):
    df = asignar_distrito(df)

# --- MAPA CON FOLIUM ---
st.subheader("📍 Ubicación de Inmuebles en Mapa")
m = folium.Map(location=[-12.1, -77.03], zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"{row['Precio']} - {row['Ubicación']}",
        tooltip=row['Precio']
    ).add_to(marker_cluster)

st_data = st_folium(m, width=1200)

# --- ANÁLISIS DE PRECIOS POR DISTRITO ---
st.subheader("📊 Análisis Comparativo de Precios por Distrito")

df_filtrado = df[df['Distrito'] != 'Desconocido']

col1, col2 = st.columns(2)
with col1:
    fig_box = px.box(df_filtrado, x="Distrito", y="Precio_Soles", points="all",
                     title="Distribución de Precios por Distrito (Boxplot)")
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    precios_mean = df_filtrado.groupby("Distrito")['Precio_Soles'].mean().reset_index()
    fig_bar = px.bar(precios_mean, x="Distrito", y="Precio_Soles", title="Precio Promedio por Distrito")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- ALEJAMIENTO DE LA MEDIA SEGÚN HABITACIONES Y BAÑOS ---
st.subheader("📈 Desviación de Precios por Habitaciones y Servicios")

# Convertimos "3 dorm." a número
df_filtrado['Habitaciones_Num'] = df_filtrado['Habitaciones'].str.extract('(\d+)').astype(float)
df_filtrado['Baños'] = pd.to_numeric(df_filtrado['Baños'], errors='coerce')

grupo = df_filtrado.groupby(['Habitaciones_Num', 'Baños']).agg(
    promedio=('Precio_Soles', 'mean'),
    std=('Precio_Soles', 'std'),
    conteo=('Precio_Soles', 'count')
).reset_index()

fig_heatmap = px.density_heatmap(grupo, x="Habitaciones_Num", y="Baños",
                                 z="promedio", histfunc="avg",
                                 color_continuous_scale="Viridis",
                                 title="Mapa de calor del precio promedio por cantidad de Habitaciones y Baños")
st.plotly_chart(fig_heatmap, use_container_width=True)