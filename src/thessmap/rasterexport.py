"""Turning a population raster into something MapLibre can draw."""

import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rasterio.warp import transform_bounds

from . import config, palette

TARGET_CRS = "EPSG:3857"


def _read_mercator(path):
    """Reproject a raster to Web Mercator, keeping nodata masked."""

    with rasterio.open(path) as source:
        transform, width, height = calculate_default_transform(
            source.crs, TARGET_CRS, source.width, source.height, *source.bounds
        )

        destination = np.full((height, width), np.nan, dtype="float32")

        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=source.nodata,
            dst_transform=transform,
            dst_crs=TARGET_CRS,
            dst_nodata=np.nan,
            resampling=Resampling.nearest,
        )

        bounds = rasterio.transform.array_bounds(height, width, transform)

    return destination, bounds


def placement(path):
    """Where a raster's PNG sits on the map, without rendering it."""

    with rasterio.open(path) as source:
        transform, width, height = calculate_default_transform(
            source.crs, TARGET_CRS, source.width, source.height, *source.bounds
        )
        bounds = rasterio.transform.array_bounds(height, width, transform)

    west, south, east, north = transform_bounds(TARGET_CRS, "EPSG:4326", *bounds)

    return [
        [west, north],
        [east, north],
        [east, south],
        [west, south],
    ]


def _class_colours(breaks):
    """RGBA per class, from the choropleth ramp plus the raster's own alpha."""

    if len(breaks) != len(palette.POP_DENSITY_RAMP):
        raise ValueError(
            f"{len(breaks)} breaks against {len(palette.POP_DENSITY_RAMP)} "
            "ramp colours — the two must agree"
        )

    colours = []
    for colour, alpha in zip(palette.POP_DENSITY_RAMP, palette.POP_RASTER_ALPHA):
        red, green, blue = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
        colours.append((red, green, blue, alpha))

    return colours


def _classify(values, breaks):
    """Class index per cell, -1 where there is no data."""

    interior = breaks[:-1]

    index = np.digitize(np.nan_to_num(values, nan=-1.0), interior, right=True)
    index[~np.isfinite(values)] = -1

    return index


def _colourise(index, colours):
    """Paint each class, leaving nodata fully transparent."""

    height, width = index.shape
    rgba = np.zeros((height, width, 4), dtype="uint8")

    for position, colour in enumerate(colours):
        rgba[index == position] = colour

    return rgba


def export_population_raster(source_path, destination, breaks, verbose=True):
    """Write the coloured PNG and return what the frontend needs to place it."""

    values, _bounds = _read_mercator(source_path)

    colours = _class_colours(breaks)
    index = _classify(values, breaks)
    rgba = _colourise(index, colours)

    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(destination, optimize=True)

    if verbose:
        height, width = index.shape
        counted = [int((index == position).sum()) for position in range(len(colours))]
        print(f"  {destination.name:<22} {width}x{height}  "
              f"{destination.stat().st_size / 1e6:.2f} MB")
        print(f"    cells per class: {counted}  nodata {int((index == -1).sum())}")

    return {
        "url": destination.name,
        "coordinates": placement(source_path),
    }


def hub_catchment(point, radius_m, raster_path=None):
    """Residents living within `radius_m` of a point."""

    from pyproj import Transformer

    path = raster_path or config.RASTERS / "ghs_pop_2020.tif"

    with rasterio.open(path) as source:
        to_raster = Transformer.from_crs(
            "EPSG:4326", source.crs, always_xy=True
        )
        centre_x, centre_y = to_raster.transform(*point)

        window = rasterio.windows.from_bounds(
            centre_x - radius_m, centre_y - radius_m,
            centre_x + radius_m, centre_y + radius_m,
            transform=source.transform,
        )

        values = source.read(1, window=window, boundless=True, fill_value=0)
        transform = source.window_transform(window)
        nodata = source.nodata

    rows, columns = np.indices(values.shape)
    xs, ys = rasterio.transform.xy(transform, rows, columns)
    xs = np.reshape(xs, values.shape)
    ys = np.reshape(ys, values.shape)

    inside = (xs - centre_x) ** 2 + (ys - centre_y) ** 2 <= radius_m ** 2

    if nodata is not None:
        inside &= values != nodata

    inside &= np.isfinite(values)

    return {
        "population": int(round(float(values[inside].sum()))),
        "cells": int(inside.sum()),
        "radius_m": radius_m,
    }
