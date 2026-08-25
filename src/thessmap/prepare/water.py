"""Rivers, water bodies and hydraulic structures."""

import geopandas as gpd
import pandas as pd

from .. import config
from .geometry import keep_columns, valid_geometries

LINE_TYPES = ["LineString", "MultiLineString"]
POLYGON_TYPES = ["Polygon", "MultiPolygon"]
SIMPLIFY = 5
LINE_COLUMNS = ["waterway"]
POLYGON_COLUMNS = ["fclass"]
POINT_COLUMNS = ["waterway"]
OPTIONAL = ("name", "name:el", "name:en")
DROP_NATURAL = {"coastline"}
UNCLIPPED_WATERWAYS = {"river", "canal"}


def _osm_key(value):
    """A bare OSM id, from either `osm_id` or the `way/123` form."""
    if value is None:
        return None
    return str(value).split("/")[-1].strip() or None


def _load(path, boundary):
    gdf = gpd.read_file(path)

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=config.SOURCE_CRS)
    if gdf.crs != boundary.crs:
        gdf = gdf.to_crs(boundary.crs)

    return gdf.explode(index_parts=False).reset_index(drop=True)


def prepare_water(boundary, raw=None, processed=None, verbose=True):
    """Merge the three water sources into lines, bodies and structures."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    lines = _load(raw / "water_lines.gpkg", boundary)
    lines["osm_key"] = lines.get("osm_id", pd.Series(dtype=str)).map(_osm_key)

    polygons = _load(raw / "water_polygons.gpkg", boundary)
    polygons["osm_key"] = polygons.get("osm_id", pd.Series(dtype=str)).map(_osm_key)

    extra = _load(raw / "water.gpkg", boundary)
    extra["osm_key"] = extra["id"].map(_osm_key)

    if "natural" in extra.columns:
        before = len(extra)
        extra = extra[~extra["natural"].isin(DROP_NATURAL)].copy()
        if verbose:
            print(f"  dropped {before - len(extra)} coastline segments "
                  "(the basemap draws the shore)")

    known = set(lines["osm_key"].dropna()) | set(polygons["osm_key"].dropna())
    fresh = extra[~extra["osm_key"].isin(known)].copy()

    if verbose:
        print(f"  water.gpkg: {len(extra)} features, "
              f"{len(extra) - len(fresh)} already present, {len(fresh)} new")

    results = {}

    fresh_lines = valid_geometries(fresh, LINE_TYPES)
    merged_lines = pd.concat([
        keep_columns(lines, LINE_COLUMNS, OPTIONAL),
        keep_columns(fresh_lines, LINE_COLUMNS, OPTIONAL),
    ], ignore_index=True)

    is_major = merged_lines["waterway"].isin(UNCLIPPED_WATERWAYS)

    major = _prepare(merged_lines[is_major], boundary, clip=False)
    minor = _prepare(merged_lines[~is_major], boundary, clip=True)

    if verbose:
        print(f"  rivers & canals: {len(major)} features, "
              f"{major.to_crs(config.SOURCE_CRS).length.sum() / 1000:.0f} km "
              "(not clipped)")
        print(f"  minor waterways: {len(minor)} features, "
              f"{minor.to_crs(config.SOURCE_CRS).length.sum() / 1000:.0f} km "
              "(clipped)")

    results["water_lines"] = _save(
        pd.concat([major, minor], ignore_index=True), minor.crs,
        processed, "water_lines", verbose
    )

    fresh_polygons = valid_geometries(fresh, POLYGON_TYPES)
    merged_polygons = pd.concat([
        keep_columns(polygons, POLYGON_COLUMNS, OPTIONAL),
        keep_columns(fresh_polygons, POLYGON_COLUMNS, OPTIONAL),
    ], ignore_index=True)
    results["water_polygons"] = _save(
        _prepare(merged_polygons, boundary, clip=True),
        None, processed, "water_polygons", verbose
    )

    points = valid_geometries(fresh, ["Point"])
    results["water_points"] = _save(
        _prepare(keep_columns(points, POINT_COLUMNS, OPTIONAL),
                 boundary, clip=True, simplify=False),
        None, processed, "water_points", verbose,
    )

    return results


def _prepare(frame, boundary, clip=True, simplify=True):
    """Optionally clip, simplify, and reproject to the web CRS."""

    gdf = gpd.GeoDataFrame(frame, geometry="geometry", crs=boundary.crs).copy()

    if clip:
        gdf = gpd.clip(gdf, boundary).copy()

    if simplify:
        gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY)

    return gdf.to_crs(epsg=config.WEB_CRS)


def _save(frame, crs, processed, name, verbose):
    """Write a prepared frame, already in the web CRS."""

    gdf = gpd.GeoDataFrame(
        frame, geometry="geometry", crs=crs or f"EPSG:{config.WEB_CRS}"
    )

    path = processed / f"{name}_web_4326.gpkg"
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, layer=f"{name}_web_4326", driver="GPKG")

    if verbose:
        print(f"  saved {len(gdf)} features -> {path.name}")

    return gdf
