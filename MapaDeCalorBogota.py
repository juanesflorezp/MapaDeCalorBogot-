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
                places[place["place_id"]] = place  # <-- Aquí quitamos el filtro de rating

            next_page_token = results.get("next_page_token")
            if not next_page_token:
                break
        except Exception as e:
            st.warning(f"Error buscando '{keyword or search_type}': {e}")
            break
    return list(places.values())
