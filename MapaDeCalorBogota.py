# -*- coding: utf-8 -*-

import streamlit as st
import googlemaps
import pandas as pd
import time
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import os

# Configuración básica - Debe ser la primera llamada de Streamlit
st.set_page_config(layout="wide")
st.title("📍 Mapa de Calor de Bogotá")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Selección del lugar de inicio
definir_ubicacion = st.text_input("Ingrese una ubicación inicial (ej. Bogotá, Colombia):", "Bogotá, Colombia")

try:
    geocode_result = gmaps.geocode(definir_ubicacion)
    if geocode_result:
        UBICACION_BOGOTA = [
            geocode_result[0]["geometry"]["location"]["lat"],
            geocode_result[0]["geometry"]["location"]["lng"]
        ]
    else:
        UBICACION_BOGOTA = [4.60971, -74.08175]  # Valor por defecto
except Exception as e:
    st.warning(f"No se pudo obtener la ubicación, usando el valor por defecto. Error: {str(e)}")
    UBICACION_BOGOTA = [4.60971, -74.08175]

# Crear un mapa base con zoom dinámico
mapa = folium.Map(location=UBICACION_BOGOTA, zoom_start=12, control_scale=True)

# Función para obtener lugares cercanos
def obtener_lugares(location, radius, tipo):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type=tipo).get("results", [])
        return resultados
    except Exception as e:
        st.warning(f"Error obteniendo {tipo}: {str(e)}")
        return []

# Obtener datos para el heatmap
st.subheader("Cargando mapa de calor...")
all_places = []
for tipo in ["restaurant", "office", "bus_station"]:
    all_places.extend(obtener_lugares(UBICACION_BOGOTA, 5000, tipo))

# Generar heatmap con los puntos obtenidos
heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in all_places]
HeatMap(heat_data).add_to(mapa)

# Mostrar el mapa en la aplicación
map_data = st_folium(mapa, width=1200, height=600)

# Verificar zoom y actualizar marcadores dinámicamente
if map_data and "zoom" in map_data:
    zoom_level = map_data["zoom"]
    center = map_data["center"]
    
    # Si el zoom es alto, agregar marcadores dinámicamente
    if zoom_level > 14:
        lugares_cercanos = []
        for tipo in ["restaurant", "office", "bus_station"]:
            lugares_cercanos.extend(obtener_lugares((center["lat"], center["lng"]), 1000, tipo))
        
        # Crear un nuevo mapa con los marcadores actualizados
        mapa = folium.Map(location=[center["lat"], center["lng"]], zoom_start=zoom_level, control_scale=True)
        HeatMap(heat_data).add_to(mapa)
        
        for lugar in lugares_cercanos:
            folium.Marker(
                location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
                popup=lugar["name"],
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(mapa)
        
    # Actualizar el mapa con los nuevos datos
    map_data = st_folium(mapa, width=1200, height=600)
