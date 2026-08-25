"""The layer registry: every layer on the map, declared once."""

from dataclasses import dataclass

from . import config


@dataclass(frozen=True)
class LayerSpec:
    id: str
    label: str
    theme: str
    show: bool = False
    parent: str | None = None
    min_zoom: int | None = None
    max_zoom: int | None = None
    group: str | None = None
    short: str | None = None
    pinned: bool = False
    auto_hide_above: int | None = None

    @property
    def menu_label(self):
        return self.short or self.label

    @property
    def is_detail(self):
        return self.parent is not None


GROUPS = {
    "metro": "Metro",
    "bus": "Bus",
    "bike": "Bike",
    "ferry": "Ferry",
}


THEMES = {
    "zones": "Zones",
    "environment": "Environment",
    "fabric": "Urban fabric",
    "transport": "Transport",
    "services": "Mobility services",
    "amenities": "Amenities",
    "population": "Population density",
}


LAYERS = [
    LayerSpec("zones", "Urban / Metropolitan / Regional Frame", "zones",
              show=True, auto_hide_above=config.MIN_ZOOM),


    LayerSpec("water", "Rivers & Lakes", "environment", show=True),
    LayerSpec("lakes", "Named Lakes", "environment", parent="water"),
    LayerSpec("water_major", "Rivers & Canals", "environment",
              parent="water"),
    LayerSpec("water_minor", "Streams & Drains", "environment",
              parent="water"),
    LayerSpec("water_structures", "Weirs, Dams & Waterfalls", "environment",
              parent="water", min_zoom=15),


    LayerSpec("landuse", "Land Use", "fabric", min_zoom=11),

    LayerSpec("buildings", "Buildings by Height", "fabric", min_zoom=12),

    LayerSpec("bus_lanes", "Bus Lanes", "transport",
              group="bus", short="Lanes"),

    LayerSpec("bike_lanes", "Bike Lanes", "transport", min_zoom=12,
              group="bike", short="Lanes, parking, rental"),
    LayerSpec("bike_detail", "Bike Details", "transport",
              parent="bike_lanes", min_zoom=16),
    LayerSpec("bike_rental_hint", "Bike Rental Hint", "transport",
              parent="bike_lanes", min_zoom=12, max_zoom=13),
    LayerSpec("bike_rental_symbols", "Bike Rental", "transport",
              parent="bike_lanes", min_zoom=13),
    LayerSpec("bike_points", "Bike Parking & Rental", "transport",
              parent="bike_lanes", min_zoom=14),
    LayerSpec("bike_parking_hint", "Bike Parking Hint", "transport",
              parent="bike_lanes", min_zoom=15, max_zoom=17),
    LayerSpec("bike_parking_symbols", "Bike Parking", "transport",
              parent="bike_lanes", min_zoom=17),

    LayerSpec("bike_lanes_proposed", "Proposed Bike Lanes", "transport",
              min_zoom=12, group="bike", short="Proposed"),

    LayerSpec("bus_stops", "Bus Stops", "transport",
              group="bus", short="Stops"),
    LayerSpec("bus_stops_simple", "Bus Stops Simple", "transport",
              parent="bus_stops", min_zoom=12, max_zoom=15),
    LayerSpec("bus_stops_outer", "Bus Stops Service Intensity", "transport",
              parent="bus_stops", min_zoom=14),
    LayerSpec("bus_stops_symbols", "Bus Stops Type Symbols", "transport",
              parent="bus_stops", min_zoom=15),

    LayerSpec("metro_line", "Metro Line", "transport", show=True,
              group="metro", short="Line"),
    LayerSpec("metro_line_zoomout", "Metro Line Strong", "transport",
              parent="metro_line", max_zoom=14),
    LayerSpec("metro_line_zoomin", "Metro Line Normal", "transport",
              parent="metro_line", min_zoom=14),

    LayerSpec("metro_stations", "Metro Stations", "transport", show=True,
              group="metro", short="Stations"),
    LayerSpec("metro_stations_symbols", "Metro Stations Symbols", "transport",
              parent="metro_stations", min_zoom=12),
    LayerSpec("metro_stations_small", "Metro Stations Small Symbols", "transport",
              parent="metro_stations", min_zoom=13, max_zoom=15),
    LayerSpec("metro_stations_outer", "Metro Stations Service Intensity", "transport",
              parent="metro_stations", min_zoom=15),
    LayerSpec("metro_stations_large", "Metro Stations Large Symbols", "transport",
              parent="metro_stations", min_zoom=15),

    LayerSpec("ferry_routes", "Ferry Routes", "transport", show=True,
              group="ferry", short="Routes"),
    LayerSpec("ferry_terminals", "Ferry Terminals", "transport", show=True,
              group="ferry", short="Terminals"),
    LayerSpec("ferry_terminals_symbols", "Ferry Terminals Symbols", "transport",
              parent="ferry_terminals", min_zoom=12),

    LayerSpec("walkways", "Pedestrian Network", "transport", min_zoom=13),

    LayerSpec("parking", "Parking Places", "services"),
    LayerSpec("parking_hint", "Parking Hint", "services",
              parent="parking", min_zoom=14, max_zoom=15),
    LayerSpec("parking_polygons", "Parking Places Polygons", "services",
              parent="parking", min_zoom=15),
    LayerSpec("parking_symbols", "Parking Places Symbols", "services",
              parent="parking", min_zoom=15),

    LayerSpec("mobility_hubs", "Mobility Hubs", "services", show=True),
    LayerSpec("hub_overview", "Hub Sites", "services",
              parent="mobility_hubs", min_zoom=12, max_zoom=14),
    LayerSpec("hub_connection", "Connection Hubs", "services",
              parent="mobility_hubs", min_zoom=14),
    LayerSpec("hub_neighbourhood", "Neighbourhood Hubs", "services",
              parent="mobility_hubs", min_zoom=14),
    LayerSpec("hub_street", "Street-scale Hubs", "services",
              parent="mobility_hubs", min_zoom=14),
    LayerSpec("hub_selected", "Kinesis City Hub", "services",
              parent="mobility_hubs", min_zoom=14),

    LayerSpec("taxi", "Taxi Spots", "services"),
    LayerSpec("taxi_hint", "Taxi Hint", "services",
              parent="taxi", min_zoom=14, max_zoom=15),
    LayerSpec("taxi_symbols", "Taxi Spots Symbols", "services",
              parent="taxi", min_zoom=15),

    LayerSpec("trees", "Trees", "environment"),
    LayerSpec("trees_density", "Tree Density", "environment",
              parent="trees", min_zoom=13, max_zoom=17),
    LayerSpec("trees_texture", "Tree Texture", "environment",
              parent="trees", min_zoom=16),
    LayerSpec("trees_symbols", "Trees Symbols", "environment",
              parent="trees", min_zoom=18),

    LayerSpec("education", "Education", "amenities"),
    LayerSpec("education_hint", "Education Hint", "amenities",
              parent="education", min_zoom=14, max_zoom=15),
    LayerSpec("education_polygons", "Education Polygons", "amenities",
              parent="education", min_zoom=15),
    LayerSpec("education_symbols", "Education Symbols", "amenities",
              parent="education", min_zoom=15),

    LayerSpec("culture", "Culture", "amenities"),
    LayerSpec("culture_hint", "Culture Hint", "amenities",
              parent="culture", min_zoom=14, max_zoom=15),
    LayerSpec("culture_polygons", "Culture Polygons", "amenities",
              parent="culture", min_zoom=15),
    LayerSpec("culture_lines", "Culture Lines", "amenities",
              parent="culture", min_zoom=15),
    LayerSpec("culture_symbols", "Culture Symbols", "amenities",
              parent="culture", min_zoom=15),

    LayerSpec("health", "Health", "amenities"),
    LayerSpec("health_hint", "Health Hint", "amenities",
              parent="health", min_zoom=14, max_zoom=15),
    LayerSpec("health_symbols", "Health Symbols", "amenities",
              parent="health", min_zoom=15),

    LayerSpec("sport", "Sport", "amenities"),
    LayerSpec("sport_hint", "Sport Hint", "amenities",
              parent="sport", min_zoom=14, max_zoom=15),
    LayerSpec("sport_symbols", "Sport Symbols", "amenities",
              parent="sport", min_zoom=15),

    LayerSpec("public_services", "Public Services", "amenities"),
    LayerSpec("public_services_hint", "Public Services Hint", "amenities",
              parent="public_services", min_zoom=14, max_zoom=15),
    LayerSpec("public_services_symbols", "Public Services Symbols", "amenities",
              parent="public_services", min_zoom=15),

    LayerSpec("commercial", "Commercial", "amenities"),

    LayerSpec("playgrounds", "Playgrounds", "amenities"),
    LayerSpec("playground_hint", "Playground Hint", "amenities",
              parent="playgrounds", min_zoom=14, max_zoom=15),
    LayerSpec("playground_symbols", "Playground Symbols", "amenities",
              parent="playgrounds", min_zoom=15),
    LayerSpec("commercial_hint", "Commercial Hint", "amenities",
              parent="commercial", min_zoom=14, max_zoom=15),
    LayerSpec("commercial_symbols", "Commercial Symbols", "amenities",
              parent="commercial", min_zoom=15),

    LayerSpec("green_spaces", "Green & Open Space", "environment",
              show=True, pinned=True),

    LayerSpec("squares", "Squares", "environment", show=True, pinned=True),

]


