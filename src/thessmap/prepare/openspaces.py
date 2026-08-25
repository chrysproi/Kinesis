"""Public open space: green space, forest, playgrounds and squares."""

import geopandas as gpd
import pandas as pd

from .. import config
from .amenities import MIN_SYMBOL_DISTANCE, _finalise, _load_source
from .geometry import keep_columns, valid_geometries

POLYGON_TYPES = ["Polygon", "MultiPolygon"]
SIMPLIFY = 2
PLAYGROUND_COLUMNS = ["playground_source"]
PLAYGROUND_OPTIONAL = ("name", "name:el", "leisure", "operator", "access",
                       "opening_hours", "surface")

GREEN_COLUMNS = ["green_subtype"]
GREEN_OPTIONAL = ("name", "name:el", "leisure", "landuse", "access")
SQUARE_COLUMNS = []
SQUARE_OPTIONAL = ("name", "name:el", "place", "leisure", "amenity",
                   "landuse", "surface")

GREEN_SUBTYPES = {
    "GREEN_SPACE": "Green space",
    "RECREATIONAL_SPACE": "Recreational space",
    "PARK": "Park",
}

MERGED_GREEN = {
    "forest": "Forest",
    "playground_polygons": "Playground",
}


def _classify_green(row):
    raw = row.get("SUBCATEGORY")
    text = str(raw).strip().upper() if raw is not None else ""

    if text in GREEN_SUBTYPES:
        return GREEN_SUBTYPES[text]

    if str(row.get("leisure", "")).strip().lower() == "park":
        return GREEN_SUBTYPES["PARK"]

    return "Green space"


def prepare_open_spaces(boundary, raw=None, processed=None, verbose=True):
    """Build all four public-open-space layers."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    results = {}

    polygons = _load_source(raw / "playground_polygons.gpkg", boundary)
    polygons = valid_geometries(polygons, POLYGON_TYPES)
    polygons["playground_source"] = "polygon"
    polygons = keep_columns(polygons, PLAYGROUND_COLUMNS, PLAYGROUND_OPTIONAL)

    nodes = _load_source(raw / "playground_points.gpkg", boundary)
    nodes = valid_geometries(nodes, ["Point"])
    nodes["playground_source"] = "node"
    nodes = keep_columns(nodes, PLAYGROUND_COLUMNS, PLAYGROUND_OPTIONAL)

    symbols_from_polygons = polygons.copy()
    symbols_from_polygons["geometry"] = polygons.geometry.representative_point()
    symbols_from_polygons["symbol_origin"] = "polygon"
    nodes = nodes.assign(symbol_origin="node")

    if verbose:
        print(f"  playgrounds: {len(polygons)} areas, {len(nodes)} nodes")

    results["playground_symbols"] = _finalise(
        [symbols_from_polygons, nodes], boundary,
        processed / "playground_symbols_web_4326.gpkg",
        "playground_symbols_web_4326", thin=True,
        protect_column="symbol_origin", verbose=verbose,
    )

    green = _load_source(raw / "green_recreational.gpkg", boundary)
    green = valid_geometries(green, POLYGON_TYPES)
    green["green_subtype"] = green.apply(_classify_green, axis=1)
    parts = [keep_columns(green, GREEN_COLUMNS, GREEN_OPTIONAL)]

    for stem, subtype in MERGED_GREEN.items():
        extra = _load_source(raw / f"{stem}.gpkg", boundary)
        extra = valid_geometries(extra, POLYGON_TYPES)
        extra["green_subtype"] = subtype
        parts.append(keep_columns(extra, GREEN_COLUMNS, GREEN_OPTIONAL))
        if verbose:
            print(f"  merged {len(extra)} {subtype.lower()} polygons")

    merged = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), crs=boundary.crs
    )

    if verbose:
        print(f"  green layer: {merged['green_subtype'].value_counts().to_dict()}")

    results["green_spaces"] = _finalise(
        [merged], boundary,
        processed / "green_spaces_web_4326.gpkg",
        "green_spaces_web_4326", verbose=verbose,
    )

    squares = _load_source(raw / "squares.gpkg", boundary)
    squares = valid_geometries(squares, POLYGON_TYPES)

    if verbose:
        named = squares["name"].notna().sum() if "name" in squares else 0
        print(f"  squares: {len(squares)}, {named} named")

    results["squares"] = _finalise(
        [keep_columns(squares, SQUARE_COLUMNS, SQUARE_OPTIONAL)], boundary,
        processed / "squares_web_4326.gpkg",
        "squares_web_4326", verbose=verbose,
    )

    return results
