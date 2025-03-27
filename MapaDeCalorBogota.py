import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import HeatMap, MarkerCluster
import os

st.title("📍 Mapa de Lugares en Bogotá")

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

if "ubicacion_usuario" not in st.session_state:
    st.session_state["ubicacion_usuario"] = [4.60971, -74.08175]
if "direccion_obtenida" not in st.session_state:
    st.session_state["direccion_obtenida"] = ""

if mapa_data["last_clicked"]:
    lat, lon = mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"]
    st.session_state["ubicacion_usuario"] = [lat, lon]
    st.success(f"Ubicación seleccionada: {lat}, {lon}")

def get_all_places(place_type, location):
    places = {}
    next_page_token = None
    while True:
        try:
            if next_page_token:
                time.sleep(2)
                results = gmaps.places_nearby(
                    location=location,
                    radius=20000,  # Ampliar radio a 20 km
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
            if not next_page_token:
                break
        except Exception as e:
            st.warning(f"Error al obtener lugares para {place_type}: {e}")
            break
    return list(places.values())

category_icons = {
    "restaurant": "utensils",
    "transit_station": "bus",
    "real_estate_agency": "building"
}

category_colors = {
    "restaurant": "red",
    "transit_station": "blue",
    "real_estate_agency": "green"
}

if st.button("Iniciar Búsqueda"):
    with st.spinner("Buscando lugares en Bogotá..."):
        user_location = st.session_state["ubicacion_usuario"]
        places_data = {}
        categories = ["restaurant", "transit_station", "real_estate_agency"]
        progress_bar = st.progress(0)
        
        heatmap_data = []
        mapa = folium.Map(location=user_location, zoom_start=12)
        marker_cluster = MarkerCluster().add_to(mapa)
        
        for i, category in enumerate(categories):
            places_data[category] = get_all_places(category, user_location)
            progress_bar.progress((i + 1) / len(categories))
            st.write(f"{len(places_data[category])} lugares encontrados en {category}")
            
            for place in places_data[category]:
                if "geometry" in place and "location" in place["geometry"]:
                    lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
                    heatmap_data.append([lat, lon])
        
        progress_bar.empty()
        
        folium.Marker(user_location, popup="Ubicación seleccionada", icon=folium.Icon(color="black", icon="info-sign")).add_to(mapa)
        
        for category, places in places_data.items():
            for place in places:
                if "geometry" in place and "location" in place["geometry"]:
                    lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
                    folium.Marker(
                        [lat, lon],
                        popup=f"{place['name']} - Rating: {place.get('rating', 'N/A')}\nDirección: {place.get('vicinity', 'No disponible')}\nTipo: {category}",
                        icon=folium.Icon(color=category_colors.get(category, "gray"), icon=category_icons.get(category, "info-sign"), prefix='fa')
                    ).add_to(marker_cluster)
        
        HeatMap(heatmap_data).add_to(mapa)
        folium_static(mapa)
