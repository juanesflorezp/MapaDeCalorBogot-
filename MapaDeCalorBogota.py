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
st.title("📍 Mapa de Calor Interactivo")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 
if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Selección de ubicación inicial
definir_ubicacion = st.text_input("Ingrese una ubicación inicial:", "Bogotá, Colombia")
try:
    geocode_result = gmaps.geocode(definir_ubicacion)
    if geocode_result:
        UBICACION_INICIAL = [
            geocode_result[0]["geometry"]["location"]["lat"],
            geocode_result[0]["geometry"]["location"]["lng"]
        ]
    else:
        UBICACION_INICIAL = [4.60971, -74.08175]  # Valor por defecto
except Exception as e:
    st.warning(f"Error obteniendo la ubicación: {str(e)}")
    UBICACION_INICIAL = [4.60971, -74.08175]

# Crear mapa base
mapa = folium.Map(location=UBICACION_INICIAL, zoom_start=12, control_scale=True)

# Función para obtener lugares cercanos
def obtener_lugares(location, radius, tipo):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type=tipo).get("results", [])
        return resultados
    except Exception as e:
        st.warning(f"Error obteniendo {tipo}: {str(e)}")
        return []

# Cargar heatmap inicial
st.subheader("Cargando mapa de calor...")
all_places = []
for tipo in ["restaurant", "office", "bus_station"]:
    all_places.extend(obtener_lugares(UBICACION_INICIAL, 5000, tipo))

# Generar heatmap
heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in all_places]
HeatMap(heat_data).add_to(mapa)

# Mostrar mapa inicial
data_mapa = st_folium(mapa, width=1200, height=600)

# Actualización dinámica con zoom
def actualizar_mapa(data_mapa):
    if data_mapa and "zoom" in data_mapa:
        zoom_level = data_mapa["zoom"]
        center = data_mapa["center"]
        
        if zoom_level > 14:
            lugares_cercanos = []
            for tipo in ["restaurant", "office", "bus_station"]:
                lugares_cercanos.extend(obtener_lugares((center["lat"], center["lng"]), 1000, tipo))
            
            mapa = folium.Map(location=[center["lat"], center["lng"]], zoom_start=zoom_level, control_scale=True)
            HeatMap(heat_data).add_to(mapa)
            
            for lugar in lugares_cercanos: 
                folium.Marker(
                    location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
                    popup=lugar["name"],
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(mapa)
            
            st_folium(mapa, width=1200, height=600)

actualizar_mapa(data_mapa)
