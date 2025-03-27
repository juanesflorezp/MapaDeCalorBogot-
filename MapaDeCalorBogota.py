import streamlit as st
import googlemaps
import time
import json
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import MarkerCluster
import os

st.title("📍 Mapa de Bogotá: Restaurantes y Cafés")

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw" 

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Definir múltiples ubicaciones para ampliar la cobertura
locations = [
    [4.60971, -74.08175],  # Centro
    [4.6351, -74.0703],    # Chapinero
    [4.6570, -74.0934],    # Teusaquillo
    [4.5893, -74.0745],    # La Candelaria
    [4.7041, -74.0424],    # Suba
    [4.6138, -74.2103]     # Bosa
]

def get_all_places(place_type, locations, radius=10000):
    places = {}
    for location in locations:
        next_page_token = None
        while True:
            try:
                # Hacer la solicitud con o sin token de paginación
                params = {"location": location, "radius": radius, "type": place_type}
                if next_page_token:
                    params["page_token"] = next_page_token
                    time.sleep(2)  # Google recomienda esperar antes de usar el token

                results = gmaps.places_nearby(**params)

                for place in results.get("results", []):
                    places[place["place_id"]] = place

                # Verificar si hay más páginas
                next_page_token = results.get("next_page_token")
                if not next_page_token:
                    break  # No hay más resultados
            except Exception as e:
                st.warning(f"Error al obtener lugares para {place_type}: {e}")
                break
    
    return list(places.values())

if st.button("Iniciar Búsqueda"):
    with st.spinner("Buscando lugares en Bogotá..."):
        categories = ["restaurant", "cafe"]
        places_data = {category: get_all_places(category, locations) for category in categories}
        
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
        mapa = folium.Map(location=[4.60971, -74.08175], zoom_start=12)
        marker_cluster = MarkerCluster().add_to(mapa)
        colors = {"restaurant": "red", "cafe": "brown"}
        icons = {"restaurant": "utensils", "cafe": "coffee"}
        
        # Agregar marcadores
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
    except FileNotFoundError:
        st.error("No se encontró el archivo places_data.json. Primero realiza la búsqueda.")
