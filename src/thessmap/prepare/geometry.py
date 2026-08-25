"""Geometry transforms shared by the preparation pipeline."""

import geopandas as gpd


def valid_geometries(gdf, geom_types=None):
    """Drop null/empty geometries, optionally keeping only some types."""

    keep = gdf.geometry.notna() & ~gdf.geometry.is_empty

    if geom_types is not None:
        keep &= gdf.geom_type.isin(geom_types)

    return gdf[keep].copy()


def to_symbol_points(gdf):
    """
    Reduce mixed geometry to one representative point per feature.

    Point            -> unchanged
    Polygon          -> representative_point(), guaranteed inside
    LineString       -> midpoint

    Used for education and culture, where a school may arrive as a
    building footprint from one source and a node from another, but the
    map needs a single symbol either way.
    """

    gdf = valid_geometries(gdf)

    points = []

    for geom in gdf.geometry:
        if geom.geom_type == "Point":
            points.append(geom)
        elif geom.geom_type in ("Polygon", "MultiPolygon"):
            points.append(geom.representative_point())
        elif geom.geom_type in ("LineString", "MultiLineString"):
            points.append(geom.interpolate(0.5, normalized=True))
        else:
            points.append(None)

    gdf["geometry"] = points

    return valid_geometries(gdf, ["Point"])


def thin_close_points(gdf, min_distance, protect_column=None, protect_value=None):
    """
    Keep one point wherever several fall within `min_distance`.

    `protect_column`/`protect_value` mark points that are always kept and
    that thin the others around them — used so polygon-derived culture
    symbols survive while dense node symbols get thinned.

    Distance is in CRS units, so run this before reprojecting to 4326
    while still in metres.
    """

    gdf = gdf.copy().reset_index(drop=True)

    if protect_column is not None:
        # Built after reset_index, so the mask shares the frame's index
        protect = gdf[protect_column] == protect_value
        protected = gdf[protect]
        candidates = gdf[~protect]
    else:
        protected = gdf.iloc[0:0]
        candidates = gdf

    # Protected points still have to be thinned against *each other*.
    # Overlapping sources describe the same landmark more than once — the
    # White Tower appeared twice at the identical coordinate — and keeping
    # every protected point stacks those symbols permanently.
    kept_geometries = []
    kept_indices = []

    for index, row in protected.iterrows():
        point = row.geometry

        if point is None or point.is_empty:
            continue

        if any(point.distance(other) < min_distance for other in kept_geometries):
            continue

        kept_indices.append(index)
        kept_geometries.append(point)

    for index, row in candidates.iterrows():
        point = row.geometry

        if point is None or point.is_empty:
            continue

        if any(point.distance(other) < min_distance for other in kept_geometries):
            continue

        kept_indices.append(index)
        kept_geometries.append(point)

    return gdf.loc[sorted(kept_indices)].copy().reset_index(drop=True)


def keep_columns(gdf, required, optional=()):
    """
    Narrow to `required` plus whichever `optional` columns exist.

    Geometry is always last, matching how the source notebooks wrote it.
    """

    columns = [c for c in required if c in gdf.columns and c != "geometry"]

    for column in optional:
        if column in gdf.columns and column not in columns:
            columns.append(column)

    return gdf[columns + ["geometry"]].copy()


def merge(layers, crs):
    """Concatenate several GeoDataFrames into one."""

    import pandas as pd

    merged = pd.concat(layers, ignore_index=True)

    return gpd.GeoDataFrame(merged, geometry="geometry", crs=crs)
