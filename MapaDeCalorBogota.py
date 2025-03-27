# -*- coding: utf-8 -*-

import streamlit as st
import googlemaps
import pandas as pd
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import os

# Configuración básica
st.set_page_config(layout="wide")
st.title("📍 Mapa de Calor - Zona Centro y Norte de Bogotá")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 
if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Ubicación inicial en la zona centro-norte de Bogotá
UBICACION_INICIAL = [4.657, -74.093]

# Crear mapa base
mapa = folium.Map(location=UBICACION_INICIAL, zoom_start=13, control_scale=True)

# Función para obtener lugares cercanos
def obtener_lugares(location, radius, tipo):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type=tipo).get("results", [])
        return resultados
    except Exception as e:
        st.warning(f"Error obteniendo {tipo}: {str(e)}")
        return []

# Obtener datos para el heatmap y marcadores
st.subheader("Cargando mapa de calor y ubicaciones...")
all_places = []
marcadores = []
for tipo in ["restaurant", "office", "bus_station"]:
    lugares = obtener_lugares(UBICACION_INICIAL, 5000, tipo)
    all_places.extend(lugares)
    marcadores.extend(lugares)

# Generar heatmap
heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in all_places]
HeatMap(heat_data).add_to(mapa)

# Agregar marcadores
for lugar in marcadores:
    folium.Marker(
        location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
        popup=lugar["name"],
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(mapa)

# Mostrar mapa en la aplicación
st_folium(mapa, width=1200, height=600)
