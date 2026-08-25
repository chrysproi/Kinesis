"""Which source layer becomes which web layer, and how.

Everything expressible as "clip, simplify, reproject" lives in SIMPLE as
data. The four layers needing derived columns or a merge get a function
in `special.py`.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    """A layer that `prepare_web_layer` can handle unaided."""

    name: str                       # output name, without _web_4326
    source: str                     # source file, without .gpkg
    simplify: float = 2             # metres; 0 disables
    geom_types: tuple | None = None
    explode: bool = False
    clip: bool = True
    thin_distance: float = 0        # metres; collapse co-located points
    columns: object = None          # None = geometry only, "all", or a list
    optional_columns: tuple = field(default_factory=tuple)


POINT = ("Point",)
LINE = ("LineString", "MultiLineString")
POLYGON = ("Polygon", "MultiPolygon")


SIMPLE = [
    # Buildings dominate file size, so they get the heaviest simplification
    Source("buildings", "buildings", simplify=3),

    Source("bus_lanes", "bus_lanes"),
    Source("bike_lanes_primary", "bike_lanes_primary"),
    Source("bike_lanes_secondary", "bike_lanes_secondary"),
    # The proposed network, 3.3 km over 9 lines and carrying no
    # attributes of its own. Not clipped: it is drawn inside the study
    # area by definition, and clipping a 9-line file buys nothing.
    Source("bike_lanes_proposed", "bike_lanes_proposed",
           geom_types=LINE, clip=False),

    # Points gain nothing from simplification
    Source("bike_parking", "bike_parking", simplify=0),
    Source("bike_rental", "bike_rental", simplify=0),

    # These keep every attribute: the map reads feature names from
    # whichever of name / name:el / station the source happens to carry.
    Source("metro_line", "metro_line", simplify=1,
           geom_types=LINE, explode=False, columns="all"),
    Source("metro_stations", "metro_stations", simplify=0,
           geom_types=POINT, explode=True, columns="all"),

    # Ferry routes run outside the study area, so they are not clipped
    Source("ferry_routes", "ferry_routes", simplify=5,
           geom_types=LINE, clip=False, columns="all"),
    # Not thinned. The port is listed once per berth, 424-810 m apart, and
    # collapsing those cost two of the six terminals — a visible loss for a
    # layer this small. Keeping all six only costs one zoom level: they are
    # clean from z12 instead of z11.
    Source("ferry_terminals", "ferry_terminals", simplify=0,
           geom_types=POINT, explode=True, clip=False, columns="all"),

    Source("parking_places", "parking_places", simplify=0,
           geom_types=POLYGON, columns="all"),

    # Land use. LU_GROUP is the pre-grouped category the map draws from;
    # `landuse` is kept per the brief, for the detail behind the group.
    # Three columns out of the source's 228 — the rest is OSM kitchen
    # sink, and carrying it would treble the exported file.
    #
    # Simplified at 5 m. Heavier tolerances barely help: these follow
    # parcel boundaries, so the cost is vertex count, and 15 m only takes
    # 7.9 MB to 5.2 MB. Gzipped it is 0.84 MB either way.
    Source("landuse", "landuse", simplify=5,
           geom_types=POLYGON, columns=["LU_GROUP", "landuse"],
           optional_columns=("name",)),

    # ELSTAT 2021 indicators per municipality. Not clipped: the 14
    # polygons dissolve to exactly the study boundary already — their
    # total area matches thess_units to the last digit.
    #
    # An explicit column list rather than "all", to drop the source's
    # own `zone` field. It carries one value per municipality, but a
    # municipality spans up to three zones (Echedoro, Lagadas,
    # Oreokastro, Panorama, Stavroupoli and Thermi each span all three),
    # so the dissolve kept an arbitrary member unit's label and marked
    # dense urban cores like Sykees "Regional".
    Source("municipalities", "municipalities_indicators", simplify=2,
           geom_types=POLYGON, clip=False,
           columns=["NAME_ENG", "NAME_GR", "DIMOS", "POP_2021",
                    "AREA_KM2", "POP_DENS"],
           optional_columns=("AGE60_PCT", "UNEMP_PCT",
                             "HIGHEDU_PCT", "NOCAR_PCT")),
]

SIMPLE_BY_NAME = {source.name: source for source in SIMPLE}

# Layers needing derived columns or a merge, handled in special.py
SPECIAL = ["water", "bus_stops", "parking_points",
           "taxi_spots", "trees", "education", "culture",
           # Section 3B destinations, all points-only
           "health", "sport", "public_services", "commercial",
           # The walkable network, as a display layer
           "walkways",
           # 192,645 footprints with surveyed roof heights
           "buildings_height",
           # Playgrounds, green & recreational space, squares
           "open_spaces",
           # 222 scored candidate hub sites in three tiers
           "hub_network"]

ALL_NAMES = [source.name for source in SIMPLE] + SPECIAL
