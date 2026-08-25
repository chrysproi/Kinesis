"""Which source layer becomes which web layer, and how."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    """A layer that `prepare_web_layer` can handle unaided."""

    name: str
    source: str
    simplify: float = 2
    geom_types: tuple | None = None
    explode: bool = False
    clip: bool = True
    thin_distance: float = 0
    columns: object = None
    optional_columns: tuple = field(default_factory=tuple)


POINT = ("Point",)
LINE = ("LineString", "MultiLineString")
POLYGON = ("Polygon", "MultiPolygon")


SIMPLE = [
    Source("buildings", "buildings", simplify=3),

    Source("bus_lanes", "bus_lanes"),
    Source("bike_lanes_primary", "bike_lanes_primary"),
    Source("bike_lanes_secondary", "bike_lanes_secondary"),
    Source("bike_lanes_proposed", "bike_lanes_proposed",
           geom_types=LINE, clip=False),

    Source("bike_parking", "bike_parking", simplify=0),
    Source("bike_rental", "bike_rental", simplify=0),

    Source("metro_line", "metro_line", simplify=1,
           geom_types=LINE, explode=False, columns="all"),
    Source("metro_stations", "metro_stations", simplify=0,
           geom_types=POINT, explode=True, columns="all"),

    Source("ferry_routes", "ferry_routes", simplify=5,
           geom_types=LINE, clip=False, columns="all"),
    Source("ferry_terminals", "ferry_terminals", simplify=0,
           geom_types=POINT, explode=True, clip=False, columns="all"),

    Source("parking_places", "parking_places", simplify=0,
           geom_types=POLYGON, columns="all"),

    Source("landuse", "landuse", simplify=5,
           geom_types=POLYGON, columns=["LU_GROUP", "landuse"],
           optional_columns=("name",)),

    Source("municipalities", "municipalities_indicators", simplify=2,
           geom_types=POLYGON, clip=False,
           columns=["NAME_ENG", "NAME_GR", "DIMOS", "POP_2021",
                    "AREA_KM2", "POP_DENS"],
           optional_columns=("AGE60_PCT", "UNEMP_PCT",
                             "HIGHEDU_PCT", "NOCAR_PCT")),
]

SIMPLE_BY_NAME = {source.name: source for source in SIMPLE}
SPECIAL = ["water", "bus_stops", "parking_points",
           "taxi_spots", "trees", "education", "culture",
           "health", "sport", "public_services", "commercial",
           "walkways",
           "buildings_height",
           "open_spaces",
           "hub_network"]

ALL_NAMES = [source.name for source in SIMPLE] + SPECIAL
