"""Assembling the whole map."""

from .render.builder import MapBuilder
from .render.layers import amenities, bike, bus, environment, ferry, metro, parking, zones

STEPS = [
    ("zones", zones.add),
    ("lakes", environment.add_lakes),
    ("hover", zones.add_hover_layer),
    ("water", environment.add_water),
    ("buildings", environment.add_buildings),
    ("bus_lanes", bus.add_lanes),
    ("bike", bike.add),
    ("bus_stops", bus.add_stops),
    ("metro_line", metro.add_line),
    ("metro_stations", metro.add_stations),
    ("ferry_routes", ferry.add_routes),
    ("ferry_terminals", ferry.add_terminals),
    ("parking", parking.add_parking),
    ("taxi", parking.add_taxi),
    ("trees", environment.add_trees),
    ("education", amenities.add_education),
    ("culture", amenities.add_culture),
]

STEP_NAMES = [name for name, _ in STEPS]


def build_map(only=None, data=None, verbose=True, center=None, zoom=None,
              show_all=False):
    """Build the map and return the MapBuilder."""

    if only is not None:
        unknown = set(only) - set(STEP_NAMES)
        if unknown:
            raise ValueError(
                f"Unknown layers: {sorted(unknown)}. "
                f"Available: {', '.join(STEP_NAMES)}"
            )

    builder = MapBuilder(data=data, center=center, zoom=zoom, show_all=show_all)

    for name, add_layer in STEPS:
        if only is not None and name not in only and name != "hover":
            continue

        if verbose:
            print(f"  adding {name}")

        add_layer(builder)

    builder.finish()

    return builder
