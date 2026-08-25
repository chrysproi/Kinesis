"""Buildings, classified by roof height."""

import geopandas as gpd

from .. import config
from .geometry import keep_columns, valid_geometries

POLYGON_TYPES = ["Polygon", "MultiPolygon"]
SIMPLIFY = 0.5
COLUMNS = ["ROOF_H"]
OPTIONAL = ("MAX_FLOOR", "NO_APPART")
MIN_HEIGHT = 0.0


def prepare_buildings_height(boundary, raw=None, processed=None, verbose=True):
    """Clip the national building dataset to the study area."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    gdf = gpd.read_file(
        raw / "buildingsheight.gpkg",
        bbox=tuple(boundary.total_bounds),
        columns=COLUMNS + list(OPTIONAL),
    )

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=config.SOURCE_CRS)
    if gdf.crs != boundary.crs:
        gdf = gdf.to_crs(boundary.crs)

    if verbose:
        print(f"  read {len(gdf):,} features within the study bbox")

    gdf = valid_geometries(gdf, POLYGON_TYPES)
    gdf = gpd.clip(gdf, boundary).copy()

    before = len(gdf)
    gdf = gdf[gdf["ROOF_H"] > MIN_HEIGHT].copy()

    if verbose:
        print(f"  clipped to {before:,}, dropped {before - len(gdf)} with "
              f"roof height <= {MIN_HEIGHT:.0f} m")

    gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY)
    gdf = keep_columns(gdf, COLUMNS, OPTIONAL)

    web = gdf.to_crs(epsg=config.WEB_CRS)

    path = processed / "buildings_height_web_4326.gpkg"
    path.parent.mkdir(parents=True, exist_ok=True)
    web.to_file(path, layer="buildings_height_web_4326", driver="GPKG")

    if verbose:
        print(f"  saved {len(web):,} features -> {path.name}")

    return web
