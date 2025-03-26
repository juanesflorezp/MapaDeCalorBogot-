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

# Configuración de la página
st.set_page_config(layout="wide")
st.title("📍 Mapa de Lugares Específicos en Bogotá")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("API Key no encontrada. Por favor define GOOGLE_MAPS_API_KEY en tu archivo .env")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# Configuración fija para Bogotá
UBICACION_BOGOTA = [4.60971, -74.08175]
RADIO_DEFAULT = 1000  # Radio por defecto aumentado para mejor cobertura

# Lista de estaciones de Transmilenio (puedes agregar más)
ESTACIONES_TRANSMILENIO = [
    "Portal 80", "Portal Américas", "Portal Eldorado", "Portal Norte",
    "Portal Suba", "Portal Sur", "Portal Tunal", "Calle 100",
    "Calle 72", "Calle 45", "Calle 26", "Calle 19", "Calle 22",
    "Museo del Oro", "Av. Jiménez", "Universidades", "Santander",
    "Héroes", "Paloquemao", "Restrepo", "Alcalá", "Calle 127",
    "Toberín", "Usaquén", "Cedritos", "Pepe Sierra", "Calle 146"
]

# Configuración de la UI
with st.sidebar:
    st.header("Configuración de Búsqueda")
    radio = st.slider("Radio de búsqueda (metros):", 100, 5000, RADIO_DEFAULT, 100)
    opcion_busqueda = st.radio("Método de búsqueda:", ["Usar dirección escrita", "Usar ubicación del mapa"])
    direccion = st.text_input("Ingresa una dirección en Bogotá:", "")

# Función para buscar estaciones de Transmilenio
def buscar_transmilenio(location, radius):
    try:
        resultados = []
        # Búsqueda por nombres conocidos
        for estacion in ESTACIONES_TRANSMILENIO:
            time.sleep(0.1)  # Pequeña pausa para evitar límites de la API
            try:
                places_result = gmaps.places(
                    query=f"Estación {estacion} Transmilenio",
                    location=location,
                    radius=radius
                )
                resultados.extend(places_result.get("results", []))
            except:
                continue
        
        # Búsqueda genérica
        try:
            places_result = gmaps.places_nearby(
                location=location,
                radius=radius,
                type="transit_station",
                keyword="Transmilenio"
            )
            resultados.extend(places_result.get("results", []))
        except:
            pass
        
        # Eliminar duplicados
        seen = set()
        return [x for x in resultados if x['place_id'] not in seen and not seen.add(x['place_id'])]
    except Exception as e:
        st.warning(f"Error al buscar Transmilenio: {str(e)}")
        return []

# Función para buscar oficinas (mejorada)
def buscar_oficinas(location, radius):
    try:
        # Búsqueda por tipo 'office'
        results = gmaps.places_nearby(
            location=location,
            radius=radius,
            type="office"
        ).get("results", [])
        
        # Búsqueda adicional por palabras clave comunes
        keywords = ["edificio oficinas", "torre empresarial", "centro de negocios"]
        for keyword in keywords:
            time.sleep(0.1)
            try:
                more_results = gmaps.places_nearby(
                    location=location,
                    radius=radius,
                    keyword=keyword
                ).get("results", [])
                results.extend(more_results)
            except:
                continue
        
        # Filtrar solo resultados que parezcan oficinas
        filtered = []
        for place in results:
            types = place.get("types", [])
            if 'office' in types or any(word in place['name'].lower() for word in ['oficina', 'edificio', 'torre', 'empresarial']):
                filtered.append(place)
        
        # Eliminar duplicados
        seen = set()
        return [x for x in filtered if x['place_id'] not in seen and not seen.add(x['place_id'])]
    except Exception as e:
        st.warning(f"Error al buscar oficinas: {str(e)}")
        return []

# Mapa interactivo
mapa = folium.Map(location=UBICACION_BOGOTA, zoom_start=13)
mapa_data = st_folium(mapa, width=1200, height=600)

