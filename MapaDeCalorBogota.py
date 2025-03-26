# -*- coding: utf-8 -*-

import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap, MousePosition
import os

st.title("\ud83d\udccd Mapa de Oficinas, Restaurantes y TransMilenio en Bogot\u00e1")

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw"

if not API_KEY:
    st.error("API Key no encontrada. Aseg\u00farate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Selecci\u00f3n de ubicaci\u00f3n inicial en el mapa
st.write("Haz clic en el mapa para seleccionar la ubicaci\u00f3n de b\u00fasqueda")

# Mapa inicial centrado en Bogot\u00e1
if "ubicacion_seleccionada" not in st.session_state:
    st.session_state["ubicacion_seleccionada"] = [4.72, -74.05]

# Crear mapa
mapa_base = folium.Map(location=st.session_state["ubicacion_seleccionada"], zoom_start=12)
mouse_position = MousePosition(position='topright', separator=' | ', empty_string='No data', num_digits=5, prefix='Lat: ')
mapa_base.add_child(mouse_position)

# Mostrar mapa interactivo
map_data = st_folium(mapa_base, height=500, width=700)

# Actualizar ubicaci\u00f3n si el usuario hace clic en el mapa
if map_data and "last_clicked" in map_data:
    st.session_state["ubicacion_seleccionada"] = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]

st.write("Ubicaci\u00f3n seleccionada: ", st.session_state["ubicacion_seleccionada"])

# Radio de b\u00fasqueda
tadio = 2000  # Reducido a 2km

# Categor\u00edas disponibles
categorias_disponibles = {
    "restaurant": {"nombre": "\ud83c\udf7d\ufe0f Restaurantes", "color": "red", "icono": "cutlery"},
    "real_estate_agency": {"nombre": "\ud83c\udfe2 Oficinas", "color": "blue", "icono": "building"},
    "office": {"nombre": "\ud83c\udfe2 Oficinas en general", "color": "darkblue", "icono": "briefcase"},
    "coworking_space": {"nombre": "\ud83d\udcbc Espacios de Coworking", "color": "purple", "icono": "users"},
    "transit_station": {"nombre": "\ud83d\ude87 Estaciones de TransMilenio", "color": "green", "icono": "train"},
}

categorias_seleccionadas = st.multiselect(
    "Selecciona las categor\u00edas a mostrar:",
    list(categorias_disponibles.keys()),
    default=list(categorias_disponibles.keys())
)

# Bot\u00f3n para iniciar la b\u00fasqueda
if st.button("Iniciar B\u00fasqueda"):
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
