"""Project paths and constants.

Paths resolve from this file's location, not the working directory, so
everything works identically from a notebook, a script or a test —
regardless of where the process was launched.
"""

from pathlib import Path

# src/thessmap/config.py -> src/thessmap -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA = PROJECT_ROOT / "data"

# Source GeoPackages. These currently sit directly in data/; the intended
# layout is data/raw/. Moving them needs write permission on data/, which
# is read-only today, so point at the flat layout and switch when it moves.
RAW = DATA

PROCESSED = DATA / "processed"
ICONS = DATA / "icons"
TILES = DATA / "tiles"

# Population grids: the 100 m density surface drawn on the map, and the
# GHSL person-per-cell grid the hub catchment sums over.
RASTERS = DATA / "rasters"
OUTPUTS = PROJECT_ROOT / "outputs"

# Greek Grid. Source data uses this; distances and simplification
# tolerances are therefore in metres.
SOURCE_CRS = 2100

# WGS84, required by Leaflet / MapLibre
WEB_CRS = 4326

MAP_CENTER = (40.6401, 22.9444)
DEFAULT_ZOOM = 10

# Panning limit in EPSG:4326. The study area itself is
#   W 22.4893  S 40.3491  E 23.7651  N 41.0060
# but the box is padded ~1° so that MIN_ZOOM stays reachable: MapLibre
# refuses to zoom out past the point where maxBounds stops filling the
# viewport, so a tight box makes the zoom floor depend on window width.
MAP_BOUNDS = (21.49, 39.85, 24.77, 41.51)

# Zoom floor. The study area fills a normal window at 9; below that there
# is nothing to see but ocean and Bulgaria.
MIN_ZOOM = 9
MAX_ZOOM = 19

BASEMAP_TILES = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
BASEMAP_ATTRIBUTION = "© OpenStreetMap contributors © CARTO"
BASEMAP_NAME = "CartoDB Positron No Labels"

MAP_FILENAME = "urban_metropolitan_regional_interactive.html"


def raw_path(name):
    """Path to a source GeoPackage, e.g. raw_path("trees")."""
    return RAW / f"{name}.gpkg"


def processed_path(name):
    """Path to a web-ready layer, e.g. processed_path("trees")."""
    return PROCESSED / f"{name}_web_4326.gpkg"