# Manejo de ubicación
ubicacion_usuario = None
if mapa_data["last_clicked"]:
    ubicacion_usuario = (mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"])
    st.success(f"Ubicación seleccionada: {ubicacion_usuario}")

if opcion_busqueda == "Usar dirección escrita" and direccion:
    try:
        geocode_result = gmaps.geocode(f"{direccion}, Bogotá, Colombia")
        if geocode_result:
            ubicacion_usuario = (
                geocode_result[0]["geometry"]["location"]["lat"],
                geocode_result[0]["geometry"]["location"]["lng"]
            )
            st.success(f"Ubicación encontrada: {ubicacion_usuario}")
    except Exception as e:
        st.error(f"Error al geocodificar: {str(e)}")

# Botón de búsqueda
if st.button("Buscar Lugares") and ubicacion_usuario:
    with st.spinner("Realizando búsqueda..."):
        try:
            # Realizar todas las búsquedas
            restaurantes = gmaps.places_nearby(
                location=ubicacion_usuario,
                radius=radio,
                type="restaurant"
            ).get("results", [])
            
            oficinas = buscar_oficinas(ubicacion_usuario, radio)
            transmilenio = buscar_transmilenio(ubicacion_usuario, radio)

            # Configuración de iconos
            iconos = {
                "restaurant": {"icon": "cutlery", "color": "red", "name": "Restaurante"},
                "office": {"icon": "briefcase", "color": "blue", "name": "Oficina"},
                "transmilenio": {"icon": "bus", "color": "green", "name": "Transmilenio"}
            }

            # Crear mapa
            mapa_resultados = folium.Map(location=ubicacion_usuario, zoom_start=15)
            
            # Añadir marcador de ubicación seleccionada
            folium.Marker(
                location=ubicacion_usuario,
                popup="Tu ubicación",
                icon=folium.Icon(color="black", icon="star")
            ).add_to(mapa_resultados)

            # Añadir resultados al mapa
            for lugar, tipo in [(r, "restaurant") for r in restaurantes] + \
                             [(o, "office") for o in oficinas] + \
                             [(t, "transmilenio") for t in transmilenio]:
                folium.Marker(
                    location=[lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]],
                    popup=f"<b>{lugar['name']}</b><br>{iconos[tipo]['name']}",
                    icon=folium.Icon(color=iconos[tipo]["color"], icon=iconos[tipo]["icon"], prefix="fa")
                ).add_to(mapa_resultados)

            # Añadir heatmap
            heat_data = [
                [lugar["geometry"]["location"]["lat"], lugar["geometry"]["location"]["lng"]]
                for lugar in restaurantes + oficinas + transmilenio
            ]
            HeatMap(heat_data).add_to(mapa_resultados)

            # Mostrar resultados
            st.subheader("Resultados encontrados")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Restaurantes:** {len(restaurantes)}")
                st.markdown(f"**Oficinas:** {len(oficinas)}")
                st.markdown(f"**Estaciones de Transmilenio:** {len(transmilenio)}")
            
            with col2:
                folium_static(mapa_resultados)

            # Mostrar tabla de resultados
            st.subheader("Detalle de Lugares")
            datos = []
            for lugar, tipo in [(r, "Restaurante") for r in restaurantes] + \
                            [(o, "Oficina") for o in oficinas] + \
                            [(t, "Transmilenio") for t in transmilenio]:
                datos.append({
                    "Nombre": lugar["name"],
                    "Tipo": tipo,
                    "Dirección": lugar.get("vicinity", "No disponible"),
                    "Rating": lugar.get("rating", "N/A"),
                    "Abreviatura": ", ".join([x for x in lugar.get("types", []) if not x.startswith("point_of_interest")][:3])
                })
            
            df = pd.DataFrame(datos)
            st.dataframe(df.sort_values(by="Tipo"), height=400)

        except Exception as e:
            st.error(f"Error en la búsqueda: {str(e)}")
