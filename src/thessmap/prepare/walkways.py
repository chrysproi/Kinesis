"""The pedestrian network as a display layer."""

import geopandas as gpd
import pandas as pd

from .. import config
from .geometry import valid_geometries

LINE_TYPES = ["LineString", "MultiLineString"]
WALK_CLASSES = {
    "walk_pedestrian": "Pedestrian street",
    "walk_footway": "Footway",
    "walk_path": "Path",
    "walk_hiking": "Hiking route",
}

SIMPLIFY = 3
WALK_COLUMNS = ["walk_class"]


def prepare_walkways(boundary, raw=None, processed=None, verbose=True):
    """Merge every walkable source into one clipped, simplified layer."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    layers = []

    for source, label in WALK_CLASSES.items():
        gdf = gpd.read_file(raw / f"{source}.gpkg")[["geometry"]]

        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=config.SOURCE_CRS)
        if gdf.crs != boundary.crs:
            gdf = gdf.to_crs(boundary.crs)

        gdf = valid_geometries(gdf, LINE_TYPES)
        gdf["walk_class"] = label
        layers.append(gdf)

        if verbose:
            print(f"  {source:<22} {len(gdf):>6} segments")

    merged = gpd.GeoDataFrame(
        pd.concat(layers, ignore_index=True), crs=boundary.crs
    )

    clipped = gpd.clip(merged, boundary).copy()
    clipped["geometry"] = clipped.geometry.simplify(SIMPLIFY)
    clipped = valid_geometries(clipped, LINE_TYPES)

    web = clipped[WALK_COLUMNS + ["geometry"]].to_crs(epsg=config.WEB_CRS)

    path = processed / "walkways_web_4326.gpkg"
    path.parent.mkdir(parents=True, exist_ok=True)
    web.to_file(path, layer="walkways_web_4326", driver="GPKG")

    if verbose:
        counts = web.walk_class.value_counts().to_dict()
        print(f"  saved {len(web)} features -> {path.name}  {counts}")

    return web
