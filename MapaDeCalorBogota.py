# -*- coding: utf-8 -*-

import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap, MousePosition
import os

st.title("📍 Mapa de Oficinas, Restaurantes y TransMilenio en Bogotá")

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw"

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Selección de ubicación inicial en el mapa
st.write("Haz clic en el mapa para seleccionar la ubicación de búsqueda")

# Mapa inicial centrado en Bogotá
if "ubicacion_seleccionada" not in st.session_state:
    st.session_state["ubicacion_seleccionada"] = [4.72, -74.05]

# Crear mapa
mapa_base = folium.Map(location=st.session_state["ubicacion_seleccionada"], zoom_start=12)
mouse_position = MousePosition(position='topright', separator=' | ', empty_string='No data', num_digits=5, prefix='Lat: ')
mapa_base.add_child(mouse_position)

# Mostrar mapa interactivo
map_data = st_folium(mapa_base, height=500, width=700)

# Actualizar ubicación si el usuario hace clic en el mapa
if map_data and map_data.get("last_clicked"):
    st.session_state["ubicacion_seleccionada"] = [
        map_data["last_clicked"].get("lat", st.session_state["ubicacion_seleccionada"][0]),
        map_data["last_clicked"].get("lng", st.session_state["ubicacion_seleccionada"][1])
    ]

st.write("Ubicación seleccionada: ", st.session_state["ubicacion_seleccionada"])

# Radio de búsqueda
radio = 2000  # Reducido a 2km

# Categorías disponibles
categorias_disponibles = {
    "restaurant": {"nombre": "🍽️ Restaurantes", "color": "red", "icono": "cutlery"},
    "real_estate_agency": {"nombre": "🏢 Oficinas", "color": "blue", "icono": "building"},
    "office": {"nombre": "🏢 Oficinas en general", "color": "darkblue", "icono": "briefcase"},
    "coworking_space": {"nombre": "💼 Espacios de Coworking", "color": "purple", "icono": "users"},
    "transit_station": {"nombre": "🚉 Estaciones de TransMilenio", "color": "green", "icono": "train"},
}

categorias_seleccionadas = st.multiselect(
    "Selecciona las categorías a mostrar:",
    list(categorias_disponibles.keys()),
    default=list(categorias_disponibles.keys())
)

# Botón para iniciar la búsqueda
if st.button("Iniciar Búsqueda"):
    @st.cache_data(show_spinner="Buscando lugares cercanos...")
    def get_all_places(place_type, location, radius):
        places = []
        next_page_token = None
        while True:
            try:
                params = {"location": location, "radius": radius, "type": place_type}
                if next_page_token:
                    params["page_token"] = next_page_token
                    time.sleep(2)
                places_result = gmaps.places_nearby(**params)
                
                for place in places_result.get("results", []):
                    lat = place["geometry"]["location"]["lat"]
                    lon = place["geometry"]["location"]["lng"]
                    if 4.50 <= lat <= 4.85 and -74.20 <= lon <= -73.98:
                        places.append(place)
                
                next_page_token = places_result.get("next_page_token")
                if not next_page_token:
                    break
            except Exception as e:
                st.warning(f"Error al obtener lugares para {place_type}: {e}")
                break
        return places

    places_data = []
    for category in categorias_seleccionadas:
        places = get_all_places(category, st.session_state["ubicacion_seleccionada"], radio)
        places_data.extend(places)

    mapa = folium.Map(location=st.session_state["ubicacion_seleccionada"], zoom_start=12)
    
    if places_data:
        heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in places_data]
        HeatMap(heat_data).add_to(mapa)
        for place in places_data:
            lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
            categoria_valida = next((c for c in categorias_seleccionadas if c in place.get("types", [])), None)
            if categoria_valida:
                info_categoria = categorias_disponibles[categoria_valida]
                folium.Marker(
                    location=[lat, lon],
                    popup=f"{place['name']} ({info_categoria['nombre']})\nRating: {place.get('rating', 'N/A')}",
                    icon=folium.Icon(color=info_categoria["color"], icon=info_categoria["icono"], prefix="fa")
                ).add_to(mapa)
    
    st_folium(mapa, height=500, width=700)
