"""Generating the web app's data and layer definitions from Python.

`registry.py` and `palette.py` stay the single source of truth: this
module turns them into GeoJSON files, MapLibre layer definitions and a
TypeScript module. Nothing about a layer — its label, its zoom range,
its colour — is written twice.
"""

import json
import re

from . import config, palette, registry
from .prepare.sources import SIMPLE_BY_NAME

# Web CRS layers small enough to ship as GeoJSON during development.
# Buildings and water move to vector tiles later; they are excluded here
# because plain GeoJSON would be tens of megabytes.
GEOJSON_SOURCES = {
    "zones": "units_4326",
    "municipalities": "municipalities",
    "landuse": "landuse",
    "buildings_height": "buildings_height",
    "lakes": "selected_lakes",
    "water_lines": "water_lines",
    "water_polygons": "water_polygons",
    "water_points": "water_points",
    "walkways": "walkways",
    "bus_lanes": "bus_lanes",
    "bike_lanes_primary": "bike_lanes_primary",
    "bike_lanes_secondary": "bike_lanes_secondary",
    "bike_lanes_proposed": "bike_lanes_proposed",
    "bike_points": "bike_points",
    "bus_stops": "bus_stops",
    "metro_line": "metro_line",
    "metro_stations": "metro_stations",
    "ferry_routes": "ferry_routes",
    "ferry_terminals": "ferry_terminals",
    "parking_places": "parking_places",
    "parking_points": "parking_points",
    "taxi_spots": "taxi_spots",
    "education_polygons": "education_polygons",
    "education_symbols": "education_symbols",
    "culture_polygons": "culture_polygons",
    "culture_lines": "culture_lines",
    "culture_symbols": "culture_symbols",
    "playground_symbols": "playground_symbols",
    "green_spaces": "green_spaces",
    "squares": "squares",
    "health_symbols": "health_symbols",
    "sport_symbols": "sport_symbols",
    "public_services_symbols": "public_services_symbols",
    "commercial_symbols": "commercial_symbols",
    "trees": "trees",
    "hub_network": "hub_network",
}

# Sources the frontend adds with clustering on. Mirrors Folium's
# MarkerCluster: a 30 px radius, and individual points from z18.
CLUSTERED_SOURCES = {
    "bike_points": {"radius": 30, "maxZoom": 17},
}

# Rasters shipped as coloured PNGs behind a MapLibre `image` source.
# {source name: (input GeoTIFF stem, output PNG name)}
RASTER_SOURCES = {
    "pop_density_100m": ("pop_density_100m", "pop_density_100m.png"),
}

# Icons that are supplied artwork rather than a colourised lucide glyph.
# {sprite id: file under web/public}
RASTER_ICONS = {
    palette.HUB_ICON: palette.HUB_ICON_FILE,
}

# 6 decimal places is ~0.1 m, far finer than anything visible
COORDINATE_PRECISION = 6

# Sources where even that is more than the geometry deserves. Buildings
# are simplified at 0.5 m and there are 192,565 of them, so the sixth
# decimal costs 2.9 MB of exported GeoJSON to describe a precision the
# footprints do not have.
PRECISION_OVERRIDES = {
    "buildings_height": 5,   # ~1 m
}

# Sources fetched only when their layer is first switched on, rather than
# at startup. Buildings are 64 MB and trees 8.7 MB, both off by default,
# and downloading them eagerly cost 28 seconds before the map could be
# used — for data most visitors never look at.
#
# Everything else stays eager: the whole rest of the payload is about
# 1 MB gzipped, and lazy loading it would trade a fast first paint for a
# stutter on every toggle.
LAZY_SOURCES = ["buildings_height", "trees"]

# Sources prepared with geometry only. Clicking one can never show
# anything, so layers drawn from them get no popup and no pointer cursor
# rather than an empty card.
GEOMETRY_ONLY = frozenset(
    name for name, source in SIMPLE_BY_NAME.items() if source.columns is None
)

# Sources that carry attributes but are still not worth clicking. The
# open-space fills are a backdrop: they cover most of the map, so a click
# meant for a stop or a symbol would land on a park instead.
NON_INTERACTIVE = frozenset({"green_spaces", "squares"})


def export_geojson(data, destination, verbose=True):
    """Write each web source to destination as GeoJSON."""

    destination.mkdir(parents=True, exist_ok=True)
    written = {}

    for name, attribute in GEOJSON_SOURCES.items():
        gdf = getattr(data, attribute)
        path = destination / f"{name}.geojson"

        gdf.to_file(
            path, driver="GeoJSON",
            COORDINATE_PRECISION=PRECISION_OVERRIDES.get(
                name, COORDINATE_PRECISION
            ),
        )

        written[name] = path.stat().st_size

        if verbose:
            print(f"  {name:<22} {len(gdf):>7} features  "
                  f"{written[name] / 1e6:>6.2f} MB")

    return written


# --------------------------------------------------
# MapLibre paint, derived from palette.py
# --------------------------------------------------


def _zone_match(key):
    """A MapLibre match expression over the zone column."""
    expression = ["match", ["get", "zone"]]
    for zone, style in palette.ZONE_STYLES.items():
        expression += [zone, style[key]]
    expression.append(palette.DEFAULT_ZONE_STYLE[key])
    return expression


def _ramp(pair, registry_id, hi_zoom=None):
    """Interpolate a (debut, max) pair across the zooms a layer is alive."""
    lo = _debut_zoom(registry_id)
    hi = hi_zoom if hi_zoom is not None else config.MAX_ZOOM
    if hi <= lo:
        return pair[0]
    return ["interpolate", ["linear"], ["zoom"], lo, pair[0], hi, pair[1]]


def _hint(layer_id, source, registry_id, color):
    """
    A small muted dot marking that a dataset is there, before its icon
    becomes readable. Presence first, detail later: without this a layer
    is simply absent until its detail zoom, which reads as an empty map
    that suddenly fills up.
    """
    return _layer(layer_id, source, "circle", {
        "circle-color": color,
        "circle-radius": _grow(
            lambda scale: round(palette.HINT_RADIUS * scale, 2), registry_id
        ),
        "circle-opacity": palette.HINT_OPACITY,
    }, registry_id=registry_id)


def _tree_heatmap():
    """
    Canopy density before individual trees are legible.

    42,000 points cannot be drawn as readable symbols until z18, but
    vegetation density is exactly the sort of information that should
    reach the reader early, so the layer arrives as a heatmap first.
    """
    ramp = ["interpolate", ["linear"], ["heatmap-density"]]
    for stop, color in palette.TREE_HEAT_RAMP:
        ramp += [stop, color]

    return {
        "heatmap-color": ramp,
        "heatmap-weight": 1,
        "heatmap-intensity": [
            "interpolate", ["linear"], ["zoom"], 13, 0.5, 16, 1.1,
        ],
        # Grows with zoom so the blur tracks real canopy spread
        "heatmap-radius": [
            "interpolate", ["linear"], ["zoom"], 13, 6, 16, 20,
        ],
        # Fades out as the stippled points take over
        "heatmap-opacity": [
            "interpolate", ["linear"], ["zoom"],
            13, palette.TREE_HEAT_OPACITY[0],
            16, palette.TREE_HEAT_OPACITY[1],
            17, 0,
        ],
    }


def _tree_texture_radius():
    """
    Stipple that grows into the full symbols: barely-there points at 16,
    the palette's height-class radii by 18.
    """
    return [
        "interpolate", ["linear"], ["zoom"],
        16, 2.0,
        17, 3.4,
        18, _tree_match(1),
        config.MAX_ZOOM, _tree_match(1, SYMBOL_MAX_SCALE),
    ]


def _dash(pattern_px, width):
    """
    Convert a pixel dash pattern to MapLibre units.

    Leaflet's dashArray is in pixels; MapLibre's line-dasharray is in
    multiples of line-width. Passing Leaflet's numbers straight through
    makes a 3 px line draw 12 px dashes.
    """
    return [round(value / width, 3) for value in pattern_px]


_BREAK_CACHE = {}


