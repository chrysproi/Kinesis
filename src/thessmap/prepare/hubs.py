"""The candidate mobility hub network."""

import geopandas as gpd

from .. import config
from .geometry import keep_columns, valid_geometries

HUB_TIERS = {
    "CONNECTION": ("Connection hub", "Τοπικός κόμβος σύνδεσης"),
    "NEIGHBORHOOD": ("Neighbourhood hub", "Γειτονιακός / κοινοτικός κόμβος"),
    "STREET": ("Street-scale hub", "Μικροκόμβος / κόμβος κλίμακας οδού"),
}

SPACE_TYPES = {
    "PARKING": "Car park",
    "SQUARE": "Square",
    "PEDESTRIAN_AREA": "Pedestrian area",
}

COLUMNS = ["hub_tier", "hub_tier_el", "hub_space", "hub_selected"]
SELECTED_HUB = (22.93420, 40.64057)
SELECTED_TOLERANCE = 30
SELECTED_NAME = "Kinesis City Hub"
OPTIONAL = ("name", "AREA_M2", "PT_ACCESS_SCORE", "BUS_ACCESS_SCORE",
            "METRO_ACCESS_SCORE", "TYPE_COUNT")


def _tier(value):
    key = str(value).strip().upper()
    return HUB_TIERS.get(key, HUB_TIERS["STREET"])


def prepare_hub_network(boundary, raw=None, processed=None, verbose=True):
    """Read the scored hub network and label its three tiers."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    gdf = gpd.read_file(raw / "hub_network.gpkg")

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=config.SOURCE_CRS)
    if gdf.crs != boundary.crs:
        gdf = gdf.to_crs(boundary.crs)

    gdf = valid_geometries(gdf.explode(index_parts=False).reset_index(drop=True),
                           ["Point"])

    gdf["hub_tier"] = gdf["HUB_TYPE"].map(lambda v: _tier(v)[0])
    gdf["hub_tier_el"] = gdf["HUB_TYPE"].map(lambda v: _tier(v)[1])
    gdf["hub_space"] = gdf["SP_TYPE"].map(
        lambda v: SPACE_TYPES.get(str(v).strip().upper(), "Open space")
    )

    for column in ("AREA_M2", "PT_ACCESS_SCORE", "BUS_ACCESS_SCORE",
                   "METRO_ACCESS_SCORE"):
        if column in gdf.columns:
            gdf[column] = gdf[column].astype(float).round(3)

    import shapely

    target = gpd.GeoSeries(
        [shapely.Point(*SELECTED_HUB)], crs=f"EPSG:{config.WEB_CRS}"
    ).to_crs(gdf.crs).iloc[0]

    distance = gdf.distance(target)
    gdf["hub_selected"] = False

    if distance.min() <= SELECTED_TOLERANCE:
        chosen = distance.idxmin()
        gdf.loc[chosen, "hub_selected"] = True
        gdf.loc[chosen, "name"] = SELECTED_NAME
    elif verbose:
        print(f"  no hub within {SELECTED_TOLERANCE} m of the selected site "
              f"(nearest {distance.min():.0f} m) — none marked")

    gdf = keep_columns(gdf, COLUMNS, OPTIONAL)
    web = gdf.to_crs(epsg=config.WEB_CRS)

    path = processed / "hub_network_web_4326.gpkg"
    path.parent.mkdir(parents=True, exist_ok=True)
    web.to_file(path, layer="hub_network_web_4326", driver="GPKG")

    if verbose:
        print(f"  {web['hub_tier'].value_counts().to_dict()}")
        print(f"  sites today: {web['hub_space'].value_counts().to_dict()}")
        print(f"  saved {len(web)} features -> {path.name}")

    return web
