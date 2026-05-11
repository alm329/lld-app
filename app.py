import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer
import folium
from streamlit_folium import st_folium
import json

# =========================
# PAGE
# =========================
st.set_page_config(
    page_title="LLD Lookup",
    page_icon="🗺️",
    layout="wide"
)

# =========================
# CSS
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    max-width: 1100px;
    padding-left: 2rem;
    padding-right: 2rem;
}
.info-box {
    background: var(--secondary-background-color);
    padding: 0.9rem 1.1rem;
    border-radius: 12px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 1rem;
    font-size: 0.93rem;
    line-height: 1.7;
    color: var(--text-color);
}
.info-box strong { color: #2563eb; }
div[data-baseweb="input"] { max-width: 350px; }
.stFormSubmitButton > button {
    background: #2563eb;
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    width: auto !important;
    min-width: 110px;
    white-space: nowrap;
}
.stFormSubmitButton > button:hover { background: #1d4ed8; }
.result-heading {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
    color: var(--text-color);
}
.value-row {
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.35rem;
    border: 1px solid rgba(128,128,128,0.2);
    background: var(--secondary-background-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
}
.value-text { flex: 1; }
.value-label {
    font-size: 0.72rem;
    opacity: 0.55;
    margin-bottom: 0.1rem;
    color: var(--text-color);
}
.value-main {
    font-weight: 600;
    font-size: 0.93rem;
    color: var(--text-color);
}
.copy-btn {
    background: none;
    border: 1px solid rgba(128,128,128,0.3);
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
    cursor: pointer;
    color: var(--text-color);
    opacity: 0.6;
    font-size: 0.95rem;
    line-height: 1;
    transition: all 0.15s;
}
.copy-btn:hover {
    opacity: 1;
    border-color: #2563eb;
    color: #2563eb;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.title("LLD Lookup")

st.markdown("""
<div class="info-box">
    Det här verktyget låter dig slå upp geografisk information för en valfri plats i Sverige.
    Klistra in eller skriv in koordinater (t.ex. från Google Maps) i fälten nedan och klicka på
    <b><em>Hämta</em></b> – du får då:<br><br>
    Koordinater omvandlade till SWEREF99 TM (det svenska standardkoordinatsystemet)<br>
    Landsdel, landskap, län, kommun och distrikt för punkten<br>
    Punkten visualiserad på en interaktiv karta<br><br>
    <em>Tips: I Google Maps högerklickar du på en punkt och kopierar koordinaterna direkt därifrån.</em>
</div>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    kommun   = gpd.read_file("kommun.shp",       engine="pyogrio").to_crs("EPSG:3006")
    lan      = gpd.read_file("lan.shp",           engine="pyogrio").to_crs("EPSG:3006")
    landskap = gpd.read_file("landskap.geo.json", engine="pyogrio").to_crs("EPSG:3006")
    distrikt = gpd.read_file("distrikt.gpkg",     engine="pyogrio").to_crs("EPSG:3006")
    return kommun, lan, landskap, distrikt

kommun, lan, landskap, distrikt = load_data()

# =========================
# SESSION STATE
# =========================
if "result" not in st.session_state:
    st.session_state.result = None

# =========================
# INPUT ROW
# =========================
with st.form("lookup_form"):
    col1, col2, col3, _ = st.columns([3, 3, 1, 4], vertical_alignment="bottom")
    with col1:
        lat_input = st.text_input("Latitud", placeholder="Ex. 57.98735")
    with col2:
        lon_input = st.text_input("Longitud", placeholder="Ex. 14.854094")
    with col3:
        run_lookup = st.form_submit_button("Hämta")

# =========================
# LOOKUP
# =========================
if run_lookup:
    if not lat_input or not lon_input:
        st.error("Fyll i både latitud och longitud innan du skickar.")
    else:
        try:
            lat = float(lat_input.replace(",", "."))
            lon = float(lon_input.replace(",", "."))

            transformer = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
            x, y = transformer.transform(lon, lat)
            point = Point(x, y)

            def spatial_lookup(gdf):
                result = gdf[gdf.intersects(point)]
                if result.empty:
                    result = gdf[gdf.intersects(point.buffer(100))]
                return None if result.empty else result.iloc[0]

            kommun_hit   = spatial_lookup(kommun)
            lan_hit      = spatial_lookup(lan)
            landskap_hit = spatial_lookup(landskap)
            distrikt_hit = spatial_lookup(distrikt)

            def safe(hit, field):
                return "Okänd" if hit is None else str(hit[field])

            st.session_state.result = {
                "lat": lat,
                "lon": lon,
                "SWEREF N/S":     f"{y:.2f}",
                "SWEREF Ö/V":     f"{x:.2f}",
                "Landsdel":     safe(landskap_hit, "landsdel"),
                "Län":          safe(lan_hit,      "LnNamn"),
                "Landskap":     safe(landskap_hit, "landskap"),
                "Kommun":       safe(kommun_hit,   "KnNamn"),
                "Distrikt":     safe(distrikt_hit, "distriktsnamn"),
                "Distriktskod": safe(distrikt_hit, "distriktskod"),
            }

        except Exception as e:
            st.error("Kunde inte hämta information. Kontrollera att koordinaterna är giltiga (t.ex. 57.987, 14.854).")
            st.exception(e)  # Ta bort i produktion

# =========================
# VISA RESULTAT
# =========================
if st.session_state.result:
    r = st.session_state.result
    lat, lon = r["lat"], r["lon"]

    display_keys = [
        "SWEREF N/S", "SWEREF Ö/V", "Landsdel", "Län",
        "Landskap", "Kommun", "Distrikt", "Distriktskod"
    ]

    st.markdown("""
    <style>
    /* Minska gap mellan element i kolumnen */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        gap: 0.1rem !important;
    }

    /* Etikett: liten, tight, nästan klistrad mot kodrutan */
    div[data-testid="stCaptionContainer"], .stCaption, p.st-emotion-cache-1rsyhoq {
        margin: 0.2rem 0 0rem 0.15rem !important;
        padding: 0 !important;
        font-size: 0.78rem !important;
        line-height: 1 !important;
        opacity: 0.65;
    }

    /* Större kodruta (mer luft inuti, större text) */
    div[data-testid="stCode"] {
        margin: 0 0 0.35rem 0 !important;
    }
    div[data-testid="stCode"] pre {
        padding: 0.7rem 0.9rem !important;
        margin: 0 !important;
        font-size: 1rem !important;
        line-height: 1.3 !important;
    }

    /* Kopieringsknapp alltid synlig */
    div[data-testid="stCode"] button[title="Copy to clipboard"],
    div[data-testid="stCode"] button[data-testid="stCodeCopyButton"],
    div[data-testid="stCode"] button[kind="copyButton"],
    div[data-testid="stCode"] [data-testid="stTooltipHoverTarget"],
    div[data-testid="stCode"] button[data-testid="stBaseButton-elementToolbar"] {
        opacity: 1 !important;
        visibility: visible !important;
        pointer-events: auto !important;
    }
                

    p {
        margin: 0 0 0 0;
    }

     /* Dölj Streamlits "Press Enter to submit form" text i formulär */
        div[data-testid="stForm"] div[data-testid="stTextInput"] + div {
        display: none !important;
    }          

                
    </style>
""", unsafe_allow_html=True)


    result_col, map_col = st.columns([1, 2])

    with result_col:
        for key in display_keys:
            value = r.get(key, "")
            st.caption(key)
            st.code(str(value), language=None)

    with map_col:
        m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
        folium.Marker([lat, lon], tooltip=f"{lat}, {lon}").add_to(m)
        st_folium(m, width=None, height=500, key="map")




# =======================================================
# =======================================================
# =======================================================
# =======================================================


# import streamlit as st
# import geopandas as gpd
# from shapely.geometry import Point
# from pyproj import Transformer

# # =========================
# # PAGE
# # =========================
# st.set_page_config(page_title="LLD Lookup", layout="centered")

# st.title("LLD Lookup")
# st.write("Konvertera WGS84 → SWEREF99 TM + geografisk information")

# # =========================
# # LOAD DATA
# # =========================
# @st.cache_data
# def load_data():

#     with st.spinner("Laddar geodata..."):

#         kommun = gpd.read_file("kommun.shp", engine="pyogrio").to_crs("EPSG:3006")
    
#         lan = gpd.read_file("lan.shp", engine="pyogrio").to_crs("EPSG:3006")

#         landskap = gpd.read_file("landskap.geo.json", engine="pyogrio").to_crs("EPSG:3006")
    
#         distrikt = gpd.read_file("distrikt.gpkg", engine="pyogrio").to_crs("EPSG:3006")

#     return kommun, lan, landskap, distrikt


# kommun, lan, landskap, distrikt = load_data()

# # =========================
# # INPUT
# # =========================
# lat = st.number_input("Latitud (WGS84)", value=57.98735, format="%.8f")
# lon = st.number_input("Longitud (WGS84)", value=14.854094, format="%.8f")

# # =========================
# # BUTTON
# # =========================
# if st.button("Hämta information"):

#     # =========================
#     # WGS84 -> SWEREF99
#     # =========================
#     transformer = Transformer.from_crs(
#         "EPSG:4326",
#         "EPSG:3006",
#         always_xy=True
#     )

#     x, y = transformer.transform(lon, lat)

#     point = Point(x, y)

#     # =========================
#     # LOOKUP FUNCTION
#     # =========================
#     def spatial_lookup(gdf):

#         result = gdf[gdf.intersects(point)]

#         if result.empty:
#             result = gdf[gdf.intersects(point.buffer(100))]

#         if result.empty:
#             return None

#         return result.iloc[0]

#     # =========================
#     # LOOKUPS
#     # =========================
#     kommun_hit = spatial_lookup(kommun)
#     lan_hit = spatial_lookup(lan)
#     landskap_hit = spatial_lookup(landskap)
#     distrikt_hit = spatial_lookup(distrikt)

#     # =========================
#     # EXTRACT
#     # =========================
#     kommun_namn = kommun_hit["KnNamn"] if kommun_hit is not None else None

#     lan_namn = lan_hit["LnNamn"] if lan_hit is not None else None

#     landskap_namn = None
    
#     if landskap_hit is not None:

#         # GeoJSON-fält
#         if "landskap" in landskap_hit.index:
#             landskap_namn = landskap_hit["landskap"]
    
#         # fallback
#         else:
#             for col in landskap_hit.index:
    
#                 c = col.lower()
    
#                 if "namn" in c or "name" in c:
#                     landskap_namn = landskap_hit[col]
#                     break

#     distrikt_namn = (
#         distrikt_hit["distriktsnamn"]
#         if distrikt_hit is not None
#         else None
#     )

#     distrikt_kod = (
#         distrikt_hit["distriktskod"]
#         if distrikt_hit is not None
#         else None
#     )

#     # =========================
#     # LANDSDEL
#     # =========================
#     landsdel_map = {
    
#         # Götaland
#         "Skåne": "Götaland",
#         "Blekinge": "Götaland",
#         "Halland": "Götaland",
#         "Småland": "Götaland",
#         "Västergötland": "Götaland",
#         "Östergötland": "Götaland",
#         "Gotland": "Götaland",
#         "Bohuslän": "Götaland",
#         "Dalsland": "Götaland",
    
#         # Svealand
#         "Uppland": "Svealand",
#         "Södermanland": "Svealand",
#         "Västmanland": "Svealand",
#         "Närke": "Svealand",
#         "Värmland": "Svealand",
#         "Dalarna": "Svealand",
    
#         # Norrland
#         "Gästrikland": "Norrland",
#         "Hälsingland": "Norrland",
#         "Medelpad": "Norrland",
#         "Ångermanland": "Norrland",
#         "Jämtland": "Norrland",
#         "Västerbotten": "Norrland",
#         "Norrbotten": "Norrland",
#         "Lappland": "Norrland"
#     }

#     landsdel = landsdel_map.get(landskap_namn)
    
#     # =========================
#     # OUTPUT
#     # =========================
#     st.subheader("Resultat")
    
#     st.write(f"### SWEREF99 TM")
#     st.write(f"X: {x:.2f}")
#     st.write(f"Y: {y:.2f}")
    
#     st.write(f"### Geografisk information")
#     st.write(f"Landsdel: {landsdel}")
#     st.write(f"Län: {lan_namn}")
#     st.write(f"Landskap: {landskap_namn}")
#     st.write(f"Kommun: {kommun_namn}")
    
#     st.write(f"Distrikt: {distrikt_namn}")
#     st.write(f"Distriktskod: {distrikt_kod}")