def indicator_breaks(column):
    """
    Jenks class bounds for one indicator column, from the real values.

    Computed here rather than hardcoded so the fill expression, the
    legend and the raster classification can never disagree, and so
    re-running on updated census figures reclassifies instead of
    silently mislabelling.
    """

    if column not in _BREAK_CACHE:
        from . import classify
        from .data import MapData

        values = MapData().municipalities[column].values
        _BREAK_CACHE[column] = classify.breaks(
            values, palette.POP_DENSITY_CLASSES
        )

    return _BREAK_CACHE[column]


def density_breaks():
    """The population-density breaks, which the 100 m raster shares."""
    return indicator_breaks("POP_DENS")


def _indicator_step(column):
    """
    A MapLibre step expression over one indicator column.

    `step` needs the interior breaks only: five classes, four stops. The
    last bound from the classifier is the data maximum, so it is dropped.
    """

    expression = ["step", ["get", column], palette.INDICATOR_RAMP[0]]

    for bound, colour in zip(indicator_breaks(column), palette.INDICATOR_RAMP[1:]):
        expression += [round(bound, 4), colour]

    return expression


def _fade(stops):
    """An opacity curve from (zoom, value) pairs."""
    expression = ["interpolate", ["linear"], ["zoom"]]
    for zoom, value in stops:
        expression += [zoom, value]
    return expression


def _zone_fill_opacity():
    """Per-zone fill opacity, faded out as the map zooms in."""

    def at(scale):
        expression = ["match", ["get", "zone"]]
        for zone, style in palette.ZONE_STYLES.items():
            expression += [zone, round(style["fillOpacity"] * scale, 3)]
        expression.append(
            round(palette.DEFAULT_ZONE_STYLE["fillOpacity"] * scale, 3)
        )
        return expression

    stops = []
    for zoom, scale in palette.ZONE_FILL_FADE:
        stops += [zoom, at(scale)]

    return ["interpolate", ["linear"], ["zoom"], *stops]


def _tree_match(index, scale=1):
    """Colour (0) or radius (1) per tree class, radius optionally scaled."""
    if index == 1:
        scale *= palette.TREE_DOT_SCALE

    expression = ["match", ["get", "tree_class"]]
    for tree_class, values in palette.TREE_CLASSES.items():
        value = values[index]
        expression += [tree_class, round(value * scale, 3) if index == 1 else value]
    fallback = palette.TREE_CLASSES["Unknown"][index]
    expression.append(round(fallback * scale, 3) if index == 1 else fallback)
    return expression


# Trees are physical objects, so their symbols hold a constant *ground*
# size rather than a constant pixel size. Metres per pixel halves with
# every zoom level, so the radius doubles to compensate.
#
# At zoom 18 and latitude 40.6, one pixel is ~0.45 m, which puts the
# palette's radii at ~1.0 m for saplings and ~2.3 m for the tallest
# class — sensible crown radii. Anchoring here keeps those true.
TREE_RADIUS_ANCHOR_ZOOM = 18


def _tree_radius():
    """Radius interpolated by zoom, preserving ground size."""

    span = config.MAX_ZOOM - TREE_RADIUS_ANCHOR_ZOOM
    scale = 2 ** span

    return [
        "interpolate", ["exponential", 2], ["zoom"],
        TREE_RADIUS_ANCHOR_ZOOM, _tree_match(1),
        config.MAX_ZOOM, _tree_match(1, scale),
    ]


def _bus_stop_radius(scale=1):
    """Service intensity as a step expression over line_count."""
    r = lambda value: round(value * scale, 2)
    expression = ["step", ["to-number", ["get", "line_count"], 0]]
    expression.append(r(palette.BUS_STOP_OUTER_RADII[0][1]))
    for max_lines, radius in palette.BUS_STOP_OUTER_RADII[1:]:
        expression += [max_lines, r(radius)]
    expression += [palette.BUS_STOP_OUTER_RADII[-1][0] + 1,
                   r(palette.BUS_STOP_MAX_RADIUS)]
    return expression


def _layer(layer_id, source, kind, paint, registry_id=None, source_layer=None):
    """One MapLibre layer, taking its zoom range from the registry."""

    spec = registry.SPEC.get(registry_id or layer_id)

    definition = {
        "id": layer_id,
        "type": kind,
        "source": source,
        "paint": paint,
    }

    if spec is not None:
        if spec.min_zoom is not None:
            definition["minzoom"] = spec.min_zoom
        if spec.max_zoom is not None:
            definition["maxzoom"] = spec.max_zoom

    definition["metadata"] = {
        # Which sidebar toggle owns this layer
        "thessmap:parent": (spec.parent or spec.id) if spec else layer_id,
        # The registry entry it was built from
        "thessmap:spec": spec.id if spec else layer_id,
        # Whether clicking a feature can show anything. A raster has no
        # features to query, so it never gets a popup or a pointer.
        "thessmap:interactive": (
            kind != "raster"
            and source not in GEOMETRY_ONLY
            and source not in NON_INTERACTIVE
        ),
    }

    return definition


# --------------------------------------------------
# Icon sprites
# --------------------------------------------------
# Each entry becomes a raster registered with map.addImage(). Emitted to
# TypeScript so the frontend never hardcodes an icon name or colour.

ICON_RASTER_SIZE = 24  # lucide's native viewBox

# A symbol debuts a little under its nominal size and grows to a little
# over it by the deepest zoom. Fixed-pixel symbols look oversized the
# moment they appear and undersized once the map has grown around them,
# which is what made plates and halos read as inconsistent.
SYMBOL_DEBUT_SCALE = 0.78
SYMBOL_MAX_SCALE = 1.22


def _debut_zoom(registry_id, fallback=None):
    spec = registry.SPEC.get(registry_id)
    if spec is not None and spec.min_zoom is not None:
        return spec.min_zoom
    return fallback if fallback is not None else config.MIN_ZOOM


def _grow(build, registry_id, hi_zoom=None):
    """
    Interpolate a size between a layer's debut zoom and the deepest zoom.

    `build` takes a scale factor and returns a number or a data-driven
    expression, so this works for plain radii and for the bus stop step
    expression alike.
    """

    spec = registry.SPEC.get(registry_id)

    lo = _debut_zoom(registry_id)

    # Interpolate only across the zooms the layer is actually alive for,
    # otherwise a layer that stops at 16 is sized as if it reached 19.
    if hi_zoom is not None:
        hi = hi_zoom
    elif spec is not None and spec.max_zoom is not None:
        hi = spec.max_zoom
    else:
        hi = config.MAX_ZOOM

    if hi <= lo:                      # nothing to interpolate across
        return build(1)

    return [
        "interpolate", ["linear"], ["zoom"],
        lo, build(SYMBOL_DEBUT_SCALE),
        hi, build(SYMBOL_MAX_SCALE),
    ]


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class _Sprites:
    """Collects the icons referenced while building layers."""

    def __init__(self):
        self.items = {}

    def add(self, sprite_id, lucide, color):
        self.items[sprite_id] = {
            "id": sprite_id,
            "lucide": lucide,
            "color": color,
            "size": ICON_RASTER_SIZE,
        }
        return sprite_id

    def manifest(self):
        return sorted(self.items.values(), key=lambda item: item["id"])


def _plated_symbol(layer_id, source, icon, registry_id, color,
                   plate_radius=9, icon_size=0.55, pane_color=None,
                   plate=True):
    """
    An icon, optionally on a white disc.

    Two layers rather than one: MapLibre has no notion of a symbol
    backdrop, and an unplated stroke icon disappears over dense basemap
    detail — the same reason the Folium symbols sat on white circles.

    `plate=False` for symbols that carry their own enclosure, or that read
    better bare — the parking P and the metro M both do.
    """

    plate_layer = _layer(
        f"{layer_id}-plate", source, "circle",
        {
            "circle-color": pane_color or palette.ICON_PLATE_COLOR,
            "circle-radius": _grow(
                lambda scale: round(plate_radius * palette.PLATE_SCALE * scale, 2),
                registry_id,
            ),
            "circle-stroke-color": color,
            "circle-stroke-width": 1,
        },
        registry_id=registry_id,
    )

    symbol = _layer(layer_id, source, "symbol", {}, registry_id=registry_id)
    symbol["layout"] = {
        "icon-image": icon,
        "icon-size": _grow(
            lambda scale: round(icon_size * palette.ICON_SCALE * scale, 3),
            registry_id,
        ),
        # Symbols are the point of the layer, so never drop one for overlap
        "icon-allow-overlap": True,
        "icon-ignore-placement": True,
    }
    del symbol["paint"]

    return [plate_layer, symbol] if plate else [symbol]

