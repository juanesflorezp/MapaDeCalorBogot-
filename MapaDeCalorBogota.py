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

st.title("📍 Mapa de Lugares Específicos en Bogotá")  # Título modificado

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw"  # Asegúrate de tener esto en tu .env

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Configuración fija para Bogotá
ciudad_seleccionada = "Bogotá"
ubicacion_ciudad = [4.60971, -74.08175]  # Coordenadas de Bogotá

# Input para definir el radio de búsqueda
radio = st.slider("Selecciona el radio de búsqueda (metros):", min_value=100, max_value=5000, value=500, step=100)

# Opción para elegir método de búsqueda
opcion_busqueda = st.radio("¿Cómo quieres buscar?", ("Usar dirección escrita", "Usar ubicación del mapa"))

# Input para ingresar dirección (opcional)
direccion = st.text_input("Ingresa una dirección en Bogotá (opcional):", "")

# Inicializar session_state si no existe
if "ubicacion_usuario" not in st.session_state:
    st.session_state["ubicacion_usuario"] = None
if "direccion_obtenida" not in st.session_state:
    st.session_state["direccion_obtenida"] = ""

# Crear mapa base solo una vez
mapa = folium.Map(location=ubicacion_ciudad, zoom_start=14)

# Mostrar mapa interactivo con `st_folium`
mapa_data = st_folium(mapa, width=700, height=500)

# Si el usuario ha hecho clic en una nueva ubicación
if mapa_data["last_clicked"]:
    lat, lon = mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"]
    
    # Solo actualizar session_state si la ubicación cambia
    if st.session_state["ubicacion_usuario"] != (lat, lon):
        st.session_state["ubicacion_usuario"] = (lat, lon)

        # Obtener dirección inversa con Google Maps
        try:
            reverse_geocode_result = gmaps.reverse_geocode((lat, lon))
            if reverse_geocode_result:
                st.session_state["direccion_obtenida"] = reverse_geocode_result[0]["formatted_address"]
                st.success(f"Ubicación seleccionada: {st.session_state['direccion_obtenida']}")
        except Exception as e:
            st.warning(f"Error al obtener dirección: {e}")

# Mostrar la dirección obtenida en el campo de texto
direccion = st.text_input("Dirección seleccionada:", st.session_state["direccion_obtenida"])

# Botón para iniciar la búsqueda
if st.button("Iniciar Búsqueda"):

    # Buscar con dirección escrita
    if opcion_busqueda == "Usar dirección escrita" and direccion:
        try:
            geocode_result = gmaps.geocode(direccion + ", Bogotá, Colombia")  # Forzar búsqueda en Bogotá
            if geocode_result:
                lat = geocode_result[0]["geometry"]["location"]["lat"]
                lon = geocode_result[0]["geometry"]["location"]["lng"]
                st.success(f"Ubicación obtenida de la dirección: {lat}, {lon}")
            else:
                st.error("No se encontraron coordenadas para la dirección.")
                st.stop()
        except Exception as e:
            st.error(f"Error al obtener coordenadas: {e}")
            st.stop()

    # Buscar con ubicación del mapa
    elif opcion_busqueda == "Usar ubicación del mapa" and st.session_state["ubicacion_usuario"]:
        lat, lon = st.session_state["ubicacion_usuario"]
    else:
        st.warning("Debes seleccionar una ubicación en el mapa o ingresar una dirección.")
        st.stop()

    user_location = (lat, lon)

    # Obtener lugares cercanos (solo restaurantes, oficinas y estaciones de Transmilenio)
    try:
        categories = ["restaurant", "office", "bus_station"]  # Categorías modificadas

        @st.cache_data(show_spinner="Buscando lugares cercanos...")
        def get_all_places(place_type, location, radius):
            places = []
            next_page_token = None
            while True:
                try:
                    if next_page_token:
                        time.sleep(2)
                        places_result = gmaps.places_nearby(
                            location=location, radius=radius, type=place_type, page_token=next_page_token
                        )
                    else:
                        places_result = gmaps.places_nearby(
                            location=location, radius=radius, type=place_type
                        )

                    places.extend(places_result.get("results", []))
                    next_page_token = places_result.get("next_page_token")

                    if not next_page_token:
                        break
                except Exception as e:
                    st.warning(f"Error al obtener lugares para {place_type}: {e}")
                    break
            return places

        places_data = []
        with st.status("Obteniendo lugares...", expanded=True) as status:
            for category in categories:
                places = get_all_places(category, user_location, radius=radio)
                # Filtrar solo resultados en Bogotá (aproximadamente)
                places = [p for p in places if 4.4 <= p["geometry"]["location"]["lat"] <= 4.8 and 
                         -74.2 <= p["geometry"]["location"]["lng"] <= -73.9]
                places_data.extend(places)
                
                # Traducción de categorías para mostrar
                category_name = {
                    "restaurant": "Restaurantes",
                    "office": "Oficinas",
                    "bus_station": "Estaciones de Transmilenio"
                }.get(category, category)
                
                st.write(f"{len(places)} lugares encontrados en {category_name}")

            status.update(label="Lugares obtenidos con éxito", state="complete")

        # Diccionario de iconos por categoría
        iconos_categorias = {
            "restaurant": {"icon": "cutlery", "color": "red", "name": "Restaurante"},
            "office": {"icon": "briefcase", "color": "blue", "name": "Oficina"},
            "bus_station": {"icon": "bus", "color": "green", "name": "Transmilenio"},
        }

        # Crear mapa con Folium y agregar los lugares encontrados
        mapa = folium.Map(location=user_location, zoom_start=16)
        folium.Marker(
            location=user_location,
            popup="Ubicación seleccionada",
            icon=folium.Icon(color="red", icon="star", prefix="glyphicon")
        ).add_to(mapa)

        if places_data:
            for place in places_data:
                place_types = place.get("types", [])
                categoria_valida = next((c for c in categories if c in place_types), None)

                if categoria_valida:
                    icono_info = iconos_categorias.get(categoria_valida, {"icon": "info-sign", "color": "gray", "name": "Otro"})

                    folium.Marker(
                        location=[place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]],
                        popup=f"{place['name']} ({icono_info['name']})\nRating: {place.get('rating', 'N/A')}",
                        icon=folium.Icon(color=icono_info["color"], icon=icono_info["icon"], prefix="fa")
                    ).add_to(mapa)

            # Agregar capa de calor
            heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in places_data]
            HeatMap(heat_data).add_to(mapa)

        folium_static(mapa)

        # Mostrar datos en tabla
        if places_data:
            st.subheader("Lista de Lugares Encontrados")
            df_data = []
            for place in places_data:
                types = place.get("types", [])
                categoria = next((iconos_categorias[c]["name"] for c in categories if c in types), "Otro")
                
                df_data.append({
                    "Nombre": place["name"],
                    "Tipo": categoria,
                    "Dirección": place.get("vicinity", "No disponible"),
                    "Rating": place.get("rating", "N/A")
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error: {e}")
