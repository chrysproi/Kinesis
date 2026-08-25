"""Running the whole preparation pipeline."""

import time

from .. import config
from ..data import MapData
from .amenities import prepare_culture, prepare_education
from .buildings import prepare_buildings_height
from .destinations import (prepare_commercial, prepare_health,
                           prepare_public_services, prepare_sport)
from .pipeline import prepare_web_layer
from .sources import ALL_NAMES, SIMPLE, SIMPLE_BY_NAME
from .special import (prepare_bus_stops, prepare_parking_points,
                      prepare_taxi_spots, prepare_trees)
from .hubs import prepare_hub_network
from .openspaces import prepare_open_spaces
from .walkways import prepare_walkways
from .water import prepare_water

SPECIAL_FUNCTIONS = {
    "bus_stops": prepare_bus_stops,
    "parking_points": prepare_parking_points,
    "taxi_spots": prepare_taxi_spots,
    "trees": prepare_trees,
    "education": prepare_education,
    "culture": prepare_culture,
    "health": prepare_health,
    "sport": prepare_sport,
    "public_services": prepare_public_services,
    "commercial": prepare_commercial,
    "walkways": prepare_walkways,
    "water": prepare_water,
    "open_spaces": prepare_open_spaces,
    "hub_network": prepare_hub_network,
    "buildings_height": prepare_buildings_height,
}


def prepare_all(only=None, raw=None, processed=None, verbose=True):
    """Build every web-ready layer from source."""

    if only is not None:
        unknown = set(only) - set(ALL_NAMES)
        if unknown:
            raise ValueError(
                f"Unknown layers: {sorted(unknown)}. "
                f"Available: {', '.join(ALL_NAMES)}"
            )

    raw = raw or config.RAW
    processed = processed or config.PROCESSED
    processed.mkdir(parents=True, exist_ok=True)

    boundary = MapData(raw=raw).study_boundary

    if verbose:
        print(f"Study boundary ready ({boundary.crs})")
        print(f"Source:      {raw}")
        print(f"Destination: {processed}\n")

    timings = {}

    for name in ALL_NAMES:
        if only is not None and name not in only:
            continue

        if verbose:
            print(f"{name}")

        started = time.perf_counter()

        if name in SPECIAL_FUNCTIONS:
            SPECIAL_FUNCTIONS[name](
                boundary, raw=raw, processed=processed, verbose=verbose
            )
        else:
            source = SIMPLE_BY_NAME[name]
            prepare_web_layer(
                input_path=raw / f"{source.source}.gpkg",
                output_path=processed / f"{source.name}_web_4326.gpkg",
                boundary=boundary,
                simplify_tolerance=source.simplify,
                columns=source.columns,
                optional_columns=source.optional_columns,
                geom_types=list(source.geom_types) if source.geom_types else None,
                explode=source.explode,
                clip=source.clip,
                thin_distance=source.thin_distance,
                verbose=verbose,
            )

        timings[name] = time.perf_counter() - started

        if verbose:
            print(f"  {timings[name]:.1f}s\n")

    return timings