def _green_space_match():
    """A match expression over the derived green_subtype."""
    expression = ["match", ["get", "green_subtype"]]
    for subtype, colour in palette.GREEN_SPACE_COLORS.items():
        expression += [subtype, colour]
    expression.append(palette.GREEN_SPACE_COLORS[palette.GREEN_SPACE_FALLBACK])
    return expression


def _building_height_step():
    """A step expression over ROOF_H, on round metre breaks."""

    expression = ["step", ["get", "ROOF_H"], palette.BUILDING_HEIGHT_RAMP[0]]

    for bound, colour in zip(palette.BUILDING_HEIGHT_BREAKS,
                             palette.BUILDING_HEIGHT_RAMP[1:]):
        expression += [bound, colour]

    return expression


def _landuse_match(key="color"):
    """A MapLibre match expression over LU_GROUP."""
    source = (palette.LANDUSE_COLORS if key == "color"
              else palette.LANDUSE_LABELS)
    fallback = (palette.LANDUSE_FALLBACK_COLOR if key == "color"
                else "Other / transitional")

    expression = ["match", ["get", "LU_GROUP"]]
    for group, value in source.items():
        expression += [group, value]
    expression.append(fallback)

    return expression


def _indicator_layers():
    """A fill and a hairline outline per mapped indicator."""
    from .indicators import MAPPED

    layers = []

    for indicator in MAPPED:
        layers.append(_layer(
            f"{indicator.layer_id}-fill", "municipalities", "fill", {
                "fill-color": _indicator_step(indicator.column),
                "fill-opacity": _fade(palette.INDICATOR_FILL_OPACITY),
            }, registry_id=indicator.layer_id))

        # White rather than a ramp colour: a coloured edge on a
        # sequential fill reads as a sixth class.
        layers.append(_layer(
            f"{indicator.layer_id}-outline", "municipalities", "line", {
                "line-color": palette.POP_DENSITY_OUTLINE,
                "line-width": _ramp(palette.POP_DENSITY_OUTLINE_WIDTH,
                                    indicator.layer_id),
                "line-opacity": palette.POP_DENSITY_OUTLINE_OPACITY,
            }, registry_id=indicator.layer_id))

    return layers


