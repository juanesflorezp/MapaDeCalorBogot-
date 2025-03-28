import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static
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

# Ubicación fija: Bogotá
ubicacion_ciudad = [4.60971, -74.08175]
radio = 10000  # Radio fijo

st.info("Buscando restaurantes, bares, coworkings, oficinas y estaciones de TransMilenio (biarticulado) en el centro de Bogotá")

# --- FUNCIONES ---

def get_all_places(location, radius, search_type=None, keyword=None):
    places = {}
    next_page_token = None
    while True:
        try:
            if next_page_token:
                time.sleep(2)
                results = gmaps.places_nearby(
                    location=location,
                    radius=radius,
                    type=search_type,
                    keyword=keyword,
                    page_token=next_page_token
                )
            else:
                results = gmaps.places_nearby(
                    location=location,
                    radius=radius,
                    type=search_type,
                    keyword=keyword
                )
            
            for place in results.get("results", []):
                if place.get("rating", 0) >= 3.5:
                    places[place["place_id"]] = place
            
            next_page_token = results.get("next_page_token")
            if not next_page_token:
                break
        except Exception as e:
            st.warning(f"Error buscando '{keyword or search_type}': {e}")
            break
    return list(places.values())

# --- CATEGORÍAS PERSONALIZADAS ---

categories = {
    "restaurant": {"type": "restaurant", "color": "red", "icon": "utensils"},
    "bar": {"type": "bar", "color": "purple", "icon": "cocktail"},
    "coworking": {"keyword": "Coworking", "color": "green", "icon": "building"},
    "oficinas": {"keyword": "Oficinas", "color": "blue", "icon": "briefcase"},
    "transmilenio": {"keyword": "Estación TransMilenio", "color": "orange", "icon": "bus"}
}

if st.button("🔍 Buscar Lugares Cercanos"):
    with st.spinner("Buscando lugares..."):
        user_location = ubicacion_ciudad
        places_data = {}
        progress_bar = st.progress(0)

        heatmap_data = []
        mapa = folium.Map(location=user_location, zoom_start=15)
        marker_cluster = MarkerCluster().add_to(mapa)

        for i, (key, info) in enumerate(categories.items()):
            st.write(f"Buscando: {key}")
            places = get_all_places(
                location=user_location,
                radius=radio,
                search_type=info.get("type"),
                keyword=info.get("keyword")
            )
            places_data[key] = places
            progress_bar.progress((i + 1) / len(categories))
            st.write(f"{len(places)} lugares encontrados en {key}")

            for place in places:
                heatmap_data.append([place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]])

        progress_bar.empty()

        folium.Marker(user_location, popup="Centro de Bogotá", icon=folium.Icon(color="black", icon="info-sign")).add_to(mapa)

        for key, places in places_data.items():
            color = categories[key]["color"]
            icon = categories[key]["icon"]
            for place in places:
                lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
                folium.Marker(
                    [lat, lon],
                    popup=f"{place['name']} - Rating: {place.get('rating', 'N/A')}",
                    icon=folium.Icon(color=color, icon=icon, prefix='fa')
                ).add_to(marker_cluster)

        HeatMap(heatmap_data).add_to(mapa)
        folium_static(mapa)
