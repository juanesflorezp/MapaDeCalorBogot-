import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static, st_folium
import folium
from folium.plugins import HeatMap
import os

st.title("📍 Mapa de Oficinas, Restaurantes y TransMilenio en Bogotá")  # Título de la app

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Usar variable de entorno

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Coordenadas de Bogotá
ubicacion_ciudad = [4.60971, -74.08175]

# Input para definir el radio de búsqueda
radio = st.slider("Selecciona el radio de búsqueda (metros):", min_value=100, max_value=5000, value=500, step=100)

# Inicializar session_state si no existe
if "ubicacion_usuario" not in st.session_state:
    st.session_state["ubicacion_usuario"] = None
if "direccion_obtenida" not in st.session_state:
    st.session_state["direccion_obtenida"] = ""

# Crear mapa base solo una vez
mapa = folium.Map(location=ubicacion_ciudad, zoom_start=14)

# Mostrar mapa interactivo con `st_folium`
mapa_data = st_folium(mapa, width=700, height=500)

# Si el usuario ha hecho clic en una nueva ubicación
if mapa_data["last_clicked"]:
    lat, lon = mapa_data["last_clicked"]["lat"], mapa_data["last_clicked"]["lng"]
    
    # Solo actualizar session_state si la ubicación cambia
    if st.session_state["ubicacion_usuario"] != (lat, lon):
        st.session_state["ubicacion_usuario"] = (lat, lon)

        # Obtener dirección inversa con Google Maps
        try:
            reverse_geocode_result = gmaps.reverse_geocode((lat, lon))
            if reverse_geocode_result:
                st.session_state["direccion_obtenida"] = reverse_geocode_result[0]["formatted_address"]
                st.success(f"Ubicación seleccionada: {st.session_state['direccion_obtenida']}")
        except Exception as e:
            st.warning(f"Error al obtener dirección: {e}")

# Botón para iniciar la búsqueda
if st.button("Iniciar Búsqueda"):

    # Definir categorías específicas de búsqueda
    categories = {
        "restaurant": "🍽️ Restaurante",
        "real_estate_agency": "🏢 Oficina",
        "transit_station": "🚇 Estación TransMilenio"
    }

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

    # Obtener lugares cercanos
    places_data = []
    with st.status("Obteniendo lugares...", expanded=True) as status:
        for category, name in categories.items():
            places = get_all_places(category, st.session_state["ubicacion_usuario"] or ubicacion_ciudad, radio)
            places_data.extend(places)
            st.write(f"{len(places)} lugares encontrados en {name}")

        status.update(label="Lugares obtenidos con éxito", state="complete")

    # Diccionario de iconos por categoría
    iconos_categorias = {
        "restaurant": {"icon": "cutlery", "color": "red"},
        "real_estate_agency": {"icon": "building", "color": "blue"},
        "transit_station": {"icon": "train", "color": "green"},
    }

    # Crear mapa con Folium y agregar los lugares encontrados
    mapa = folium.Map(location=st.session_state["ubicacion_usuario"] or ubicacion_ciudad, zoom_start=16)
    folium.Marker(
        location=st.session_state["ubicacion_usuario"] or ubicacion_ciudad,
        popup="Ubicación seleccionada",
        icon=folium.Icon(color="red", icon="star", prefix="glyphicon")
    ).add_to(mapa)

    if places_data:
        for place in places_data:
            place_types = place.get("types", [])
            categoria_valida = next((c for c in categories if c in place_types), None)

            if categoria_valida:
                icono_info = iconos_categorias[categoria_valida]

                folium.Marker(
                    location=[place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]],
                    popup=f"{place['name']} ({categories[categoria_valida]})\nRating: {place.get('rating', 'N/A')}",
                    icon=folium.Icon(color=icono_info["color"], icon=icono_info["icon"], prefix="fa")
                ).add_to(mapa)

        # Agregar capa de calor
        heat_data = [[p["geometry"]["location"]["lat"], p["geometry"]["location"]["lng"]] for p in places_data]
        HeatMap(heat_data).add_to(mapa)

    folium_static(mapa)