def _population_layers():
    from .indicators import MAPPED

    density, *rest = MAPPED

    return [
        LayerSpec(density.layer_id, f"{density.label} (ELSTAT 2021)",
                  "population", short=density.short),
        LayerSpec("pop_density_100m",
                  "Population Density \u2013 100 m (GHSL 2020)",
                  "population", short="100 m grid"),
    ] + [
        LayerSpec(indicator.layer_id, indicator.label, "population",
                  short=indicator.short)
        for indicator in rest
    ]


LAYERS += _population_layers()


EXCLUSIVE = [
    ["zones"] + [spec.id for spec in LAYERS if spec.theme == "population"],
]


SPEC = {layer.id: layer for layer in LAYERS}
PARENTS = [layer for layer in LAYERS if not layer.is_detail]
PINNED = [layer.id for layer in LAYERS if layer.pinned]
AUTO_HIDE = {
    layer.id: layer.auto_hide_above
    for layer in LAYERS
    if layer.auto_hide_above is not None
}
DETAILS = [layer for layer in LAYERS if layer.is_detail]


def spec(layer_id):
    """Look up a LayerSpec, with a helpful error for typos."""
    try:
        return SPEC[layer_id]
    except KeyError:
        raise KeyError(
            f"Unknown layer {layer_id!r}. Known layers: {', '.join(sorted(SPEC))}"
        ) from None


def menu():
    """The menu tree."""
    tree = {}
    for theme in THEMES:
        entries, seen = [], set()
        for layer in PARENTS:
            if layer.theme != theme or layer.pinned:
                continue
            if layer.group is None:
                entries.append({"kind": "layer", "layer": layer})
            elif layer.group not in seen:
                seen.add(layer.group)
                entries.append({
                    "kind": "group",
                    "group": layer.group,
                    "label": GROUPS[layer.group],
                    "layers": [l for l in PARENTS
                               if l.theme == theme and l.group == layer.group],
                })
        tree[theme] = entries
    return tree
