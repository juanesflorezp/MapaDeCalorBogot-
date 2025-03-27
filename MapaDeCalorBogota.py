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

# Configuración básica
st.set_page_config(layout="wide")
st.title("📍 Mapa de Calor de Bogotá")

# Cargar API Key
load_dotenv()
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

# Configuración básica
st.set_page_config(layout="wide")
st.title("📍 Mapa de Calor de Bogotá")

# Cargar API Key
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Ubicación por defecto (Bogotá)
UBICACION_BOGOTA = [4.60971, -74.08175]

# Crear un mapa base con zoom dinámico
mapa = folium.Map(location=UBICACION_BOGOTA, zoom_start=12, control_scale=True)
st_folium(mapa, width=1200, height=600)

# Función para obtener lugares cercanos
def obtener_lugares(location, radius, tipo):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type=tipo).get("results", [])
        return resultados
    except Exception as e:
        st.warning(f"Error obteniendo {tipo}: {str(e)}")
        return []

# Obtener datos para el heatmap (inicialmente con toda Bogotá)
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
    if zoom_level > 14:  # Mostrar marcadores cuando el zoom es alto
        lugares_cercanos = []
        for tipo in ["restaurant", "office", "bus_station"]:
            lugares_cercanos.extend(obtener_lugares((center["lat"], center["lng"]), 1000, tipo))
        
        for lugar in lugares_cercanos:
            folium.Marker(
                location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
                popup=lugar["name"],
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(mapa)

    # Actualizar el mapa con los nuevos datos
    st_folium(mapa, width=1200, height=600)


if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Ubicación por defecto (Bogotá)
UBICACION_BOGOTA = [4.60971, -74.08175]

# Crear un mapa base con zoom dinámico
mapa = folium.Map(location=UBICACION_BOGOTA, zoom_start=12, control_scale=True)
st_folium(mapa, width=1200, height=600)

# Función para obtener lugares cercanos
def obtener_lugares(location, radius, tipo):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type=tipo).get("results", [])
        return resultados
    except Exception as e:
        st.warning(f"Error obteniendo {tipo}: {str(e)}")
        return []

# Obtener datos para el heatmap (inicialmente con toda Bogotá)
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
    if zoom_level > 14:  # Mostrar marcadores cuando el zoom es alto
        lugares_cercanos = []
        for tipo in ["restaurant", "office", "bus_station"]:
            lugares_cercanos.extend(obtener_lugares((center["lat"], center["lng"]), 1000, tipo))
        
        for lugar in lugares_cercanos:
            folium.Marker(
                location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
                popup=lugar["name"],
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(mapa)

    # Actualizar el mapa con los nuevos datos
    st_folium(mapa, width=1200, height=600)
