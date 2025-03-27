import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import MarkerCluster
import os

st.title("📍 Mapa de Bogotá: Restaurantes, Oficinas y TransMilenio")

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

mapa = folium.Map(location=[4.60971, -74.08175], zoom_start=12)
mapa_data = st_folium(mapa, width=700, height=500)

def get_all_places(place_type, location):
    places = {}
    next_page_token = None
    attempts = 0
    while True:
        try:
            if next_page_token:
                time.sleep(2)
                results = gmaps.places_nearby(
                    location=location,
                    radius=20000,
                    type=place_type,
                    page_token=next_page_token
                )
            else:
                results = gmaps.places_nearby(
                    location=location,
                    radius=20000,
                    type=place_type
                )
            
            for place in results.get("results", []):
                places[place["place_id"]] = place
            
            next_page_token = results.get("next_page_token")
            attempts += 1
            if not next_page_token or attempts >= 5:
                break
        except Exception as e:
            st.warning(f"Error al obtener lugares para {place_type}: {e}")
            break
    return list(places.values())

if st.button("Iniciar Búsqueda"):
    with st.spinner("Buscando lugares en Bogotá..."):
        user_location = [4.60971, -74.08175]
        places_data = {"restaurant": [], "office": [], "transit_station": []}
        
        for category in places_data.keys():
            for _ in range(5):
                new_places = get_all_places(category, user_location)
                places_data[category].extend(new_places)
                time.sleep(2)
        
        mapa = folium.Map(location=user_location, zoom_start=12)
        marker_cluster = MarkerCluster().add_to(mapa)
        colors = {"restaurant": "red", "office": "blue", "transit_station": "green"}
        icons = {"restaurant": "utensils", "office": "briefcase", "transit_station": "bus"}
        
        for category, places in places_data.items():
            for place in places:
                if "geometry" in place and "location" in place["geometry"]:
                    lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
                    folium.Marker(
                        [lat, lon],
                        popup=f"{place['name']} - {category.capitalize()}\nDirección: {place.get('vicinity', 'No disponible')}",
                        icon=folium.Icon(color=colors[category], icon=icons[category], prefix='fa')
                    ).add_to(marker_cluster)
        
        folium_static(mapa)
