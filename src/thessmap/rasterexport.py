"""Turning a population raster into something MapLibre can draw.

MapLibre reads no GeoTIFF, so the 100 m grid is reprojected to Web
Mercator, colourised here, and shipped as one RGBA PNG added through an
`image` source. Because the PNG is already in EPSG:3857 the four corner
coordinates map it exactly — no resampling in the browser and no tile
pyramid for a grid this small.

The alternative, raster tiles, buys nothing: the whole grid is 1097x733
cells over a single region.
"""

import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rasterio.warp import transform_bounds

from . import config, palette

# MapLibre renders image sources in Web Mercator
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
            # Bilinear would invent density between a populated cell and
            # an empty one. Nearest keeps every pixel a measured value.
            resampling=Resampling.nearest,
        )

        bounds = rasterio.transform.array_bounds(height, width, transform)

    return destination, bounds


def placement(path):
    """
    Where a raster's PNG sits on the map, without rendering it.

    Only the reprojected grid's extent is needed, so this reads the
    header rather than the pixels. Keeps the TypeScript emission
    independent of whether the PNG has been written yet.

    Returns:
        The four corners in EPSG:4326, clockwise from top-left.
    """

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
    """
    RGBA per class, from the choropleth ramp plus the raster's own alpha.

    Sharing the ramp is deliberate: the grid and the municipal fill answer
    the same question at two resolutions, so a cell darker than the
    municipality it sits in is denser than that municipality's average.
    """

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
    """
    Class index per cell, -1 where there is no data.

    `breaks` are upper bounds, so the interior ones are the cut points;
    the last is the data maximum and would put nothing above it.
    """

    interior = breaks[:-1]

    # digitize on a NaN returns len(bins), so mask afterwards rather than
    # trusting the index
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
    """
    Write the coloured PNG and return what the frontend needs to place it.

    Args:
        source_path: the density GeoTIFF, in whatever CRS it arrives in.
        destination: PNG path.
        breaks: class upper bounds, from `classify.breaks`. Passed in
            rather than computed here so the grid and the choropleth can
            never fall onto different scales.

    Returns:
        {"url", "coordinates"} — coordinates being the four corners in
        EPSG:4326, clockwise from top-left, as MapLibre's image source
        expects.
    """

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
        # Clockwise from top-left, per the MapLibre image source spec
        "coordinates": placement(source_path),
    }


# --------------------------------------------------
# Hub catchment
# --------------------------------------------------


def hub_catchment(point, radius_m, raster_path=None):
    """
    Residents living within `radius_m` of a point.

    The GHSL grid holds persons per 100 m cell, so a catchment is the sum
    of the cells whose centres fall inside the radius. Cells are counted
    whole: at 100 m a partial-cell correction is below the accuracy of
    the source estimate.

    Args:
        point: (lon, lat) in EPSG:4326.
        radius_m: metres. 800 is the usual 10-minute walk.
        raster_path: defaults to the GHSL population grid.

    Returns:
        {"population", "cells", "radius_m"}. Population is rounded: the
        grid is a modelled estimate, so decimals would be false
        precision.
    """

    from pyproj import Transformer

    path = raster_path or config.RASTERS / "ghs_pop_2020.tif"

    with rasterio.open(path) as source:
        # Straight-line distance has to be measured in the raster's own
        # projected CRS. Mollweide is equal-area, so a metre-radius
        # circle is very slightly distorted but the enclosed area is
        # right, which is what a population sum depends on.
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
    # transform.xy flattens whatever it is given, so reshape back
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