def build_layers():
    """Every MapLibre layer, in draw order."""

    sprites = _Sprites()

    def icon(sprite_id, lucide, color):
        return sprites.add(sprite_id, lucide, color)

    bus_stop_icon = ["match", ["get", "stop_type_cat"]]
    for category, lucide in palette.BUS_STOP_ICONS.items():
        bus_stop_icon += [
            category,
            icon(f"bus-{_slug(category)}", lucide, palette.BUS_STOP_SYMBOL_COLOR),
        ]
    bus_stop_icon.append(
        f"bus-{_slug(palette.BUS_STOP_FALLBACK_CATEGORY)}"
    )

    culture_icon = ["match", ["get", "culture_subtype"]]
    for subtype, lucide in palette.CULTURE_ICONS.items():
        culture_icon += [
            subtype,
            icon(f"culture-{_slug(subtype)}", lucide, palette.CULTURE_SYMBOL_COLOR),
        ]
    culture_icon.append(
        f"culture-{_slug(palette.CULTURE_FALLBACK_SUBTYPE)}"
    )

    layers = [
        # ---------------- zones ----------------
        _layer("zones-fill", "zones", "fill", {
            "fill-color": _zone_match("fillColor"),
            "fill-opacity": _zone_fill_opacity(),
        }, registry_id="zones"),
        # ---------------- population ----------------
        # Between the zone fill and the zone outline on purpose. All of
        # these fill the same footprint as the zones, so a choropleth
        # drawn under the wash would be invisible whenever zones are on;
        # drawn over the outline it would swallow the boundaries. Here it
        # covers the wash and the boundaries still read on top.
        *_indicator_layers(),

        # The 100 m grid, above the municipal fills: the same measure at
        # finer resolution, so the detail wins where both are on.
        _layer("pop-density-100m", "pop_density_100m", "raster", {
            "raster-opacity": _fade(palette.POP_RASTER_OPACITY),
            # Nearest keeps a 100 m cell a visible cell instead of
            # smoothing measured counts into a gradient
            "raster-resampling": "nearest",
        }, registry_id="pop_density_100m"),

        _layer("zones-outline", "zones", "line", {
            "line-color": _zone_match("color"),
            # The outline carries the boundary once the fill has faded
            "line-width": [
                "interpolate", ["linear"], ["zoom"],
                config.MIN_ZOOM, 0.8,
                16, 1.6,
            ],
            "line-opacity": 0.9,
        }, registry_id="zones"),

        # ---------------- land use ----------------
        # Above the zone and indicator fills, below every network. It
        # describes the character of an area, so it belongs behind the
        # infrastructure drawn across it — but in front of a regional
        # wash it would otherwise be buried under.
        _layer("landuse-fill", "landuse", "fill", {
            "fill-color": _landuse_match(),
            "fill-opacity": _fade(palette.LANDUSE_FILL_OPACITY),
        }, registry_id="landuse"),
        # A hairline so adjacent parcels of one category stay countable
        _layer("landuse-outline", "landuse", "line", {
            "line-color": _landuse_match(),
            "line-width": _ramp(palette.LANDUSE_EDGE_WIDTH, "landuse"),
            "line-opacity": palette.LANDUSE_EDGE_OPACITY,
        }, registry_id="landuse"),

        _layer("buildings-height", "buildings_height", "fill", {
            "fill-color": _building_height_step(),
            "fill-opacity": _fade(palette.BUILDING_HEIGHT_OPACITY),
        }, registry_id="buildings"),

        # ---------------- public open space ----------------
        # Above land use, below every network: open space is a kind of
        # ground, and the networks cross it.
        _layer("green-spaces-fill", "green_spaces", "fill", {
            "fill-color": _green_space_match(),
            "fill-opacity": _fade(palette.GREEN_SPACE_FILL_OPACITY),
        }, registry_id="green_spaces"),
        _layer("green-spaces-outline", "green_spaces", "line", {
            "line-color": palette.GREEN_SPACE_EDGE,
            "line-width": _ramp((0.4, 0.9), "green_spaces"),
            "line-opacity": 0.5,
        }, registry_id="green_spaces"),

        _layer("squares-fill", "squares", "fill", {
            "fill-color": palette.SQUARE_FILL,
            "fill-opacity": _fade(palette.SQUARE_FILL_OPACITY),
        }, registry_id="squares"),
        _layer("squares-outline", "squares", "line", {
            "line-color": palette.SQUARE_EDGE,
            "line-width": _ramp((0.4, 1.0), "squares"),
            "line-opacity": 0.7,
        }, registry_id="squares"),

        # ---------------- environment ----------------
        # Water bodies under the lake fill: a riverbank or reservoir is
        # the same substance, so it takes the same fill.
        _layer("water-bodies", "water_polygons", "fill", {
            "fill-color": palette.WATER_FILL,
            "fill-opacity": palette.WATER_BODY_FILL_OPACITY,
            "fill-outline-color": palette.WATER_EDGE,
        }, registry_id="water_major"),

        _layer("lakes-fill", "lakes", "fill", {
            "fill-color": palette.WATER_FILL,
            "fill-opacity": 0.8,
            "fill-outline-color": palette.WATER_EDGE,
        }, registry_id="lakes"),

        _layer("water-minor", "water_lines", "line", {
            "line-color": palette.WATER_LINE_COLOR,
            "line-width": _ramp(palette.WATER_MINOR_WIDTH, "water_minor"),
            "line-opacity": palette.WATER_LINE_OPACITY,
        }, registry_id="water_minor") | {
            "filter": ["!", ["in", ["get", "waterway"],
                             ["literal", ["river", "canal"]]]]},

        _layer("water-major", "water_lines", "line", {
            "line-color": palette.WATER_LINE_COLOR,
            "line-width": _ramp(palette.WATER_MAJOR_WIDTH, "water_major"),
            "line-opacity": palette.WATER_LINE_OPACITY,
        }, registry_id="water_major") | {
            "filter": ["in", ["get", "waterway"],
                       ["literal", ["river", "canal"]]]},

        _layer("water-structures", "water_points", "circle", {
            "circle-color": palette.WATER_STRUCTURE_COLOR,
            "circle-radius": _grow(
                lambda scale: round(palette.WATER_STRUCTURE_RADIUS * scale, 2),
                "water_structures"),
            "circle-stroke-color": palette.WATER_STRUCTURE_STROKE,
            "circle-stroke-width": 0.8,
        }, registry_id="water_structures"),

        # Trees in three tiers: density, then stipple, then symbols
        _layer("trees-heat", "trees", "heatmap", _tree_heatmap(),
               registry_id="trees_density"),
        _layer("trees-circle", "trees", "circle", {
            "circle-color": _tree_match(0),
            "circle-radius": _tree_texture_radius(),
            "circle-stroke-color": palette.TREE_EDGE_COLOR,
            # The outline would swamp a 1.3 px stipple, so it fades in
            "circle-stroke-width": [
                "interpolate", ["linear"], ["zoom"], 17, 0, 18, 0.35,
            ],
            "circle-opacity": [
                "interpolate", ["linear"], ["zoom"], 16, 0.45, 18, 0.72,
            ],
            "circle-stroke-opacity": 0.8,
        }, registry_id="trees_texture"),

        # ---------------- transport ----------------
        # First, so every network draws over it: this is the substrate
        # people walk on, not a mode competing with the others.
        _layer("walkways", "walkways", "line", {
            "line-color": palette.WALKWAY_COLOR,
            "line-width": _ramp(palette.WALKWAY_WIDTH, "walkways"),
            "line-dasharray": _dash(palette.WALKWAY_DASH,
                                    palette.WALKWAY_WIDTH[0]),
            "line-opacity": palette.WALKWAY_OPACITY,
        }, registry_id="walkways"),

        _layer("bus-lanes", "bus_lanes", "line", {
            "line-color": palette.BUS_LANE_COLOR,
            "line-width": _ramp(palette.BUS_LANE_WIDTH, "bus_lanes"),
            "line-opacity": palette.BUS_LANE_OPACITY,
        }, registry_id="bus_lanes"),

        _layer("bike-primary", "bike_lanes_primary", "line", {
            "line-color": palette.BIKE_COLOR,
            "line-width": _ramp(palette.BIKE_PRIMARY_WIDTH, "bike_lanes"),
        }, registry_id="bike_lanes"),
        _layer("bike-proposed", "bike_lanes_proposed", "line", {
            "line-color": palette.BIKE_COLOR,
            "line-width": _ramp(palette.BIKE_PROPOSED_WIDTH,
                                "bike_lanes_proposed"),
            "line-dasharray": _dash(palette.BIKE_PROPOSED_DASH,
                                    palette.BIKE_PROPOSED_WIDTH[0]),
            "line-opacity": palette.BIKE_PROPOSED_OPACITY,
        }, registry_id="bike_lanes_proposed"),

        _layer("bike-secondary", "bike_lanes_secondary", "line", {
            "line-color": palette.BIKE_COLOR,
            "line-width": _ramp(palette.BIKE_SECONDARY_WIDTH, "bike_detail"),
            "line-dasharray": _dash(palette.BIKE_SECONDARY_DASH,
                                    palette.BIKE_SECONDARY_WIDTH[0]),
        }, registry_id="bike_detail"),

        # Bus stop halo and dot stay circles: the radius carries meaning
        _layer("bus-stops-halo", "bus_stops", "circle", {
            "circle-color": palette.BUS_STOP_OUTER_COLOR,
            "circle-radius": _grow(_bus_stop_radius, "bus_stops_outer"),
            "circle-opacity": palette.BUS_STOP_HALO_OPACITY,
        }, registry_id="bus_stops_outer"),
        _layer("bus-stops-dot", "bus_stops", "circle", {
            "circle-color": palette.BUS_STOP_SIMPLE_COLOR,
            "circle-radius": _grow(
                lambda scale: round(2.9 * scale, 2), "bus_stops_simple"
            ),
            "circle-opacity": palette.BUS_STOP_DOT_OPACITY,
        }, registry_id="bus_stops_simple"),

        # A single line whose weight and opacity ease with zoom. Folium
        # needed two layers swapped at z14 because it could not interpolate;
        # that swap was a visible jump with nothing behind it.
        _layer("metro-line", "metro_line", "line", {
            "line-color": palette.METRO_LINE_COLOR,
            "line-width": _ramp(palette.METRO_LINE_WIDTH, "metro_line"),
            "line-opacity": _ramp(palette.METRO_LINE_OPACITY, "metro_line"),
            "line-dasharray": _dash(palette.METRO_DASH,
                                    palette.METRO_LINE_WIDTH[0]),
        }, registry_id="metro_line"),
        _layer("metro-stations-halo", "metro_stations", "circle", {
            "circle-color": palette.BUS_STOP_OUTER_COLOR,
            "circle-radius": _grow(
                lambda scale: round(palette.BUS_STOP_MAX_RADIUS * scale, 2),
                "metro_stations_outer",
            ),
            "circle-opacity": 0.35,
        }, registry_id="metro_stations_outer"),

        _layer("ferry-routes", "ferry_routes", "line", {
            "line-color": palette.FERRY_ROUTE_COLOR,
            "line-width": _ramp(palette.FERRY_ROUTE_WIDTH, "ferry_routes"),
            "line-opacity": palette.FERRY_ROUTE_OPACITY,
            "line-dasharray": _dash(palette.FERRY_DASH,
                                    palette.FERRY_ROUTE_WIDTH[0]),
        }, registry_id="ferry_routes"),

        _layer("parking-fill", "parking_places", "fill", {
            "fill-color": palette.PARKING_COLOR,
            "fill-opacity": palette.PARKING_FILL_OPACITY,
            "fill-outline-color": palette.PARKING_COLOR,
        }, registry_id="parking_polygons"),

        # ---------------- amenities ----------------
        _layer("education-fill", "education_polygons", "fill", {
            "fill-color": palette.EDUCATION_COLOR,
            "fill-opacity": palette.EDUCATION_FILL_OPACITY,
            "fill-outline-color": palette.EDUCATION_COLOR,
        }, registry_id="education_polygons"),

        _layer("culture-fill", "culture_polygons", "fill", {
            "fill-color": palette.CULTURE_COLOR,
            "fill-opacity": palette.CULTURE_FILL_OPACITY,
        }, registry_id="culture_polygons"),
        _layer("culture-lines", "culture_lines", "line", {
            "line-color": palette.CULTURE_LINE_COLOR,
            "line-width": _ramp(palette.CULTURE_LINE_WIDTH, "culture_lines"),
            "line-opacity": palette.CULTURE_LINE_OPACITY,
        }, registry_id="culture_lines"),
    ]

    # ---------------- presence hints, before the icons are readable -------
    layers += [
        _hint("parking-hint", "parking_points", "parking_hint",
              palette.PARKING_COLOR),
        _hint("education-hint", "education_symbols", "education_hint",
              palette.EDUCATION_SYMBOL_COLOR),
        _hint("culture-hint", "culture_symbols", "culture_hint",
              palette.CULTURE_SYMBOL_COLOR),
        _hint("taxi-hint", "taxi_spots", "taxi_hint", palette.TAXI_COLOR),

        # Section 3B destination hints
        _hint("health-hint", "health_symbols", "health_hint",
              palette.DESTINATION_INK),
        _hint("sport-hint", "sport_symbols", "sport_hint",
              palette.DESTINATION_INK),
        _hint("public-services-hint", "public_services_symbols",
              "public_services_hint", palette.DESTINATION_INK),
        _hint("commercial-hint", "commercial_symbols", "commercial_hint",
              palette.DESTINATION_INK),
        _hint("playground-hint", "playground_symbols", "playground_hint",
              palette.PLAYGROUND_SYMBOL_COLOR),
    ]

    # ---------------- plated icons, drawn last so they sit on top ----------
    layers += _plated_symbol(
        "bike-points", "bike_points",
        ["match", ["get", "kind"],
         "parking", icon("bike-parking", palette.ICON_BIKE_PARKING,
                         palette.BIKE_COLOR),
         "rental", icon("bike-rental", palette.ICON_BIKE_RENTAL,
                        palette.BIKE_COLOR),
         icon("bike-parking", palette.ICON_BIKE_PARKING, palette.BIKE_COLOR)],
        "bike_points", palette.BIKE_COLOR,
        icon_size=1.0, plate=False,
    )
    # Only the points outside a cluster draw individually
    layers[-1]["filter"] = ["!", ["has", "point_count"]]

    layers += _plated_symbol(
        "bus-stops-symbol", "bus_stops",
        bus_stop_icon,
        "bus_stops_symbols", palette.BUS_STOP_SYMBOL_COLOR,
        # No plate: the marks carry their own white fill where they need
        # one, exactly as the Folium symbols did.
        icon_size=0.78, plate=False,
    )
    layers += _plated_symbol(
        "metro-stations", "metro_stations",
        icon("metro-station", palette.ICON_METRO_STATION, palette.METRO_SYMBOL_COLOR),
        "metro_stations_symbols", palette.METRO_SYMBOL_COLOR,
        icon_size=0.72, plate=False,
    )
    layers += _plated_symbol(
        "ferry-terminals", "ferry_terminals",
        icon("ferry-terminal", palette.ICON_FERRY_TERMINAL, palette.FERRY_TERMINAL_COLOR),
        "ferry_terminals_symbols", palette.FERRY_TERMINAL_COLOR,
        plate_radius=9, icon_size=0.55,
    )
    layers += _plated_symbol(
        "parking-symbols", "parking_points",
        icon("parking", palette.ICON_PARKING, palette.PARKING_COLOR),
        "parking_symbols", palette.PARKING_COLOR,
        icon_size=0.62, plate=False,
    )
    layers += _plated_symbol(
        "taxi-spots", "taxi_spots",
        icon("taxi", palette.ICON_TAXI, palette.TAXI_COLOR),
        "taxi_symbols", palette.TAXI_COLOR, plate_radius=9, icon_size=0.55,
    )
    education_icon = ["match", ["get", "education_type"]]
    for category, lucide in palette.EDUCATION_ICONS.items():
        education_icon += [
            category,
            icon(f"education-{_slug(category)}", lucide,
                 palette.EDUCATION_SYMBOL_COLOR),
        ]
    education_icon.append(
        f"education-{_slug(palette.EDUCATION_FALLBACK_CATEGORY)}"
    )

    layers += _plated_symbol(
        "education-symbols", "education_symbols", education_icon,
        "education_symbols", palette.EDUCATION_SYMBOL_COLOR,
        plate_radius=9, icon_size=0.55,
    )
    layers += _plated_symbol(
        "playground-symbols", "playground_symbols",
        icon("playground", palette.PLAYGROUND_ICONS["Playground"],
             palette.PLAYGROUND_SYMBOL_COLOR),
        "playground_symbols", palette.PLAYGROUND_SYMBOL_COLOR,
        plate_radius=9, icon_size=0.55,
    )

    layers += _plated_symbol(
        "culture-symbols", "culture_symbols", culture_icon,
        "culture_symbols", palette.CULTURE_SYMBOL_COLOR,
        plate_radius=9, icon_size=0.55,
    )

    # Section 3B destinations. Each draws its icon from dest_category,
    # which classify.py derives from the OSM tags — see there for why the
    # files' own SUBCATEGORY column is not used.
    for prefix, source, icons, fallback in (
        ("health", "health_symbols",
         palette.HEALTH_ICONS, palette.HEALTH_FALLBACK_CATEGORY),
        ("sport", "sport_symbols",
         palette.SPORT_ICONS, palette.SPORT_FALLBACK_CATEGORY),
        ("public-services", "public_services_symbols",
         palette.PUBLIC_SERVICE_ICONS, palette.PUBLIC_SERVICE_FALLBACK_CATEGORY),
        ("commercial", "commercial_symbols",
         palette.COMMERCIAL_ICONS, palette.COMMERCIAL_FALLBACK_CATEGORY),
    ):
        expression = ["match", ["get", "dest_category"]]
        for category, lucide in icons.items():
            expression += [
                category,
                icon(f"{prefix}-{_slug(category)}", lucide,
                     palette.DESTINATION_INK),
            ]
        expression.append(f"{prefix}-{_slug(fallback)}")

        layers += _plated_symbol(
            f"{prefix}-symbols", source, expression,
            f"{source.replace('_symbols', '')}_symbols",
            palette.DESTINATION_INK,
            plate_radius=9, icon_size=0.55,
        )

    # Last in the list, so a hub is never occluded by the infrastructure
    # it is being judged against, and lowest tier first so the ranking
    # survives overlap. Every tier excludes the selected hub, or it would
    # carry both its own mark and the Kinesis one.
    unselected = ["!=", ["get", "hub_selected"], True]

    def tier_filter(tier):
        return ["all", ["==", ["get", "hub_tier"], tier], unselected]

    # z12-14: the whole network as one undifferentiated dot
    layers.append(_layer("hub-overview", "hub_network", "circle", {
        "circle-color": palette.HUB_OVERVIEW_COLOR,
        "circle-radius": _ramp(palette.HUB_OVERVIEW_RADIUS, "hub_overview",
                               hi_zoom=14),
        "circle-stroke-color": palette.HUB_DOT_STROKE,
        "circle-stroke-width": palette.HUB_DOT_STROKE_WIDTH,
    }, registry_id="hub_overview"))

    # 170 street-scale sites: the texture tier, a plain dot
    layers.append(_layer("hub-street", "hub_network", "circle", {
        "circle-color": palette.HUB_STREET_COLOR,
        "circle-radius": _ramp(palette.HUB_STREET_RADIUS, "hub_street"),
        "circle-stroke-color": palette.HUB_DOT_STROKE,
        "circle-stroke-width": palette.HUB_DOT_STROKE_WIDTH,
    }, registry_id="hub_street"))
    layers[-1]["filter"] = tier_filter("Street-scale hub")

    # 44 neighbourhood sites: a ring, drawn as a filled dot with a white
    # core over it, since MapLibre circles have no inner radius
    layers.append(_layer("hub-neighbourhood", "hub_network", "circle", {
        "circle-color": palette.HUB_NEIGHBOURHOOD_COLOR,
        "circle-radius": _ramp(palette.HUB_NEIGHBOURHOOD_RADIUS,
                               "hub_neighbourhood"),
        "circle-stroke-color": palette.HUB_DOT_STROKE,
        "circle-stroke-width": palette.HUB_DOT_STROKE_WIDTH,
    }, registry_id="hub_neighbourhood"))
    layers[-1]["filter"] = tier_filter("Neighbourhood hub")

    core = tuple(round(r * palette.HUB_NEIGHBOURHOOD_CORE_RATIO, 2)
                 for r in palette.HUB_NEIGHBOURHOOD_RADIUS)
    layers.append(_layer("hub-neighbourhood-core", "hub_network", "circle", {
        "circle-color": palette.HUB_NEIGHBOURHOOD_CORE,
        "circle-radius": _ramp(core, "hub_neighbourhood"),
    }, registry_id="hub_neighbourhood"))
    layers[-1]["filter"] = tier_filter("Neighbourhood hub")

    # 8 connection sites: a double ring, built from three stacked
    # circles since MapLibre has no inner radius. Blue, white, blue.
    for suffix, ratio, colour in (
        ("", 1.0, palette.HUB_CONNECTION_COLOR),
        ("-mid", palette.HUB_CONNECTION_MID_RATIO, palette.HUB_DOT_STROKE),
        ("-core", palette.HUB_CONNECTION_CORE_RATIO,
         palette.HUB_CONNECTION_CORE_COLOR),
    ):
        paint = {
            "circle-color": colour,
            "circle-radius": _ramp(
                tuple(round(r * ratio, 2) for r in palette.HUB_CONNECTION_RADIUS),
                "hub_connection",
            ),
        }
        # Only the outer ring carries the white edge that lifts the mark
        # off the ground; an edge on the inner two would read as a fourth
        # and fifth ring.
        if not suffix:
            paint["circle-stroke-color"] = palette.HUB_DOT_STROKE
            paint["circle-stroke-width"] = palette.HUB_DOT_STROKE_WIDTH

        layers.append(_layer(f"hub-connection{suffix}", "hub_network",
                             "circle", paint, registry_id="hub_connection"))
        layers[-1]["filter"] = tier_filter("Connection hub")

    # The one chosen site, carrying the Kinesis mark
    layers.append(_layer("mobility-hub-selected", "hub_network", "symbol", {},
                         registry_id="hub_selected"))
    layers[-1]["layout"] = {
        "icon-image": palette.HUB_ICON,
        "icon-size": _ramp(palette.HUB_ICON_SIZE, "hub_selected"),
        "icon-allow-overlap": True,
        "icon-ignore-placement": True,
    }
    layers[-1]["filter"] = ["==", ["get", "hub_selected"], True]

    build_layers.sprites = sprites.manifest()

    return layers


