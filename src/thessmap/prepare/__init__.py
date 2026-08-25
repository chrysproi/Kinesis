"""Turning source GeoPackages into web-ready layers.

`run()` is the whole pipeline; `prepare_web_layer()` is the single
function that handles every layer needing only clip/simplify/reproject.
"""

from .amenities import prepare_culture, prepare_education
from .pipeline import prepare_web_layer
from .run import prepare_all
from .sources import ALL_NAMES, SIMPLE, SIMPLE_BY_NAME
from .special import prepare_bus_stops, prepare_taxi_spots, prepare_trees

__all__ = [
    "prepare_all",
    "prepare_web_layer",
    "prepare_bus_stops",
    "prepare_taxi_spots",
    "prepare_trees",
    "prepare_education",
    "prepare_culture",
    "ALL_NAMES",
    "SIMPLE",
    "SIMPLE_BY_NAME",
]
