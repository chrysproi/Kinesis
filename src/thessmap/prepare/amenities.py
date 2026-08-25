"""Education and culture preparation.

These two are the only layers that genuinely need custom handling: both
arrive as several source files mixing polygons, lines and points, and
both need one symbol point per feature plus thinning so dense clusters
do not turn into a blob of overlapping icons.

Everything else in the project goes through `prepare_web_layer`.
"""

import geopandas as gpd

from .. import config
from .classify import classify_culture_subtype, classify_education
from .geometry import keep_columns, merge, thin_close_points, to_symbol_points, valid_geometries

# Distance below which symbols are considered duplicates. Metres, applied
# before reprojecting to 4326.
MIN_SYMBOL_DISTANCE = 35

EDUCATION_SOURCES = [f"education_{n}" for n in range(1, 10)]

CULTURE_SOURCES = {
    "culture_polygons": "Culture",
    "culture_nodes": "Culture_nodes",
    "culture_extra": "Culture_extra",
}

EDUCATION_COLUMNS = ["education_source", "education_type"]
EDUCATION_OPTIONAL = ["name", "Name", "NAME", "name_el", "name:el", "ΟΝΟΜΑΣΙΑ",
                      "onomasia", "operator", "amenity", "school:type",
                      "education", "office"]

CULTURE_COLUMNS = ["culture_type", "culture_subtype", "culture_source"]
CULTURE_OPTIONAL = ["path", "name", "Name", "NAME", "name_el", "name:el", "name_en",
                    "amenity", "tourism", "historic", "religion", "museum",
                    "theatre_ty", "library_ty", "symbol_origin"]

POLYGON_TYPES = ["Polygon", "MultiPolygon"]
LINE_TYPES = ["LineString", "MultiLineString"]


def _load_source(path, boundary):
    """Read, fix CRS, explode and drop invalid geometry."""

    gdf = gpd.read_file(path)

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=config.SOURCE_CRS)

    if gdf.crs != boundary.crs:
        gdf = gdf.to_crs(boundary.crs)

    gdf = gdf.explode(index_parts=False).reset_index(drop=True)

    return valid_geometries(gdf)


def _finalise(layers, boundary, output_path, layer_name, thin=False,
              protect_column=None, verbose=True):
    """Merge, clip, optionally thin, reproject and save."""

    if not layers:
        if verbose:
            print(f"  no features for {layer_name}, nothing written")
        return None

    merged = merge(layers, boundary.crs)
    clipped = gpd.clip(merged, boundary).copy()

    if thin:
        before = len(clipped)
        clipped = thin_close_points(
            clipped,
            min_distance=MIN_SYMBOL_DISTANCE,
            protect_column=protect_column,
            protect_value="polygon",
        )
        if verbose:
            print(f"  thinned {before} -> {len(clipped)} symbols "
                  f"(min {MIN_SYMBOL_DISTANCE} m)")

    web = clipped.to_crs(epsg=config.WEB_CRS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    web.to_file(output_path, layer=layer_name, driver="GPKG")

    if verbose:
        print(f"  saved {len(web)} features -> {output_path.name}")

    return web


def prepare_education(boundary, raw=None, processed=None, verbose=True):
    """
    Nine source files, each one education type, merged into a polygon
    layer and a thinned symbol layer.
    """

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    polygon_layers = []
    symbol_layers = []

    for source in EDUCATION_SOURCES:
        gdf = _load_source(raw / f"{source}.gpkg", boundary)

        gdf["education_source"] = source
        # From the OSM tags, not the filename: the nine files are five
        # categories split arbitrarily, and the filename leaked into the
        # popup as "Type: education_8".
        gdf["education_type"] = gdf.apply(classify_education, axis=1)

        polygons = gdf[gdf.geom_type.isin(POLYGON_TYPES)].copy()
        if len(polygons):
            polygon_layers.append(
                keep_columns(polygons, EDUCATION_COLUMNS, EDUCATION_OPTIONAL)
            )

        symbols = to_symbol_points(gdf)
        if len(symbols):
            symbol_layers.append(
                keep_columns(symbols, EDUCATION_COLUMNS, EDUCATION_OPTIONAL)
            )

        if verbose:
            print(f"  {source}: {len(polygons)} polygons, {len(symbols)} symbols")

    return {
        "education_polygons": _finalise(
            polygon_layers, boundary,
            processed / "education_polygons_web_4326.gpkg",
            "education_polygons_web_4326", verbose=verbose,
        ),
        "education_symbols": _finalise(
            symbol_layers, boundary,
            processed / "education_symbols_web_4326.gpkg",
            "education_symbols_web_4326", thin=True, verbose=verbose,
        ),
    }


def prepare_culture(boundary, raw=None, processed=None, verbose=True):
    """
    Three source files split into polygons, lines and symbols.

    Symbols come from two places — a representative point inside each
    polygon, and standalone nodes. Polygon-derived symbols are protected
    during thinning so a mapped monument never loses its icon to a
    nearby node.
    """

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    polygon_layers = []
    line_layers = []
    symbol_layers = []

    for source, filename in CULTURE_SOURCES.items():
        gdf = _load_source(raw / f"{filename}.gpkg", boundary)

        gdf["culture_type"] = "Culture"
        gdf["culture_source"] = source
        gdf["culture_subtype"] = gdf.apply(classify_culture_subtype, axis=1)

        polygons = gdf[gdf.geom_type.isin(POLYGON_TYPES)].copy()
        if len(polygons):
            polygons["symbol_origin"] = "none"
            polygons = keep_columns(polygons, CULTURE_COLUMNS, CULTURE_OPTIONAL)
            polygon_layers.append(polygons)

            # One symbol inside every polygon
            polygon_symbols = polygons.copy()
            polygon_symbols["geometry"] = polygon_symbols.geometry.representative_point()
            polygon_symbols["symbol_origin"] = "polygon"
            symbol_layers.append(polygon_symbols)

        nodes = gdf[gdf.geom_type == "Point"].copy()
        if len(nodes):
            nodes["symbol_origin"] = "node"
            symbol_layers.append(
                keep_columns(nodes, CULTURE_COLUMNS, CULTURE_OPTIONAL)
            )

        lines = gdf[gdf.geom_type.isin(LINE_TYPES)].copy()
        if len(lines):
            lines["symbol_origin"] = "none"
            line_layers.append(
                keep_columns(lines, CULTURE_COLUMNS, CULTURE_OPTIONAL)
            )

        if verbose:
            print(f"  {source}: {len(polygons)} polygons, "
                  f"{len(lines)} lines, {len(nodes)} nodes")

    return {
        "culture_polygons": _finalise(
            polygon_layers, boundary,
            processed / "culture_polygons_web_4326.gpkg",
            "culture_polygons_web_4326", verbose=verbose,
        ),
        "culture_lines": _finalise(
            line_layers, boundary,
            processed / "culture_lines_web_4326.gpkg",
            "culture_lines_web_4326", verbose=verbose,
        ),
        "culture_symbols": _finalise(
            symbol_layers, boundary,
            processed / "culture_symbols_web_4326.gpkg",
            "culture_symbols_web_4326", thin=True,
            protect_column="symbol_origin", verbose=verbose,
        ),
    }
