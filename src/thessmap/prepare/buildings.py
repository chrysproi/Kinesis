"""Buildings, classified by roof height.

From `buildingsheight.gpkg` — the Greek national building dataset, 1.99
million footprints nationwide with surveyed heights (flight date
2025-06-12). Read with a bounding-box filter rather than in full: the
file is 921 MB and the study area holds 192,645 of it.

Not to be confused with `buildings.gpkg`, the Geofabrik OSM extract also
in data/. That one carries no height at all — only osm_id, code, fclass,
name, type — which is why the height ramp waited on this file.
"""

import geopandas as gpd

from .. import config
from .geometry import keep_columns, valid_geometries

POLYGON_TYPES = ["Polygon", "MultiPolygon"]

# Metres. Footprints are small — median 91 m2 — so this is deliberately
# fine; anything coarser starts rounding off corners at z16 where the
# layer is read one building at a time.
SIMPLIFY = 0.5

COLUMNS = ["ROOF_H"]

# Only what the popup shows. The source also carries CEIL_H, PILOTI,
# YPOGEIO, ADDRESS and the elevations, but at 192,565 features every
# column is about 3 MB of exported GeoJSON, and CEIL_H is empty on 49%
# of rows while PILOTI is empty on 93%. They stay in the GeoPackage for
# analysis and out of the web layer.
OPTIONAL = ("MAX_FLOOR", "NO_APPART")

# 80 of 192,645 footprints carry a roof height of zero or below, the
# minimum being -3.0 m. Those are survey errors, not basements, and a
# height class cannot say anything about them.
MIN_HEIGHT = 0.0


def prepare_buildings_height(boundary, raw=None, processed=None, verbose=True):
    """Clip the national building dataset to the study area."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    # bbox first, so GDAL uses the spatial index instead of scanning 1.99
    # million features
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
