import streamlit as st
import googlemaps
import time
import json
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import MarkerCluster
import os

st.title("📍 Mapa de Bogotá: Lugares de Interés")

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Selección de ubicación por el usuario
st.subheader("Selecciona una ubicación en Bogotá")
locations_dict = {
    "Centro": [4.60971, -74.08175],
    "Chapinero": [4.6351, -74.0703],
    "Teusaquillo": [4.6570, -74.0934],
    "Usaquén": [4.6768, -74.0484],
    "Suba": [4.7041, -74.0424],
    "Parque de la 93": [4.6720, -74.0575],
    "Zona T": [4.6823, -74.0532]
}
user_location_name = st.selectbox("Ubicación", list(locations_dict.keys()))
user_location = locations_dict[user_location_name]

# Radio reducido a 5km
SEARCH_RADIUS = 5000

def get_all_places(place_types, location, radius=SEARCH_RADIUS):
    places = {}
    for place_type in place_types:
        next_page_token = None
        attempts = 0
        while attempts < 5:  # Intentar hasta 5 páginas de resultados
            try:
                params = {"location": location, "radius": radius, "type": place_type}
                if next_page_token:
                    params["page_token"] = next_page_token
                    time.sleep(2)  # Google recomienda esperar antes de usar el token

                results = gmaps.places_nearby(**params)

                for place in results.get("results", []):
                    places[place["place_id"]] = place

                next_page_token = results.get("next_page_token")
                if not next_page_token:
                    break  # No hay más resultados
                
                attempts += 1
            except Exception as e:
                st.warning(f"Error al obtener lugares para {place_type}: {e}")
                break
    
    return list(places.values())

if st.button("Iniciar Búsqueda"):
    with st.spinner(f"Buscando lugares en {user_location_name}..."):
        categories = ["bar", "cafe", "restaurant", "office", "transit_station"]
        places_data = {category: [] for category in categories}
        
        for category in categories:
            places_data[category] = get_all_places([category], user_location)
        
        # Guardar resultados en un archivo JSON
        with open("places_data.json", "w") as f:
            json.dump(places_data, f)
        st.success("Datos guardados correctamente en places_data.json")

# Botón para generar el mapa desde el archivo guardado
if st.button("Generar Mapa"):
    try:
        with open("places_data.json", "r") as f:
            places_data = json.load(f)
        
        # Crear mapa
        mapa = folium.Map(location=user_location, zoom_start=14)
        marker_cluster = MarkerCluster().add_to(mapa)
        colors = {
            "restaurant": "red", "cafe": "brown", "bar": "blue", "office": "green",
            "transit_station": "purple"
        }
        icons = {
            "restaurant": "utensils", "cafe": "coffee", "bar": "beer", "office": "building",
            "transit_station": "bus"
        }
        
        # Agregar marcadores
        for category, places in places_data.items():
            for place in places:
                if "geometry" in place and "location" in place["geometry"]:
                    lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
                    folium.Marker(
                        [lat, lon],
                        popup=f"{place['name']} - {category.replace('_', ' ').capitalize()}\nDirección: {place.get('vicinity', 'No disponible')}",
                        icon=folium.Icon(color=colors.get(category, "gray"), icon=icons.get(category, "map-marker"), prefix='fa')
                    ).add_to(marker_cluster)
        
        folium_static(mapa)
    except FileNotFoundError:
        st.error("No se encontró el archivo places_data.json. Primero realiza la búsqueda.")
