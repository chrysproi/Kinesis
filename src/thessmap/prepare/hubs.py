"""The candidate mobility hub network.

222 sites scored and classified into three tiers by HUB_TYPE. The tiers
are a hierarchy, not three unrelated kinds of thing — 8 connection hubs
sit on 0.95 median public-transport access, 44 neighbourhood hubs on
0.25, and 170 street-scale hubs on 0.17 — so the map draws them at three
sizes and brings them on at three zooms rather than dropping 222 equal
marks on the city at once.

Every site is an existing open space: 187 car parks, 30 squares and 5
pedestrian areas. That is what SP_TYPE records, and it is the practical
question behind a hub — what is there now that could become one.
"""

import geopandas as gpd

from .. import config
from .geometry import keep_columns, valid_geometries

# HUB_TYPE -> (English label, the Greek term it was defined as)
HUB_TIERS = {
    "CONNECTION": ("Connection hub", "Τοπικός κόμβος σύνδεσης"),
    "NEIGHBORHOOD": ("Neighbourhood hub", "Γειτονιακός / κοινοτικός κόμβος"),
    "STREET": ("Street-scale hub", "Μικροκόμβος / κόμβος κλίμακας οδού"),
}

# What the site is today
SPACE_TYPES = {
    "PARKING": "Car park",
    "SQUARE": "Square",
    "PEDESTRIAN_AREA": "Pedestrian area",
}

COLUMNS = ["hub_tier", "hub_tier_el", "hub_space", "hub_selected"]

# The one site carried forward from the first pass, in the triangle the
# cycling network encloses west of Nea Elvetia. It turned out to be in
# this network already — 3 m away, classified as a connection hub — so
# it is flagged here rather than declared separately, and it is the only
# hub that keeps the Kinesis mark. The rest are candidates, and 222
# logos would have said they were all decided.
SELECTED_HUB = (22.93420, 40.64057)
SELECTED_TOLERANCE = 30      # metres
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

    # Scores arrive as strings from the source
    for column in ("AREA_M2", "PT_ACCESS_SCORE", "BUS_ACCESS_SCORE",
                   "METRO_ACCESS_SCORE"):
        if column in gdf.columns:
            gdf[column] = gdf[column].astype(float).round(3)

    # Flag the selected site: nearest feature within tolerance, so a
    # re-export cannot quietly promote a different hub.
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
