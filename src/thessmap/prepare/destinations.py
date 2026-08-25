"""Important destinations: health, sport, public services, commercial.

Section 3B of the brief. All four are shown as point symbols only, the
way education and culture already are — the question these layers answer
is "what is here", and a footprint adds nothing an icon does not say.

Three of the four arrive as polygons, so each feature becomes one
representative point inside itself. Categories come from the OSM tags,
not from the files' own SUBCATEGORY column; see classify.py for why.
"""

import geopandas as gpd

from .. import config
from .amenities import MIN_SYMBOL_DISTANCE, _finalise, _load_source
from .classify import (DROP_AMENITIES, classify_commercial, classify_health,
                       classify_public_service, classify_sport)
from .geometry import keep_columns, to_symbol_points

# Kept on every destination layer. `dest_category` is what the map draws
# an icon from; `dest_source` records which file a feature came from,
# which is the only way to audit a merged layer later.
DESTINATION_COLUMNS = ["dest_category", "dest_source"]

# Attributes worth a popup row, kept when the file happens to carry them.
# The health and sports files went through a shapefile, which truncated
# their column names to ten characters, so both spellings are listed.
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
        self.sources = sources          # source file stems, without .gpkg
        self.classifier = classifier


DESTINATIONS = [
    # Four hospital nodes plus 27 hospital footprints. The nodes are
    # entrances and buildings inside the same campuses, so thinning
    # collapses the duplicates.
    Destination("health", ["health_points", "health_polygons"],
                classify_health),

    # 874 pitches and 27 stadiums. The largest new symbol layer by far,
    # and 90% unnamed — it is a texture of local facilities with a few
    # landmarks in it.
    Destination("sport", ["sport_pitches", "sport_stadiums"],
                classify_sport),

    Destination("public_services", ["public_services"],
                classify_public_service),

    Destination("commercial", ["commercial_major"],
                classify_commercial),
]

DESTINATIONS_BY_NAME = {d.name: d for d in DESTINATIONS}


def prepare_destination(name, boundary, raw=None, processed=None, verbose=True):
    """
    Build one destination layer: merge its sources, categorise, thin.

    Polygon-derived symbols are protected during thinning so a mapped
    hospital campus never loses its icon to an entrance node beside it.
    """

    raw = raw or config.RAW
    processed = processed or config.PROCESSED

    spec = DESTINATIONS_BY_NAME[name]
    layers = []

    for source in spec.sources:
        gdf = _load_source(raw / f"{source}.gpkg", boundary)

        # Entrances mapped onto a mall or a public building are the same
        # destination counted twice
        if "amenity" in gdf.columns:
            before = len(gdf)
            gdf = gdf[~gdf["amenity"].isin(DROP_AMENITIES)].copy()
            if verbose and len(gdf) != before:
                print(f"  {source}: dropped {before - len(gdf)} entrance nodes")

        if not len(gdf):
            continue

        gdf["dest_category"] = gdf.apply(spec.classifier, axis=1)
        gdf["dest_source"] = source

        # A point per feature, wherever the geometry started
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
