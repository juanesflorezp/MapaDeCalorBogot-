import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import HeatMap, MarkerCluster
import os

st.title("📍 Mapa de Lugares en Bogotá")

# Cargar API KEY
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en .env")
    st.stop()

# Cliente Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Coordenadas iniciales (norte de Bogotá)
ubicacion_bogota = [4.710989, -74.072090]

# Categorías personalizadas
categories = {
    "coworking": {"keyword": "Coworking", "color": "red", "icon": "building"},
    "oficinas": {"keyword": "Oficinas", "color": "purple", "icon": "briefcase"},
    "transmilenio": {"keyword": "Estación TransMilenio", "color": "green", "icon": "bus"},
}

# Dividir Bogotá en cuadrantes
def generar_cuadrantes(centro, radio, num_cuadrantes):
    cuadrantes = []
    lat, lon = centro
    delta = radio / 111320  # metros a grados
    for i in range(num_cuadrantes):
        for j in range(num_cuadrantes):
            cuadrantes.append((lat + i * delta, lon + j * delta))
    return cuadrantes

def get_all_places(location, radius, category_key, category_info):
    places = {}
    next_page_token = None

    while True:
        try:
            if next_page_token:
                time.sleep(2)
                results = gmaps.places_nearby(
                    location=location,
                    radius=radius,
                    keyword=category_info.get("keyword"),
                    page_token=next_page_token
                )
            else:
                results = gmaps.places_nearby(
                    location=location,
                    radius=radius,
                    keyword=category_info.get("keyword")
                )

            for place in results.get("results", []):
                place_id = place["place_id"]
                place["category_key"] = category_key  # 🔥 Guardamos la categoría
                places[place_id] = place

            next_page_token = results.get("next_page_token")
            if not next_page_token:
                break
        except Exception as e:
            st.warning(f"Error obteniendo lugares ({category_key}): {e}")
            break

    return list(places.values())

# ✅ Selector para definir cantidad de cuadrantes
num_cuadrantes = st.slider("Número de cuadrantes para ampliar búsqueda:", min_value=2, max_value=8, value=3, step=1)
st.caption(f"Entre más cuadrantes, más resultados (y más tiempo de búsqueda). Actualmente: {num_cuadrantes**2} cuadrantes")

if st.button("🔍 Buscar lugares"):
    with st.spinner("Buscando lugares en Bogotá..."):
        radio = 1000  # 1km por cuadrante
        cuadrantes = generar_cuadrantes(ubicacion_bogota, radio, num_cuadrantes)

        all_places = []
        progress = st.progress(0)
        total = len(categories) * len(cuadrantes)
        counter = 0

        for category_key, category_info in categories.items():
            for centro in cuadrantes:
                places = get_all_places(centro, radio, category_key, category_info)
                all_places.extend(places)
                counter += 1
                progress.progress(counter / total)

        progress.empty()

        # Mostrar en el mapa
        mapa = folium.Map(location=ubicacion_bogota, zoom_start=12)
        marker_cluster = MarkerCluster().add_to(mapa)
        heatmap_data = []

        for place in all_places:
            lat = place["geometry"]["location"]["lat"]
            lon = place["geometry"]["location"]["lng"]
            name = place.get("name", "Lugar")
            rating = place.get("rating", "N/A")

            # Recuperar categoría
            category_key = place.get("category_key")
            if category_key and category_key in categories:
                color = categories[category_key]["color"]
                icon = categories[category_key]["icon"]
            else:
                color = "cadetblue"
                icon = "info-sign"

            folium.Marker(
                [lat, lon],
                popup=f"{name} - Rating: {rating}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(marker_cluster)

            heatmap_data.append([lat, lon])

        HeatMap(heatmap_data).add_to(mapa)
        folium_static(mapa)

        st.success(f"✅ {len(all_places)} lugares encontrados y marcados")

