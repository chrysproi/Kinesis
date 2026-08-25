"""Layers that derive columns or merge several sources."""

import geopandas as gpd

from .. import config
from .classify import (classify_service_level, classify_stop_rank,
                       classify_stop_type, classify_tree_value, count_lines)
from .geometry import keep_columns, merge, to_symbol_points, valid_geometries

BUS_STOP_COLUMNS = ["code", "onomastasi", "type", "dimoskal", "lines_ejyp",
                    "stop_type_cat", "type_rank", "line_count", "service_level"]

PARKING_POINT_COLUMNS = ["amenity"]
PARKING_POINT_OPTIONAL = ("name", "name:el", "operator", "capacity", "fee",
                          "access", "parking", "surface")

TREE_VALUE_FIELD = "mo_rd"
TREE_COLUMNS = ["tree_value", "tree_class"]


def _save(gdf, processed, name, verbose=True):
    path = processed / f"{name}_web_4326.gpkg"
    path.parent.mkdir(parents=True, exist_ok=True)

    web = gdf.to_crs(epsg=config.WEB_CRS)
    web.to_file(path, driver="GPKG")

    if verbose:
        print(f"  saved {len(web)} features -> {path.name}")

    return web


def prepare_bus_stops(boundary, raw=None, processed=None, verbose=True):
    """Derives the fields the map's service-intensity symbology depends on."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    stops = gpd.read_file(raw / "bus_stops_clean.gpkg")
    stops = stops.explode(index_parts=False).reset_index(drop=True)

    if stops.crs != boundary.crs:
        stops = stops.to_crs(boundary.crs)

    stops = gpd.clip(stops, boundary).copy()

    stops["stop_type_cat"] = stops["type"].apply(classify_stop_type)
    stops["type_rank"] = stops["stop_type_cat"].apply(classify_stop_rank)
    stops["line_count"] = stops["lines_ejyp"].apply(count_lines)
    stops["service_level"] = stops["line_count"].apply(classify_service_level)

    if verbose:
        print(f"  {len(stops)} stops, service levels: "
              f"{stops['service_level'].value_counts().to_dict()}")

    stops = keep_columns(stops, BUS_STOP_COLUMNS)

    return _save(stops, processed, "bus_stops", verbose)


def prepare_taxi_spots(boundary, raw=None, processed=None, verbose=True):
    """Two source files merged."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    layers = []

    for source in ("taxi_spots_1", "taxi_spots_2"):
        gdf = gpd.read_file(raw / f"{source}.gpkg")
        gdf["source_layer"] = source

        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=config.SOURCE_CRS)

        if gdf.crs != boundary.crs:
            gdf = gdf.to_crs(boundary.crs)

        gdf = gdf.explode(index_parts=False).reset_index(drop=True)
        gdf = to_symbol_points(gdf)

        if verbose:
            print(f"  {source}: {len(gdf)} points")

        layers.append(gdf)

    spots = merge(layers, boundary.crs)
    spots = gpd.clip(spots, boundary).copy()

    return _save(spots, processed, "taxi_spots", verbose)


def prepare_trees(boundary, raw=None, processed=None, verbose=True):
    """Classifies trees into height bands."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    trees = gpd.read_file(raw / "trees.gpkg")

    if trees.crs is None:
        trees = trees.set_crs(epsg=config.SOURCE_CRS)

    trees = trees.explode(index_parts=False).reset_index(drop=True)

    if trees.crs != boundary.crs:
        trees = trees.to_crs(boundary.crs)

    trees = valid_geometries(trees, ["Point"])
    trees = gpd.clip(trees, boundary).copy()

    trees["tree_value"] = trees[TREE_VALUE_FIELD]
    trees["tree_class"] = trees["tree_value"].apply(classify_tree_value)

    if verbose:
        print(f"  {len(trees)} trees, classes: "
              f"{trees['tree_class'].value_counts().to_dict()}")

    trees = keep_columns(trees, TREE_COLUMNS)

    return _save(trees, processed, "trees", verbose)


def prepare_parking_points(boundary, raw=None, processed=None, verbose=True):
    """One point per parking place, for the hint dot and the P symbol."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    polygons = gpd.read_file(processed / "parking_places_web_4326.gpkg")
    points = to_symbol_points(polygons.to_crs(boundary.crs))

    points = keep_columns(points, PARKING_POINT_COLUMNS, PARKING_POINT_OPTIONAL)

    if verbose:
        print(f"  {len(points)} points from {len(polygons)} parking polygons")

    return _save(points, processed, "parking_points", verbose)
