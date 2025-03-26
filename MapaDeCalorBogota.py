# -*- coding: utf-8 -*-

import streamlit as st
import googlemaps
import time
from dotenv import load_dotenv
from streamlit_folium import folium_static
import folium
from folium.plugins import HeatMap, MousePosition
import os

st.title("📍 Mapa de Oficinas, Restaurantes y TransMilenio en Bogotá")

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    st.error("API Key no encontrada. Asegúrate de definir GOOGLE_MAPS_API_KEY en un archivo .env")
    st.stop()

# Inicializar cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Selección de ubicación inicial en el mapa
st.write("Haz clic en el mapa para seleccionar la ubicación de búsqueda")

# Mapa inicial centrado en Bogotá
mapa_base = folium.Map(location=[4.72, -74.05], zoom_start=12)
mouse_position = MousePosition(position='topright', separator=' | ', empty_string='No data', num_digits=5, prefix='Lat: ', lat_formatter=None, lng_formatter=None)
mapa_base.add_child(mouse_position)

# Permitir al usuario seleccionar ubicación
if "ubicacion_seleccionada" not in st.session_state:
    st.session_state["ubicacion_seleccionada"] = [4.72, -74.05]

# Capturar clic del usuario en el mapa
mapa_base.add_child(folium.LatLngPopup())
folium_static(mapa_base)

st.write("Ubicación seleccionada: ", st.session_state["ubicacion_seleccionada"])

radio = 2000  # Reducido a 2km

# Categorías disponibles
categorias_disponibles = {
    "restaurant": {"nombre": "🍽️ Restaurantes", "color": "red", "icono": "cutlery"},
    "real_estate_agency": {"nombre": "🏢 Oficinas", "color": "blue", "icono": "building"},
    "office": {"nombre": "🏢 Oficinas en general", "color": "darkblue", "icono": "briefcase"},
    "coworking_space": {"nombre": "💼 Espacios de Coworking", "color": "purple", "icono": "users"},
    "transit_station": {"nombre": "🚇 Estaciones de TransMilenio", "color": "green", "icono": "train"},
}

categorias_seleccionadas = st.multiselect(
    "Selecciona las categorías a mostrar:",
    list(categorias_disponibles.keys()),
    default=list(categorias_disponibles.keys())
)

# Checkbox para mostrar/ocultar categorías en el mapa
filtros_visuales = {}
for categoria in categorias_seleccionadas:
    filtros_visuales[categoria] = st.checkbox(f"Mostrar {categorias_disponibles[categoria]['nombre']}", value=True)

# Estaciones principales de TransMilenio con buses biarticulados
transmilenio_principales = [
    "Portal Norte", "Calle 161", "Toberín", "Pepe Sierra", "Calle 100",
    "Av. Jiménez", "Calle 26", "Calle 57", "Flores", "Portal Américas",
    "Portal Usme", "Portal Suba", "Portal 80", "Portal Sur",
    "Héroes", "Calle 72", "Calle 85", "Marly", "Universidades"
]

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

                for place in places_result.get("results", []):
                    lat = place["geometry"]["location"]["lat"]
                    lon = place["geometry"]["location"]["lng"]

                    # Filtrar solo ubicaciones dentro de Bogotá
                    if 4.50 <= lat <= 4.85 and -74.20 <= lon <= -73.98:
                        places.append(place)

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
            places = get_all_places(category, st.session_state["ubicacion_seleccionada"], radio)
            if category == "transit_station":
                places = [p for p in places if any(name in p['name'] for name in transmilenio_principales)]
            places_data.extend(places)
            st.write(f"{len(places)} lugares encontrados en {categorias_disponibles[category]['nombre']}")

        status.update(label="Lugares obtenidos con éxito", state="complete")

    # Crear mapa con Folium
    mapa = folium.Map(location=st.session_state["ubicacion_seleccionada"], zoom_start=12)

    if places_data:
        heat_data = []
        for place in places_data:
            lat, lon = place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]
            heat_data.append([lat, lon])

            # Obtener la categoría del lugar
            place_types = place.get("types", [])
            categoria_valida = next((c for c in categorias_seleccionadas if c in place_types), None)

            if categoria_valida and filtros_visuales.get(categoria_valida, True):
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
