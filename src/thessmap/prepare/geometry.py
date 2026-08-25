"""Geometry transforms shared by the preparation pipeline."""

import geopandas as gpd


def valid_geometries(gdf, geom_types=None):
    """Drop null/empty geometries, optionally keeping only some types."""

    keep = gdf.geometry.notna() & ~gdf.geometry.is_empty

    if geom_types is not None:
        keep &= gdf.geom_type.isin(geom_types)

    return gdf[keep].copy()


def to_symbol_points(gdf):
    """Reduce mixed geometry to one representative point per feature."""

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
    """Keep one point wherever several fall within `min_distance`."""

    gdf = gdf.copy().reset_index(drop=True)

    if protect_column is not None:
        protect = gdf[protect_column] == protect_value
        protected = gdf[protect]
        candidates = gdf[~protect]
    else:
        protected = gdf.iloc[0:0]
        candidates = gdf

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
    """Narrow to `required` plus whichever `optional` columns exist."""

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
