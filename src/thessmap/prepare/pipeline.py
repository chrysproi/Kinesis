"""One pipeline for turning a source layer into a web-ready one.

The original notebook defined `prepare_web_layer` and then bypassed it
seven times, hand-rolling the same nine steps for metro, ferry, parking,
taxi and trees. Those variants differed in only three ways, which are now
the three optional arguments below:

    set_crs_if_missing   some sources carry no CRS
    explode              some arrive as multipart geometry
    geom_types           some need filtering to one geometry family
"""

import geopandas as gpd

from .. import config
from .geometry import keep_columns, thin_close_points, valid_geometries


def prepare_web_layer(
    input_path,
    output_path,
    boundary,
    simplify_tolerance=2,
    columns=None,
    optional_columns=(),
    geom_types=None,
    explode=False,
    set_crs_if_missing=True,
    clip=True,
    thin_distance=0,
    verbose=True,
):
    """
    Clip, simplify and reproject a layer for web display.

    Args:
        input_path: source GeoPackage.
        output_path: destination GeoPackage.
        boundary: study boundary to clip against, in the source CRS.
        simplify_tolerance: metres. 0 disables simplification.
        columns: "all" keeps everything, a list keeps those plus geometry,
            None keeps geometry only.
        optional_columns: kept when present, ignored when absent.
        geom_types: e.g. ["Point"] to drop anything else.
        explode: split multipart geometry into single parts first.
        set_crs_if_missing: assume EPSG:2100 when the source has no CRS.
        clip: set False for layers already inside the study area.
        thin_distance: metres. Collapses points describing one place, e.g.
            a harbour listed once per berth.

    Returns:
        The saved GeoDataFrame, in EPSG:4326.
    """

    def log(*args):
        if verbose:
            print(*args)

    layer = gpd.read_file(input_path)
    log(f"  read {len(layer)} features, CRS {layer.crs}")

    if layer.crs is None and set_crs_if_missing:
        layer = layer.set_crs(epsg=config.SOURCE_CRS)
        log(f"  CRS was missing, assumed EPSG:{config.SOURCE_CRS}")

    if explode:
        layer = layer.explode(index_parts=False).reset_index(drop=True)
        log(f"  exploded to {len(layer)} single-part features")

    if layer.crs != boundary.crs:
        layer = layer.to_crs(boundary.crs)

    if geom_types is not None:
        layer = valid_geometries(layer, geom_types)
        log(f"  kept {len(layer)} features of type {'/'.join(geom_types)}")

    if clip:
        layer = gpd.clip(layer, boundary).copy()
        log(f"  clipped to {len(layer)} features")

    if thin_distance:
        before = len(layer)
        layer = thin_close_points(layer, min_distance=thin_distance)
        log(f"  thinned {before} -> {len(layer)} (min {thin_distance} m apart)")

    if columns == "all":
        pass
    elif columns is not None:
        layer = keep_columns(layer, columns, optional_columns)
    else:
        layer = layer[["geometry"]].copy()

    if simplify_tolerance:
        # Tolerance is in metres because we are still in the source CRS
        layer["geometry"] = layer.geometry.simplify(
            tolerance=simplify_tolerance, preserve_topology=True
        )

    layer_web = layer.to_crs(epsg=config.WEB_CRS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    layer_web.to_file(output_path, driver="GPKG")

    log(f"  saved {len(layer_web)} features -> {output_path.name}")

    return layer_web
