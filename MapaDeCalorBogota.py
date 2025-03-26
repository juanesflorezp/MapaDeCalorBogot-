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
st.title("📍 Mapa de Lugares en Bogotá")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Ubicación por defecto (Bogotá)
UBICACION_BOGOTA = [4.60971, -74.08175]

# Lista mejorada de estaciones de Transmilenio
ESTACIONES_TRANSMILENIO = [
    "Portal 80", "Portal Américas", "Portal Eldorado", "Portal Norte",
    "Portal Suba", "Portal Sur", "Portal Tunal", "Calle 100",
    "Calle 72", "Calle 45", "Calle 26", "Calle 19", "Calle 22",
    "Museo del Oro", "Av. Jiménez", "Universidades", "Santander",
    "Héroes", "Paloquemao", "Restrepo", "Alcalá", "Calle 127",
    "Toberín", "Usaquén", "Cedritos", "Pepe Sierra", "Calle 146"
]

# Interfaz de usuario
with st.sidebar:
    st.header("Configuración")
    radio = st.slider("Radio de búsqueda (metros):", 100, 5000, 1000, 100)
    direccion = st.text_input("Ingresa una dirección en Bogotá:", "")
    usar_mapa = st.checkbox("Seleccionar ubicación en el mapa")

# Mapa interactivo
mapa = folium.Map(location=UBICACION_BOGOTA, zoom_start=13)
mapa_data = st_folium(mapa, width=1200, height=600)

# Manejo de ubicación
ubicacion_usuario = None
if usar_mapa and mapa_data["last_clicked"]:
    ubicacion_usuario = (mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"])
    st.success(f"Ubicación seleccionada: {ubicacion_usuario}")

if direccion:
    try:
        geocode_result = gmaps.geocode(f"{direccion}, Bogotá, Colombia")
        if geocode_result:
            ubicacion_usuario = (
                geocode_result[0]["geometry"]["location"]["lat"],
                geocode_result[0]["geometry"]["location"]["lng"]
            )
            st.success(f"Ubicación encontrada: {ubicacion_usuario}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Funciones de búsqueda optimizadas
def buscar_transmilenio(location, radius):
    resultados = []
    for estacion in ESTACIONES_TRANSMILENIO:
        try:
            res = gmaps.places(query=f"Estación {estacion}", location=location, radius=radius)
            resultados.extend(res.get("results", []))
            time.sleep(0.1)
        except:
            continue
    return list({v['place_id']:v for v in resultados}.values())

def buscar_oficinas(location, radius):
    try:
        resultados = gmaps.places_nearby(location=location, radius=radius, type="office").get("results", [])
        mas_resultados = gmaps.places_nearby(location=location, radius=radius, keyword="oficinas").get("results", [])
        resultados.extend(mas_resultados)
        return list({v['place_id']:v for v in resultados}.values())
    except Exception as e:
        st.warning(f"Error oficinas: {str(e)}")
        return []

# Búsqueda principal
if ubicacion_usuario and st.button("Buscar Lugares"):
    with st.spinner("Buscando lugares..."):
        try:
            # Realizar búsquedas
            restaurantes = gmaps.places_nearby(
                location=ubicacion_usuario,
                radius=radio,
                type="restaurant"
            ).get("results", [])
            
            oficinas = buscar_oficinas(ubicacion_usuario, radio)
            transmilenio = buscar_transmilenio(ubicacion_usuario, radio)

            # Configurar iconos
            iconos = {
                "restaurant": {"icon": "cutlery", "color": "red"},
                "office": {"icon": "briefcase", "color": "blue"},
                "transmilenio": {"icon": "bus", "color": "green"}
            }

            # Crear mapa de resultados
            mapa_resultados = folium.Map(location=ubicacion_usuario, zoom_start=15)
            folium.Marker(ubicacion_usuario, popup="Ubicación seleccionada").add_to(mapa_resultados)

            # Añadir marcadores
            for lugar, tipo in [(r, "restaurant") for r in restaurantes] + \
                             [(o, "office") for o in oficinas] + \
                             [(t, "transmilenio") for t in transmilenio]:
                folium.Marker(
                    [lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
                    popup=f"<b>{lugar['name']}</b><br>{lugar.get('vicinity', '')}",
                    icon=folium.Icon(color=iconos[tipo]["color"], icon=iconos[tipo]["icon"], prefix="fa")
                ).add_to(mapa_resultados)

            # Añadir heatmap
            HeatMap([[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] 
                   for p in restaurantes + oficinas + transmilenio]).add_to(mapa_resultados)

            # Mostrar resultados
            st.subheader("Resultados")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write(f"🍴 Restaurantes: {len(restaurantes)}")
                st.write(f"🏢 Oficinas: {len(oficinas)}")
                st.write(f"🚌 Estaciones TM: {len(transmilenio)}")
            
            with col2:
                folium_static(mapa_resultados)

            # Tabla simplificada sin rating
            datos = []
            for lugar, tipo in [(r, "Restaurante") for r in restaurantes] + \
                            [(o, "Oficina") for o in oficinas] + \
                            [(t, "Transmilenio") for t in transmilenio]:
                datos.append({
                    "Tipo": tipo,
                    "Nombre": lugar["name"],
                    "Dirección": lugar.get("vicinity", "No disponible")
                })
            
            st.dataframe(pd.DataFrame(datos).sort_values(by="Tipo"), height=400)

        except Exception as e:
            st.error(f"Error: {str(e)}")
