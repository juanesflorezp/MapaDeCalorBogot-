# -*- coding: utf-8 -*-

import streamlit as st
import googlemaps
import pandas as pd
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import HeatMap
import os

# Configuración básica
st.set_page_config(layout="wide")
st.title("📍 Mapa de Calor de la Zona Norte de Bogotá")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Ubicación por defecto (Zona Norte de Bogotá)
UBICACION_NORTE_BOGOTA = [4.71099, -74.07209]

# Crear un mapa base con zoom dinámico
mapa = folium.Map(location=UBICACION_NORTE_BOGOTA, zoom_start=13, control_scale=True)

# Función para obtener lugares cercanos
def obtener_lugares(location, radius, tipo):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type=tipo).get("results", [])
        return resultados
    except Exception as e:
        st.warning(f"Error obteniendo {tipo}: {str(e)}")
        return []

# Obtener datos para el heatmap (zona norte de Bogotá)
st.subheader("Cargando mapa de calor...")
all_places = []
for tipo in ["restaurant", "office"]:
    all_places.extend(obtener_lugares(UBICACION_NORTE_BOGOTA, 7000, tipo))

# Añadir estaciones de Transmilenio (biarticulados)
ESTACIONES_TRANSMILENIO_BIARTICULADOS = [
    "Portal Norte", "Calle 187", "Toberín", "Calle 161", "Calle 146", "Calle 142", "Alcalá", "Calle 100","Virrey"
]

def obtener_estaciones_transmilenio():
    estaciones = []
    for estacion in ESTACIONES_TRANSMILENIO_BIARTICULADOS:
        try:
            resultado = gmaps.geocode(f"Estación {estacion}, Bogotá, Colombia")
            if resultado:
                loc = resultado[0]["geometry"]["location"]
                estaciones.append({"name": estacion, "location": [loc["lat"], loc["lng"]]})
                time.sleep(0.1)
        except:
            continue
    return estaciones

estaciones_tm = obtener_estaciones_transmilenio()
for est in estaciones_tm:
    all_places.append({"geometry": {"location": {"lat": est["location"][0], "lng": est["location"][1]}}})

# Generar heatmap con los puntos obtenidos
heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in all_places]
HeatMap(heat_data).add_to(mapa)

# Añadir marcadores de lugares
for lugar in all_places:
    folium.Marker(
        location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
        popup=lugar.get("name", "Lugar encontrado"),
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(mapa)

# Mostrar el mapa en la aplicación
folium_static(mapa, width=1200, height=600)
