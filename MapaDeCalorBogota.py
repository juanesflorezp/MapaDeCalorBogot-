import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static
import folium
from folium.plugins import HeatMap, MarkerCluster
import os

st.set_page_config(page_title="Mapa Lugares Bogotá", layout="wide")
st.title("📍 Mapa de Lugares en Bogotá — Modo Turbo")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw"

if not API_KEY:
    st.error("API Key no encontrada.")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# --- Configuración ---
ubicacion_ciudad_1 = [4.6765, -74.0488]  # Zona Parque de la 93 (Bogotá)
ubicacion_ciudad_2 = [4.5970, -74.0830]  # Centro de Bogotá (Plaza de Bolívar)
radio = 10000  # 10 km de radio
grid_size = 6  # 6x6 cuadrantes (36 puntos)

categories = {
    "restaurant": {"type": "restaurant", "color": "red", "icon": "utensils"},
    "bar": {"type": "bar", "color": "purple", "icon": "cocktail"},
    "coworking": {"keyword": "Coworking", "color": "green", "icon": "building"},
    "oficinas": {"keyword": "Oficinas", "color": "blue", "icon": "briefcase"},
    "transmilenio": {"keyword": "Estación TransMilenio", "color": "orange", "icon": "bus"}
}

# --- FUNCIONES ---

def get_all_places(location, radius, search_type=None, keyword=None):
    places = {}
    next_page_token = None
    while True:
        try:
            # Recorremos todas las páginas de resultados sin limitar
            if next_page_token:
                time.sleep(2)  # Retardo entre páginas para no exceder el límite de la API
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
                places[place["place_id"]] = place  # Agregamos los lugares a la lista

            next_page_token = results.get("next_page_token")
            if not next_page_token:
                break  # Si no hay más páginas, terminamos la búsqueda
        except Exception as e:
            st.warning(f"Error buscando '{keyword or search_type}': {e}")
            break
    return list(places.values())

def generar_grid(centro, distancia, puntos):
    lat_centro, lon_centro = centro
    grid = []
    delta = distancia / 111000  # Aproximado: 1° lat ~ 111 km

    for i in range(-puntos, puntos + 1):
        for j in range(-puntos, puntos + 1):
            lat = lat_centro + i * delta
            lon = lon_centro + j * delta
            grid.append((lat, lon))
    return grid

if st.button("🚀 Iniciar Búsqueda (Modo Turbo)"):
    with st.spinner("Buscando en múltiples cuadrantes..."):
        # Generar la cuadrícula para el área del Parque de la 93
        grid_1 = generar_grid(ubicacion_ciudad_1, radio * 1.5, grid_size)
        # Generar la cuadrícula para el área del centro de Bogotá
        grid_2 = generar_grid(ubicacion_ciudad_2, radio * 1.5, grid_size)

        # Combinar las cuadrículas
        grid = grid_1 + grid_2

        st.write(f"Buscando en {len(grid)} puntos. Esto puede tomar unos minutos...")

        all_places = {}
        progress = st.progress(0)
        total = len(grid) * len(categories)

        heatmap_data = []
        mapa = folium.Map(location=ubicacion_ciudad_1, zoom_start=12, width='100%', height='800px')
        marker_cluster = MarkerCluster().add_to(mapa)

        count = 0
        for (lat, lon) in grid:
            for key, info in categories.items():
                places = get_all_places(
                    location=(lat, lon),
                    radius=radio,
                    search_type=info.get("type"),
                    keyword=info.get("keyword")
                )
                for place in places:
                    all_places[place["place_id"]] = place
                count += 1
                progress.progress(count / total)

        progress.empty()
        st.success(f"✅ {len(all_places)} lugares encontrados (sin duplicados)")

        for place in all_places.values():
            lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
            heatmap_data.append([lat, lon])
            for key, info in categories.items():
                if (info.get("type") == place.get("types", [None])[0]) or (info.get("keyword") and info["keyword"].lower() in place["name"].lower()):
                    color = info["color"]
                    icon = info["icon"]
                    break
            else:
                color = "gray"
                icon = "info-sign"

            folium.Marker(
                [lat, lon],
                popup=f"{place['name']} - Rating: {place.get('rating', 'N/A')}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(marker_cluster)

        HeatMap(heatmap_data).add_to(mapa)
        folium_static(mapa, width=1500, height=800)
