import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer

# =========================
# PAGE
# =========================
st.set_page_config(page_title="LLD Lookup", layout="centered")

st.title("LLD Lookup")
st.write("Konvertera WGS84 → SWEREF99 TM + geografisk information")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():

    with st.spinner("Laddar geodata..."):

        kommun = gpd.read_file("kommun.shp", engine="pyogrio").to_crs("EPSG:3006")
    
        lan = gpd.read_file("lan.shp", engine="pyogrio").to_crs("EPSG:3006")

        landskap = gpd.read_file("landskap.geo.json", engine="pyogrio").to_crs("EPSG:3006")
    
        distrikt = gpd.read_file("distrikt.gpkg", engine="pyogrio").to_crs("EPSG:3006")

    return kommun, lan, landskap, distrikt


kommun, lan, landskap, distrikt = load_data()

# =========================
# INPUT
# =========================
lat = st.number_input("Latitud (WGS84)", value=57.98735, format="%.8f")
lon = st.number_input("Longitud (WGS84)", value=14.854094, format="%.8f")

# =========================
# BUTTON
# =========================
if st.button("Hämta information"):

    # =========================
    # WGS84 -> SWEREF99
    # =========================
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:3006",
        always_xy=True
    )

    x, y = transformer.transform(lon, lat)

    point = Point(x, y)

    # =========================
    # LOOKUP FUNCTION
    # =========================
    def spatial_lookup(gdf):

        result = gdf[gdf.intersects(point)]

        if result.empty:
            result = gdf[gdf.intersects(point.buffer(100))]

        if result.empty:
            return None

        return result.iloc[0]

    # =========================
    # LOOKUPS
    # =========================
    kommun_hit = spatial_lookup(kommun)
    lan_hit = spatial_lookup(lan)
    landskap_hit = spatial_lookup(landskap)
    distrikt_hit = spatial_lookup(distrikt)

    # =========================
    # EXTRACT
    # =========================
    kommun_namn = kommun_hit["KnNamn"] if kommun_hit is not None else None

    lan_namn = lan_hit["LnNamn"] if lan_hit is not None else None

    landskap_namn = None

    if landskap_hit is not None:
    
        # testar vanliga kolumnnamn
        for col in landskap_hit.index:
    
            c = col.lower()
    
            if "namn" in c or "name" in c:
                landskap_namn = landskap_hit[col]
                break

    distrikt_namn = (
        distrikt_hit["distriktsnamn"]
        if distrikt_hit is not None
        else None
    )

    distrikt_kod = (
        distrikt_hit["distriktskod"]
        if distrikt_hit is not None
        else None
    )

    # =========================
    # LANDSDEL
    # =========================
    landsdel_map = {
    
        # Götaland
        "Skåne": "Götaland",
        "Blekinge": "Götaland",
        "Halland": "Götaland",
        "Småland": "Götaland",
        "Västergötland": "Götaland",
        "Östergötland": "Götaland",
        "Gotland": "Götaland",
        "Bohuslän": "Götaland",
        "Dalsland": "Götaland",
    
        # Svealand
        "Uppland": "Svealand",
        "Södermanland": "Svealand",
        "Västmanland": "Svealand",
        "Närke": "Svealand",
        "Värmland": "Svealand",
        "Dalarna": "Svealand",
    
        # Norrland
        "Gästrikland": "Norrland",
        "Hälsingland": "Norrland",
        "Medelpad": "Norrland",
        "Ångermanland": "Norrland",
        "Jämtland": "Norrland",
        "Västerbotten": "Norrland",
        "Norrbotten": "Norrland",
        "Lappland": "Norrland"
    }

    landsdel = landsdel_map.get(landskap_namn)
    
    # =========================
    # OUTPUT
    # =========================
    st.subheader("Resultat")
    
    st.write(f"### SWEREF99 TM")
    st.write(f"X: {x:.2f}")
    st.write(f"Y: {y:.2f}")
    
    st.write(f"### Geografisk information")
    st.write(f"Landsdel: {landsdel}")
    st.write(f"Län: {lan_namn}")
    st.write(f"Kommun: {kommun_namn}")
    
    st.write(f"Distrikt: {distrikt_namn}")
    st.write(f"Distriktskod: {distrikt_kod}")