def icon_sprites():
    """The icons the style needs, discovered while building layers."""
    build_layers()
    return build_layers.sprites


# --------------------------------------------------
# TypeScript emission
# --------------------------------------------------

def _colour_of(value):
    """
    A representative literal colour from a value that may be a paint
    expression. Scans forward so a match returns its first real case
    rather than its fallback, and skips fully transparent ramp stops.
    """
    if isinstance(value, str):
        if value.startswith(("#", "rgb")) and not value.endswith((", 0)", ",0)")):
            return value
        return None
    if isinstance(value, list):
        for item in value:
            found = _colour_of(item)
            if found:
                return found
    return None


def _fill_colour(fill):
    """
    The colour that stands for a fill in the menu.

    A `step` expression is a graduated scale, so its last colour is the
    top class — the one that reads as the layer's identity. Anything
    else (a `match` over categories, a literal) takes the first, since
    a match's last entry is only its fallback.
    """
    paint = fill["paint"].get("fill-color")

    if isinstance(paint, list) and paint and paint[0] == "step":
        return _colour_of(list(reversed(paint)))

    return _colour_of(paint)


def _swatch(parent_id, layers):
    """
    How to draw this layer in the menu, taken from the style itself so the
    legend cannot drift from the map.
    """
    mine = [l for l in layers if l["metadata"]["thessmap:parent"] == parent_id]

    # Prefer geometry belonging to the toggle itself over its detail
    # tiers, so Bike Lanes shows a lane and not a parking icon.
    direct = [l for l in mine if l["metadata"]["thessmap:spec"] == parent_id]
    candidates = direct or mine

    symbol = next((l for l in candidates if l["type"] == "symbol"), None)
    if symbol is not None:
        icon = symbol["layout"]["icon-image"]

        # Supplied artwork: the chip is drawn with lucide-react, which
        # cannot show a PNG, so it falls back to the nearest glyph.
        if isinstance(icon, str) and icon in RASTER_ICONS:
            return {"kind": "point", "color": palette.HUB_SWATCH_COLOR,
                    "icon": palette.HUB_SWATCH_ICON}

        # A match expression means the icon varies per feature; the menu
        # shows the fallback, which is the expression's last entry.
        sprite_id = icon if isinstance(icon, str) else icon[-1]

        # Emit the lucide name, not the sprite id: the menu draws with
        # lucide-react while the map draws rasters, and only the icon name
        # is common to both.
        sprite = next((sp for sp in icon_sprites() if sp["id"] == sprite_id), None)

        plate = next((l for l in mine if l["id"] == f"{symbol['id']}-plate"), None)
        return {
            "kind": "point",
            "color": _colour_of(plate["paint"]["circle-stroke-color"]) if plate else None,
            "icon": sprite["lucide"] if sprite else None,
        }

    fill = next((l for l in candidates if l["type"] == "fill"), None)
    if fill is not None:
        return {"kind": "area", "color": _fill_colour(fill)}

    # A raster carries no vector geometry to sample, so its swatch comes
    # from the top class of the ramp it was coloured with.
    raster = next((l for l in candidates if l["type"] == "raster"), None)
    if raster is not None:
        return {"kind": "area", "color": palette.POP_DENSITY_RAMP[-1]}

    line = next((l for l in candidates if l["type"] == "line"), None)
    if line is not None:
        return {
            "kind": "line",
            "color": _colour_of(line["paint"].get("line-color")),
            "dashed": "line-dasharray" in line["paint"],
        }

    circle = next((l for l in candidates if l["type"] == "circle"), None)
    if circle is not None:
        return {"kind": "point",
                "color": _colour_of(circle["paint"].get("circle-color")),
                "icon": None}

    heat = next((l for l in candidates if l["type"] == "heatmap"), None)
    if heat is not None:
        return {"kind": "area",
                "color": _colour_of(heat["paint"].get("heatmap-color"))}

    return None


