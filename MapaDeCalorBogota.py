import streamlit as st
import googlemaps
import pandas as pd
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import HeatMap
import os

st.title("📍 Mapa de Oficinas, Coworking, Restaurantes y TransMilenio en Bogotá")

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Ubicación fija para Bogotá
ubicacion_ciudad = [4.60971, -74.08175]

# Input para definir el radio de búsqueda
radio = st.slider("Selecciona el radio de búsqueda (metros):", min_value=100, max_value=5000, value=500, step=100)

# Permitir selección de ubicación en el mapa
st.write("Haz clic en el mapa para seleccionar una ubicación personalizada")
mapa_seleccion = folium.Map(location=ubicacion_ciudad, zoom_start=14)
mapa_data = st_folium(mapa_seleccion, width=700, height=500)

if mapa_data["last_clicked"]:
    user_location = [mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"]]
else:
    user_location = ubicacion_ciudad

# Botón para iniciar la búsqueda
if st.button("Iniciar Búsqueda"):
    try:
        categories = {
            "restaurant": {"icon": "cutlery", "color": "red"},
            "coworking_space": {"icon": "briefcase", "color": "blue"},
            "real_estate_agency": {"icon": "building", "color": "green"},
            "transit_station": {"icon": "subway", "color": "purple"},
        }

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
        for category in categories.keys():
            places = get_all_places(category, user_location, radius=radio)
            places_data.extend([(place, category) for place in places])
        
        # Crear mapa con resultados
        mapa = folium.Map(location=user_location, zoom_start=14)
        
        # Agregar marcador de ubicación seleccionada
        folium.Marker(
            location=user_location,
            popup="Ubicación seleccionada",
            icon=folium.Icon(color="darkblue", icon="star", prefix="fa")
        ).add_to(mapa)
        
        if places_data:
            for place, category in places_data:
                folium.Marker(
                    location=[place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]],
                    popup=place["name"],
                    icon=folium.Icon(color=categories[category]["color"], icon=categories[category]["icon"], prefix="fa")
                ).add_to(mapa)
            
            heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p, _ in places_data]
            HeatMap(heat_data).add_to(mapa)
        
        folium_static(mapa)
    except Exception as e:
        st.error(f"Error: {e}")
