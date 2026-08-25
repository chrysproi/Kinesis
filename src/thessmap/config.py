"""Project paths and constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA = PROJECT_ROOT / "data"
RAW = DATA
PROCESSED = DATA / "processed"
ICONS = DATA / "icons"
TILES = DATA / "tiles"
RASTERS = DATA / "rasters"
OUTPUTS = PROJECT_ROOT / "outputs"
SOURCE_CRS = 2100
WEB_CRS = 4326
MAP_CENTER = (40.6401, 22.9444)
DEFAULT_ZOOM = 10
MAP_BOUNDS = (21.49, 39.85, 24.77, 41.51)
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