def _menu():
    """The menu tree, with a swatch and zoom hint per entry."""
    layers = build_layers()

    def entry(spec, ids=None, label=None, full=None):
        """
        One menu row. `ids` lets several layers share a single switch:
        a mode's network and its nodes are usually wanted together, and
        two rows for one idea costs a line for little gain.
        """
        swatch = _swatch(spec.id, layers)
        if swatch is None:
            return None

        controlled = ids or [spec.id]
        zooms = [z for z in (_min_zoom_of(i) for i in controlled) if z is not None]

        return {
            "id": spec.id,
            "ids": controlled,
            "label": label or spec.menu_label,
            "fullLabel": full or spec.label,
            "show": spec.show,
            # The earliest zoom at which anything under this switch draws
            "minZoom": min(zooms) if len(zooms) == len(controlled) else None,
            "swatch": swatch,
        }

    tree = {}
    for theme, entries in registry.menu().items():
        rendered = []
        for item in entries:
            if item["kind"] == "layer":
                built = [entry(item["layer"])]
            else:
                # A mode group collapses to one switch over all its layers
                members = item["layers"]
                ids = [l.id for l in members]
                names = " and ".join(l.menu_label.lower() for l in members)
                built = [entry(members[0], ids=ids, label=item["label"],
                               full=f"{item['label']}: {names}")]

            built = [b for b in built if b is not None]

            # Water and buildings are still awaiting vector tiles, so they
            # have no style layers. A toggle that controls nothing is worse
            # than an absent one.
            if not built:
                continue

            rendered.append({
                "kind": item["kind"],
                "label": item["label"] if item["kind"] == "group"
                         else built[0]["label"],
                "layers": built,
            })
        tree[theme] = rendered
    return tree


BANNER = """// GENERATED by scripts/export_web_data.py — do not edit.
// Source of truth: src/thessmap/registry.py and palette.py
"""


def _ts(value):
    return json.dumps(value, ensure_ascii=False)


