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

# Radio y cantidad de resultados configurables
radio = st.slider("Selecciona el radio de búsqueda (metros):", min_value=100, max_value=5000, value=1000, step=100)
max_results = st.slider("Cantidad mínima de resultados por categoría:", min_value=20, max_value=200, value=100, step=10)

opcion_busqueda = st.radio("¿Cómo quieres buscar?", ("Usar ubicación seleccionada", "Seleccionar ubicación en el mapa"))

if "ubicacion_usuario" not in st.session_state:
    st.session_state["ubicacion_usuario"] = None

mapa = folium.Map(location=user_location, zoom_start=14)
mapa_data = st_folium(mapa, width=700, height=500)

if mapa_data["last_clicked"]:
    lat, lon = mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"]
    st.session_state["ubicacion_usuario"] = (lat, lon)
    st.success(f"Ubicación personalizada seleccionada: {lat}, {lon}")


def get_all_places(place_type, location, radius=1000, max_results=100):
    places = {}
    next_page_token = None
    attempts = 0
    while attempts < 20 and len(places) < max_results:
        try:
            params = {"location": location, "radius": radius, "type": place_type}
            if next_page_token:
                params["page_token"] = next_page_token
                time.sleep(2)

            results = gmaps.places_nearby(**params)

            for place in results.get("results", []):
                places[place["place_id"]] = place
                if len(places) >= max_results:
                    break

            next_page_token = results.get("next_page_token")
            if not next_page_token or len(places) >= max_results:
                break

            attempts += 1
        except Exception as e:
            st.warning(f"Error al obtener lugares para {place_type}: {e}")
            break

    return list(places.values())


if st.button("Iniciar Búsqueda"):
    with st.spinner(f"Buscando lugares en {user_location_name}..."):
        if opcion_busqueda == "Seleccionar ubicación en el mapa" and st.session_state["ubicacion_usuario"]:
            search_location = st.session_state["ubicacion_usuario"]
        else:
            search_location = user_location

        categories = ["bar", "cafe", "restaurant", "office", "transit_station"]
        places_data = {category: [] for category in categories}

        for category in categories:
            places_data[category] = get_all_places(category, search_location, radius=radio, max_results=max_results)
            st.write(f"{len(places_data[category])} lugares encontrados en {category}")

        # Guardar resultados en un archivo JSON
        file_name = f"places_data_{user_location_name}.json"
        with open(file_name, "w") as f:
            json.dump(places_data, f)
        st.success(f"Datos guardados correctamente en {file_name}")

# Botón para generar el mapa desde el archivo guardado
if st.button("Generar Mapa"):
    file_name = f"places_data_{user_location_name}.json"
    try:
        with open(file_name, "r") as f:
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
        st.error(f"No se encontró el archivo {file_name}. Primero realiza la búsqueda.")
