import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static
import folium
from folium.plugins import HeatMap, MarkerCluster
import os

st.set_page_config(page_title="Mapa Lugares Bogotá", layout="wide")
st.title("📍 Mapa de Lugares en Bogotá — Modo Interactivo")

# Cargar API Key
load_dotenv()
API_KEY = "AIzaSyAfKQcxysKHp0qSrKIlBj6ZXnF1x-McWtw"
if not API_KEY:
    st.error("API Key no encontrada.")
    st.stop()

gmaps = googlemaps.Client(key=API_KEY)

# --- Configuración ---
ubicacion_ciudad = [4.6805, -74.0451]  # Zona Parque El Virrey
radio = 700  # 700 metros
grid_size = 2  # 2x2 cuadrantes (10 puntos máximo)

categories = {
    "restaurant": {"type": "restaurant", "color": "red", "icon": "utensils"},
    "bar": {"type": "bar", "color": "purple", "icon": "cocktail"},
    "coworking": {"keyword": "Coworking", "color": "green", "icon": "building"},
    "oficinas": {"keyword": "Oficinas", "color": "blue", "icon": "briefcase"},
    "transmilenio": {"keyword": "Estación TransMilenio", "color": "orange", "icon": "bus"}
}

# Checkboxes para activar/desactivar categorías
selected_categories = {}
with st.sidebar:
    st.header("🔍 Filtros de Categoría")
    for key in categories:
        selected_categories[key] = st.checkbox(key.capitalize(), True)

def get_all_places(location, radius, search_type=None, keyword=None):
    places = {}
    next_page_token = None
    count = 0
    while count < 10:  # Limitar a 10 resultados
        try:
            if next_page_token:
                time.sleep(2)
                results = gmaps.places_nearby(
                    location=location, radius=radius, type=search_type, keyword=keyword, page_token=next_page_token
                )
            else:
                results = gmaps.places_nearby(
                    location=location, radius=radius, type=search_type, keyword=keyword
                )
            for place in results.get("results", []):
                places[place["place_id"]] = place
                count += 1
                if count >= 10:
                    break
            next_page_token = results.get("next_page_token")
            if not next_page_token:
                break
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
            if len(grid) >= 10:
                return grid  # Limitar la cantidad de puntos en la cuadrícula
    return grid

if st.button("🚀 Iniciar Búsqueda (Modo Interactivo)"):
    with st.spinner("Buscando en múltiples cuadrantes..."):
        grid = generar_grid(ubicacion_ciudad, radio * 1.5, grid_size)
        st.write(f"Buscando en {len(grid)} puntos. Esto puede tomar unos minutos...")

        all_places = {}
        progress = st.progress(0)
        total = len(grid) * len(categories)

        heatmap_data = []
        mapa = folium.Map(location=ubicacion_ciudad, zoom_start=13, width='100%', height='800px')
        marker_cluster = MarkerCluster().add_to(mapa)

        count = 0
        for (lat, lon) in grid:
            for key, info in categories.items():
                if not selected_categories[key]:
                    continue  # Omitir categorías desactivadas
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
                if count >= 10:
                    break
            if count >= 10:
                break

        progress.empty()
        st.success(f"✅ {len(all_places)} lugares encontrados (sin duplicados)")

        for place in all_places.values():
            lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
            heatmap_data.append([lat, lon])
            for key, info in categories.items():
                if (info.get("type") == place.get("types", [None])[0]) or (info.get("keyword") and info["keyword"].lower() in place["name"].lower()):
                    if not selected_categories[key]:
                        continue  # Omitir si está desactivado
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
