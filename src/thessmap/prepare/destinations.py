"""Important destinations: health, sport, public services, commercial."""

import geopandas as gpd

from .. import config
from .amenities import MIN_SYMBOL_DISTANCE, _finalise, _load_source
from .classify import (DROP_AMENITIES, classify_commercial, classify_health,
                       classify_public_service, classify_sport)
from .geometry import keep_columns, to_symbol_points

DESTINATION_COLUMNS = ["dest_category", "dest_source"]
DESTINATION_OPTIONAL = [
    "name", "name:el", "name_el", "name:en", "name_en", "operator",
    "amenity", "healthcare", "healthca_1", "emergency", "beds",
    "office", "government", "shop", "leisure", "sport", "capacity",
    "opening_hours", "opening_ho", "website", "phone",
]


class Destination:
    """One destination layer: its sources, and how to categorise them."""

    def __init__(self, name, sources, classifier):
        self.name = name
        self.sources = sources
        self.classifier = classifier


DESTINATIONS = [
    Destination("health", ["health_points", "health_polygons"],
                classify_health),

    Destination("sport", ["sport_pitches", "sport_stadiums"],
                classify_sport),

    Destination("public_services", ["public_services"],
                classify_public_service),

    Destination("commercial", ["commercial_major"],
                classify_commercial),
]

DESTINATIONS_BY_NAME = {d.name: d for d in DESTINATIONS}


def prepare_destination(name, boundary, raw=None, processed=None, verbose=True):
    """Build one destination layer: merge its sources, categorise, thin."""

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    spec = DESTINATIONS_BY_NAME[name]
    layers = []

    for source in spec.sources:
        gdf = _load_source(raw / f"{source}.gpkg", boundary)

        if "amenity" in gdf.columns:
            before = len(gdf)
            gdf = gdf[~gdf["amenity"].isin(DROP_AMENITIES)].copy()
            if verbose and len(gdf) != before:
                print(f"  {source}: dropped {before - len(gdf)} entrance nodes")

        if not len(gdf):
            continue

        gdf["dest_category"] = gdf.apply(spec.classifier, axis=1)
        gdf["dest_source"] = source

        was_polygon = ~gdf.geom_type.isin(["Point", "MultiPoint"])
        symbols = to_symbol_points(gdf)
        symbols["symbol_origin"] = [
            "polygon" if flag else "node" for flag in was_polygon
        ]

        symbols = keep_columns(
            symbols,
            DESTINATION_COLUMNS + ["symbol_origin"],
            DESTINATION_OPTIONAL,
        )
        layers.append(symbols)

        if verbose:
            counts = symbols["dest_category"].value_counts().to_dict()
            print(f"  {source}: {len(symbols)} symbols {counts}")

    return _finalise(
        layers, boundary,
        processed / f"{name}_symbols_web_4326.gpkg",
        f"{name}_symbols_web_4326",
        thin=True, protect_column="symbol_origin", verbose=verbose,
    )


def prepare_health(boundary, **kwargs):
    return prepare_destination("health", boundary, **kwargs)


def prepare_sport(boundary, **kwargs):
    return prepare_destination("sport", boundary, **kwargs)


def prepare_public_services(boundary, **kwargs):
    return prepare_destination("public_services", boundary, **kwargs)


def prepare_commercial(boundary, **kwargs):
    return prepare_destination("commercial", boundary, **kwargs)
