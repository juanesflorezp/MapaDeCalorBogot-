import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static
import folium
from folium.plugins import HeatMap
import os

st.title("📍 Mapa de Oficinas, Restaurantes y TransMilenio en Bogotá")  # Título de la app

# Cargar variables de entorno
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw"  # Usar variable de entorno

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Coordenadas de Bogotá
ubicacion_bogota = [4.60971, -74.08175]
radio = 5000  # Búsqueda en 5km alrededor de Bogotá

# Opciones de categorías para mostrar
categorias_disponibles = {
    "restaurant": {"nombre": "🍽️ Restaurantes", "color": "red", "icono": "cutlery"},
    "real_estate_agency": {"nombre": "🏢 Oficinas", "color": "blue", "icono": "building"},
    "transit_station": {"nombre": "🚇 Estaciones de TransMilenio", "color": "green", "icono": "train"}
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

    # Obtener lugares cercanos solo para las categorías seleccionadas
    places_data = []
    with st.status("Obteniendo lugares...", expanded=True) as status:
        for category in categorias_seleccionadas:
            places = get_all_places(category, ubicacion_bogota, radio)
            places_data.extend(places)
            st.write(f"{len(places)} lugares encontrados en {categorias_disponibles[category]['nombre']}")

        status.update(label="Lugares obtenidos con éxito", state="complete")

    # Crear mapa con Folium para toda Bogotá
    mapa = folium.Map(location=ubicacion_bogota, zoom_start=12)

    if places_data:
        heat_data = []
        for place in places_data:
            lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
            heat_data.append([lat, lon])

            # Obtener la categoría del lugar
            place_types = place.get("types", [])
            categoria_valida = next((c for c in categorias_seleccionadas if c in place_types), None)

            if categoria_valida:
                info_categoria = categorias_disponibles[categoria_valida]

                # Agregar marcador al mapa
                folium.Marker(
                    location=[lat, lon],
                    popup=f"{place['name']} ({info_categoria['nombre']})\nRating: {place.get('rating', 'N/A')}",
                    icon=folium.Icon(color=info_categoria["color"], icon=info_categoria["icono"], prefix="fa")
                ).add_to(mapa)

        # Agregar capa de calor
        HeatMap(heat_data).add_to(mapa)

    folium_static(mapa)