def write_layers_ts(path, verbose=True):
    """Emit the layer registry and MapLibre definitions as TypeScript."""

    themes = {key: label for key, label in registry.THEMES.items()}

    parents = [
        {
            "id": spec.id,
            "label": spec.label,
            "theme": spec.theme,
            "show": spec.show,
            "minZoom": _min_zoom_of(spec.id),
        }
        for spec in registry.PARENTS
        if _has_data(spec.id)
    ]

    sources = sorted(GEOJSON_SOURCES)

    lines = [
        BANNER,
        f"export type Theme = {' | '.join(_ts(t) for t in themes)};\n",
        "export interface ToggleLayer {",
        "  id: string;",
        "  label: string;",
        "  theme: Theme;",
        "  show: boolean;",
        "  /** Lowest zoom at which anything in this layer draws. */",
        "  minZoom: number | null;",
        "}\n",
        f"export const THEMES: Record<Theme, string> = {_ts(themes)};\n",
        f"export const TOGGLE_LAYERS: ToggleLayer[] = {_ts(parents)};\n",
        f"export const SOURCE_NAMES = {_ts(sources)} as const;\n",
        "export type SourceName = (typeof SOURCE_NAMES)[number];\n",
        f"export const MAP_LAYERS = {_ts(build_layers())} as const;\n",
        "export interface LegendBlock {",
        "  title: string;",
        "  kind: \"swatches\" | \"lines\" | \"gradient\" | \"icons\" | \"marks\";",
        "  /** Sidebar theme this block groups under. */",
        "  theme: Theme;",
        "  /** Shown only while this layer is drawn. Per-entry for lines. */",
        "  layer?: string;",
        "  /** Shown while any of these is drawn — for layers sharing a scale. */",
        "  anyOf?: string[];",
        "  entries?: {",
        "    label: string;",
        "    color?: string;",
        "    dashed?: boolean;",
        "    layer?: string;",
        "    /** lucide name, for kind \"icons\" and mark \"glyph\". */",
        "    icon?: string;",
        "    /** Which mark to draw, for kind \"marks\". */",
        "    mark?: \"double-ring\" | \"ring\" | \"dot\" | \"logo\";",
        "    /** Centre colour, for mark \"double-ring\". */",
        "    core?: string;",
        "  }[];",
        "  stops?: string[];",
        "  min?: string;",
        "  max?: string;",
        "  /** Appended to the block title, e.g. a unit of measure. */",
        "  unit?: string;",
        "}\n",
        f"export const LEGEND: Record<string, LegendBlock> = {_ts(_legend())};\n",
        "export interface MapConfig {",
        "  /** [west, south, east, north] — panning is clamped to this. */",
        "  bounds: [number, number, number, number];",
        "  minZoom: number;",
        "  maxZoom: number;",
        "  center: [number, number];",
        "}\n",
        f"export const MAP_CONFIG: MapConfig = {_ts(_map_config())};\n",
        "export interface IconSprite {",
        "  /** Registered with map.addImage() under this id. */",
        "  id: string;",
        "  /** lucide icon name, see lucide.dev */",
        "  lucide: string;",
        "  color: string;",
        "  size: number;",
        "}\n",
        f"export const ICON_SPRITES: IconSprite[] = {_ts(icon_sprites())};\n",
        "/** Only one layer per group may be on: they fill the same area. */",
        f"export const EXCLUSIVE_GROUPS: string[][] = {_ts(registry.EXCLUSIVE)};\n",
        "/** Property value -> display label, by property name. */",
        "export const VALUE_LABELS: Record<string, Record<string, string>> =",
        f"  {_ts({'LU_GROUP': palette.LANDUSE_LABELS})};\n",
        "/** Supplied artwork registered with addImage, by sprite id. */",
        f"export const RASTER_ICONS: Record<string, string> = {_ts(RASTER_ICONS)};\n",
        "export interface RasterSource {",
        "  /** PNG filename under public/data. */",
        "  url: string;",
        "  /** Four corners in EPSG:4326, clockwise from top-left. */",
        "  coordinates: [number, number][];",
        "}\n",
        "export const RASTER_SOURCES: Record<string, RasterSource> =",
        f"  {_ts(_raster_sources())};\n",
        "/** Always on and absent from the menu; the frontend forces these true. */",
        f"export const PINNED_LAYERS: string[] = {_ts(registry.PINNED)};\n",
        "/** {layer: zoom past which it switches itself off}. */",
        f"export const AUTO_HIDE: Record<string, number> = "
        f"{_ts(registry.AUTO_HIDE)};\n",
        "/** Fetched on first use, not at startup: too large to load eagerly. */",
        f"export const LAZY_SOURCES: string[] = {_ts(LAZY_SOURCES)};\n",
        "/** Badge colour for clustered sources, from palette.py. */",
        f"export const CLUSTER_COLOR = {_ts(palette.BIKE_CLUSTER_COLOR)};\n",
        "export interface ClusterConfig { radius: number; maxZoom: number }\n",
        "export const CLUSTERED_SOURCES: Record<string, ClusterConfig> =",
        f"  {_ts(CLUSTERED_SOURCES)};\n",
        "export interface Swatch {",
        "  kind: \"point\" | \"line\" | \"area\";",
        "  color: string | null;",
        "  /** lucide name, when the layer draws an icon. */",
        "  icon?: string | null;",
        "  dashed?: boolean;",
        "}\n",
        "export interface MenuLayer {",
        "  /** Primary layer, used for the swatch. */",
        "  id: string;",
        "  /** Every layer this one switch controls. */",
        "  ids: string[];",
        "  label: string;",
        "  fullLabel: string;",
        "  show: boolean;",
        "  minZoom: number | null;",
        "  swatch: Swatch;",
        "}\n",
        "export interface MenuEntry {",
        "  /** A standalone layer, or a mode holding a network and its nodes. */",
        "  kind: \"layer\" | \"group\";",
        "  label: string;",
        "  layers: MenuLayer[];",
        "}\n",
        f"export const MENU: Record<Theme, MenuEntry[]> = {_ts(_menu())};\n",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    if verbose:
        print(f"  {path.name}: {len(parents)} toggles, "
              f"{len(build_layers())} map layers")


def _has_data(parent_id):
    """Does any exported layer belong to this toggle?"""
    return any(
        layer["metadata"]["thessmap:parent"] == parent_id
        for layer in build_layers()
    )


def _min_zoom_of(parent_id):
    """The lowest zoom at which this toggle shows anything."""
    zooms = [
        layer.get("minzoom", 0)
        for layer in build_layers()
        if layer["metadata"]["thessmap:parent"] == parent_id
    ]
    if not zooms:
        return None
    lowest = min(zooms)
    return lowest or None


def _raster_sources():
    """
    Where each PNG belongs on the map, read from the source GeoTIFF.

    Only the extent is read, not the pixels, so this stays cheap and does
    not depend on the PNG having been rendered yet.
    """
    from . import rasterexport

    return {
        name: {
            "url": png,
            "coordinates": rasterexport.placement(config.RASTERS / f"{stem}.tif"),
        }
        for name, (stem, png) in RASTER_SOURCES.items()
    }


def _indicator_legend(indicator):
    """
    One row per Jenks class, labelled with its range.

    Ranges rather than bare class numbers: the whole point of Natural
    Breaks is that the class widths are uneven, so "462 - 4,000" tells
    the reader something "class 2" cannot.
    """
    from . import classify
    from .data import MapData

    values = MapData().municipalities[indicator.column].values
    ranges = classify.legend_ranges(values, palette.POP_DENSITY_CLASSES)

    def figure(value):
        return f"{value:,.{indicator.decimals}f}"

    def band(low, high):
        # With 14 values and 5 classes, Jenks can isolate a single
        # municipality at either end. "19.4 - 19.4" reads as a bug, so a
        # one-value class shows its value instead of a null range.
        if figure(low) == figure(high):
            return figure(low)
        return f"{figure(low)} \u2013 {figure(high)}"

    return [
        {"label": band(low, high), "color": colour}
        for (low, high), colour in zip(ranges, palette.INDICATOR_RAMP)
    ]


# Amenity legend cards. Each names the icons one toggle draws, so the
# six grey symbol layers stop relying on the reader inferring a glyph.
#
# (layer id, card title, {category: lucide})
AMENITY_KEYS = [
    ("education", "Education", palette.EDUCATION_ICONS),
    ("culture", "Culture", palette.CULTURE_ICONS),
    ("health", "Health", palette.HEALTH_ICONS),
    ("sport", "Sport", palette.SPORT_ICONS),
    ("public_services", "Public services", palette.PUBLIC_SERVICE_ICONS),
    ("commercial", "Commercial", palette.COMMERCIAL_ICONS),
    ("playgrounds", "Playgrounds", palette.PLAYGROUND_ICONS),
]


def _amenity_legend():
    """
    One card per amenity toggle, listing its icons.

    Deduplicated by icon, keeping the first category that claims it: two
    categories can legitimately share a glyph — "Hospital" and "Hospital
    with emergency", "Government office" and "Public service" — and a
    legend showing one mark twice teaches nothing and looks like a bug.
    """

    blocks = {}

    for layer_id, title, icons in AMENITY_KEYS:
        entries, seen = [], set()

        for category, lucide in icons.items():
            if lucide in seen:
                continue
            seen.add(lucide)
            entries.append({
                "label": palette.AMENITY_LEGEND_LABELS.get(lucide, category),
                "icon": lucide,
                "color": palette.DESTINATION_INK,
            })

        blocks[f"amenity_{layer_id}"] = {
            "title": title,
            "kind": "icons",
            "layer": layer_id,
            "entries": entries,
        }

    return blocks


def _all_indicators():
    """The indicators with a legend card, which is the mapped ones."""
    from .indicators import MAPPED
    return MAPPED


def _legend():
    """
    Legend blocks, grouped by category and each tied to the layer that
    justifies it. A block only renders when its layer is drawn, so the
    legend never explains a symbol that is not on screen.

    Tree height is a gradient rather than six rows: it is one hue varying
    by luminance, which is a scale, and a scale reads as a bar.

    Bus service intensity is deliberately absent. Five grey dots between
    8 and 16 px are barely distinguishable at legend size, and the circles
    read as relative weight on the map without being enumerated.

    Every block carries the theme of the layer it explains, so the legend
    groups under the same headings as the sidebar rather than presenting
    fourteen cards as one undifferentiated stack.
    """

    return _themed({
        "zones": {
            "title": "Urban zones",
            "kind": "swatches",
            "layer": "zones",
            "entries": [
                {"label": zone, "color": style["fillColor"]}
                for zone, style in palette.ZONE_STYLES.items()
            ],
        },
        # Split from the network block below. It used to sit at the top of
        # it, which was harmless as one flat stack and wrong the moment
        # the legend grouped by theme: a river is not transport.
        "water": {
            "title": "Water",
            "kind": "lines",
            "entries": [
                {"label": "Rivers & canals", "color": palette.WATER_LINE_COLOR,
                 "dashed": False, "layer": "water"},
            ],
        },
        "transport": {
            "title": "Networks",
            "kind": "lines",
            "theme": "transport",
            "entries": [
                {"label": "Pedestrian network", "color": palette.WALKWAY_COLOR,
                 "dashed": True, "layer": "walkways"},
                {"label": "Bus network", "color": palette.BUS_LANE_COLOR,
                 "dashed": False, "layer": "bus_lanes"},
                {"label": "Metro", "color": palette.METRO_LINE_COLOR,
                 "dashed": True, "layer": "metro_line"},
                {"label": "Ferry", "color": palette.FERRY_ROUTE_COLOR,
                 "dashed": True, "layer": "ferry_routes"},
                {"label": "Bike routes", "color": palette.BIKE_COLOR,
                 "dashed": False, "layer": "bike_lanes"},
                {"label": "Bike, proposed", "color": palette.BIKE_COLOR,
                 "dashed": True, "layer": "bike_lanes_proposed"},
            ],
        },
        # The five point layers the legend used to skip. They are the
        # marks a reader is least able to infer: four of the bus stop
        # symbols are geometric rather than pictorial, and nothing on
        # screen says a half-filled circle is an interchange.
        "nodes": {
            "title": "Stops & stations",
            "kind": "icons",
            "theme": "transport",
            "entries": [
                *(
                    {"label": category, "icon": sprite,
                     "color": palette.BUS_STOP_SYMBOL_COLOR,
                     "layer": "bus_stops"}
                    for category, sprite in palette.BUS_STOP_ICONS.items()
                ),
                {"label": "Metro station", "icon": palette.ICON_METRO_STATION,
                 "color": palette.METRO_SYMBOL_COLOR, "layer": "metro_stations"},
                {"label": "Ferry terminal", "icon": palette.ICON_FERRY_TERMINAL,
                 "color": palette.FERRY_TERMINAL_COLOR,
                 "layer": "ferry_terminals"},
            ],
        },
        "facilities": {
            "title": "Parking & taxi",
            "kind": "icons",
            "theme": "services",
            "entries": [
                {"label": "Parking", "icon": palette.ICON_PARKING,
                 "color": palette.PARKING_COLOR, "layer": "parking"},
                {"label": "Taxi rank", "icon": palette.ICON_TAXI,
                 "color": palette.TAXI_COLOR, "layer": "taxi"},
            ],
        },
        "buildings": {
            "title": "Building height",
            "kind": "swatches",
            "layer": "buildings",
            "unit": "roof height",
            "entries": [
                {"label": label, "color": colour}
                for label, colour in zip(palette.BUILDING_HEIGHT_LABELS,
                                         palette.BUILDING_HEIGHT_RAMP)
            ],
        },
        # Drawn as the marks themselves rather than as colour chips: the
        # three tiers differ by structure and size, not only by hue, so a
        # row of squares would have described none of what is on screen.
        "hubs": {
            "title": "Hub network",
            "kind": "marks",
            "layer": "mobility_hubs",
            "entries": [
                {"label": "Connection hub", "mark": "double-ring",
                 "color": palette.HUB_CONNECTION_COLOR,
                 "core": palette.HUB_CONNECTION_CORE_COLOR},
                {"label": "Neighbourhood hub", "mark": "ring",
                 "color": palette.HUB_NEIGHBOURHOOD_COLOR},
                {"label": "Street-scale hub", "mark": "dot",
                 "color": palette.HUB_STREET_COLOR},
                {"label": "Kinesis City Hub", "mark": "logo",
                 "color": palette.HUB_SWATCH_COLOR},
            ],
        },
        "landuse": {
            "title": "Land use",
            "kind": "swatches",
            "layer": "landuse",
            "entries": [
                {"label": palette.LANDUSE_LABELS[group], "color": colour}
                for group, colour in palette.LANDUSE_COLORS.items()
            ],
        },

        # Amenity icon keys, before the indicators: they are the layers a
        # reader most needs a key for, being six grey symbol sets that
        # differ only by glyph.
        **_amenity_legend(),

        # One block per indicator. They are mutually exclusive, so at most
        # one of these is ever on screen. The 100 m grid shares the
        # density block, being classified with the same breaks from the
        # same ramp — a second card would have repeated it row for row.
        **{
            f"indicator_{indicator.id}": {
                # Short: the card is 10.5rem wide, and the full name
                # would wrap to three lines
                "title": "Population density",
                "kind": "swatches",
                "anyOf": ([indicator.layer_id, "pop_density_100m"]
                          if indicator.column == "POP_DENS"
                          else [indicator.layer_id]),
                "unit": indicator.unit,
                "entries": _indicator_legend(indicator),
            }
            for indicator in _all_indicators()
        },

        "trees": {
            "title": "Tree canopy",
            "kind": "gradient",
            "layer": "trees",
            "stops": [colour for colour, _radius in palette.TREE_CLASSES.values()
                      if colour.startswith("#") and colour != palette.GREY_300],
            "min": _tree_range()[0],
            "max": _tree_range()[1],
        },
    })


def _themed(blocks):
    """
    Tags each block with the theme of the layer it explains.

    Derived from the registry rather than written out per block: a layer
    that moves between themes — buildings did, land use did — would
    otherwise leave the legend grouping it under the old heading with
    nothing to catch it.

    A block that names no single layer (the transport key, whose rows
    span water, walkways and three modes) sets "theme" itself and is
    left alone.
    """

    theme_of = {layer.id: layer.theme for layer in registry.LAYERS}

    for block in blocks.values():
        if block.get("theme"):
            continue

        owner = block.get("layer") or (block.get("anyOf") or [None])[0]
        if owner is None:
            entries = block.get("entries") or []
            owner = next((e["layer"] for e in entries if e.get("layer")), None)

        if owner not in theme_of:
            raise KeyError(f"legend block {block['title']!r} names no known layer")

        block["theme"] = theme_of[owner]

    return blocks


def _tree_range():
    """Outer bounds of the height classes, for the gradient's end labels."""
    numeric = [k for k in palette.TREE_CLASSES if k[0].isdigit()]
    lowest = numeric[0].split(" - ")[0]
    highest = numeric[-1].split(" - ")[-1]
    return f"{lowest} m", f"{highest} m"


def _map_config():
    """Viewport limits, so the map never loads tiles we have no data for."""

    west, south, east, north = config.MAP_BOUNDS
    latitude, longitude = config.MAP_CENTER

    return {
        "bounds": [west, south, east, north],
        "minZoom": config.MIN_ZOOM,
        "maxZoom": config.MAX_ZOOM,
        "center": [longitude, latitude],
    }


def basemap_style():
    """The Positron raster basemap as a MapLibre style."""

    return {
        "version": 8,
        "sources": {
            "positron": {
                "type": "raster",
                "tiles": [config.BASEMAP_TILES.replace("{s}", "a")],
                "tileSize": 256,
                "attribution": config.BASEMAP_ATTRIBUTION,
            }
        },
        "layers": [
            {"id": "basemap", "type": "raster", "source": "positron"}
        ],
    }
