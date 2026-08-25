"""The layer registry: every layer on the map, declared once.

This is the single source of truth for layer identity, menu grouping and
zoom thresholds. Rendering code reads it; nothing hard-codes a zoom level.

Two kinds of entry:

* A **parent** layer is what the user toggles. It appears in the layer
  menu and holds no geometry of its own.
* A **detail** layer names a parent and a zoom range. It is hidden from
  the menu and switched on automatically while its parent is enabled and
  the current zoom sits inside [min_zoom, max_zoom).

`max_zoom` is exclusive; None means unbounded on that side.

Point-symbol thresholds come from a measured viewport-density audit, not
from feature counts or city-wide median spacing. A layer can have a
comfortable median while packing hundreds of points into the historic
centre, so each layer is judged on two numbers per zoom:

  overlap%  share of symbols whose nearest neighbour is closer than one
            symbol width (global, so no windowing bias)
  n/screen  symbols in the p90 populated 1024x768 viewport

The threshold is the first zoom where overlap <= 12% and n/screen <= 160.

One deliberate exception: trees stay at 18 with ~620 dots per screen.
The per-screen budget is calibrated for POI icons that must be read
individually; trees are a 6 px texture layer covering under 2% of the
viewport, where density is the information.

When the MapLibre migration happens this module generates the style
JSON's minzoom/maxzoom directly, so the thresholds never get duplicated
between Python and TypeScript.
"""

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
    # Mode grouping for the menu. A network and its nodes stay separately
    # switchable — they answer different questions — but shown together so
    # the relationship is legible.
    group: str | None = None
    # Shorter label used when the group name already carries the mode
    short: str | None = None
    # Always drawn, and absent from the menu. For ground the map is
    # simply made of, where a switch implies a choice nobody wants to
    # make.
    pinned: bool = False
    # Switches itself off once the map is zoomed in past this, and back
    # on when it is zoomed back out. For an overview wash that answers a
    # question only the overview asks: leaving it on underneath the city
    # tints every street once the reader has moved past caring which
    # frame they are in. Cleared for good the moment the reader works
    # the switch themselves.
    auto_hide_above: int | None = None

    @property
    def menu_label(self):
        return self.short or self.label

    @property
    def is_detail(self):
        return self.parent is not None


# Mode groups inside a theme: a network and its nodes belong together
GROUPS = {
    "metro": "Metro",
    "bus": "Bus",
    "bike": "Bike",
    "ferry": "Ferry",
}


# Menu groupings, in display order
THEMES = {
    "zones": "Zones",
    "environment": "Environment",
    # Natural substrate above, the city itself below. Buildings sat under
    # "environment" before, where a building is plainly not an
    # environmental feature, and land use had a whole section to itself
    # for a single row.
    "fabric": "Urban fabric",
    "transport": "Transport",
    # Networks above, facilities here. Parking, taxi and charging are not
    # modes — they are points where a vehicle is left, taken or serviced,
    # and listing them under Transport put a taxi rank beside the metro
    # as though it were a way of getting across the city.
    #
    # They are also, together with bike parking and rental, exactly the
    # components a mobility hub is assembled from, so the grouping mirrors
    # what the project is trying to site.
    "services": "Mobility services",
    "amenities": "Amenities",
    "population": "Population density",
}


# Order matters: it sets both draw order and the order of the layer menu.
LAYERS = [
    # ---------------- zones ----------------
    # Closes on the first zoom in from the opening view, which is why the
    # threshold is the opening zoom itself rather than a number picked
    # near it. The frame answers "what am I looking at" at the overview;
    # one step in the reader has asked it and moved on, and the wash is
    # left tinting every street they zoomed in to see.
    LayerSpec("zones", "Urban / Metropolitan / Regional Frame", "zones",
              show=True, auto_hide_above=config.MIN_ZOOM),

    # ---------------- environment ----------------

    # The whole network from the minimum zoom, rivers and streams alike.
    #
    # Streams and drains were held back to 12 on the assumption that
    # 1,931 of them would be a mesh at the overview. Looking at it, they
    # are not: at z9 the minor lines are half a pixel of pale blue, and
    # what they draw is the drainage pattern of the plain and the
    # tributaries off Chortiatis — which is the most informative thing
    # this layer has to say and exactly what was missing. Holding them
    # back showed 440 of 3,125 lines and made the network look sparse.
    #
    # The two tiers remain, but as a weight hierarchy rather than a
    # visibility one: a river is heavier than a ditch at every zoom.
    LayerSpec("water", "Rivers & Lakes", "environment", show=True),
    # The three named lakes. Folded in rather than given their own
    # switch: 96% of their area is already in the water bodies below —
    # Volvi and Koroneia appear in both files — so two toggles drew the
    # same blue twice. What this tier uniquely adds is Pikrolimni, and
    # the labelling offsets the Folium map uses.
    LayerSpec("lakes", "Named Lakes", "environment", parent="water"),
    LayerSpec("water_major", "Rivers & Canals", "environment",
              parent="water"),
    LayerSpec("water_minor", "Streams & Drains", "environment",
              parent="water"),
    # Weirs, dams, waterfalls and lock gates. Street-scale features on a
    # regional network, so they wait until the network they sit on is
    # drawn at full width.
    LayerSpec("water_structures", "Weirs, Dams & Waterfalls", "environment",
              parent="water", min_zoom=15),


    # ---------------- urban fabric ----------------
    # What a place is for, and how much of it there is. Both are area
    # fills over the same ground, so they belong together — and they
    # compete with each other rather than with the water or the canopy.
    #
    # Land use from 11: at 9 the study area is 14,456 parcels averaging
    # under a pixel, which renders as noise rather than as pattern. 11 is
    # where a neighbourhood-sized block of one category becomes a shape.
    LayerSpec("landuse", "Land Use", "fabric", min_zoom=11),

    # 192,565 surveyed footprints coloured by roof height. From 12 as
    # specified: individual buildings are sub-pixel there — a 38 m pixel
    # against a median footprint of 91 m2 — but the aggregate reads as a
    # height texture of the city, which is worth having. Footprints
    # resolve individually from about 15.
    LayerSpec("buildings", "Buildings by Height", "fabric", min_zoom=12),

    # ---------------- transport ----------------
    # Line networks are tiered by the scale of the thing, not by feature
    # count. Metro, ferry and now the bus network are region-scale and
    # draw from the minimum zoom; cycling is city-scale and waits.
    #
    # Bus was paired with bike at 12 on the grounds that both are street
    # infrastructure. Measured, they are not the same kind of thing at
    # all: the bus network is 1,071 km spanning 100 km of territory,
    # while cycling is 136 km spanning the city. Bus lanes ARE the
    # regional transit armature — leaving them out of the overview left
    # the metro line running through an otherwise empty region.
    LayerSpec("bus_lanes", "Bus Lanes", "transport",
              group="bus", short="Lanes"),

    LayerSpec("bike_lanes", "Bike Lanes", "transport", min_zoom=12,
              group="bike", short="Lanes, parking, rental"),
    # Secondary lanes and the dense parking stands are street detail
    LayerSpec("bike_detail", "Bike Details", "transport",
              parent="bike_lanes", min_zoom=16),
    # Only 9 rental stations, ~490 m apart, so they read far earlier than
    # the 62 parking stands they used to be grouped with
    LayerSpec("bike_rental_hint", "Bike Rental Hint", "transport",
              parent="bike_lanes", min_zoom=12, max_zoom=13),
    LayerSpec("bike_rental_symbols", "Bike Rental", "transport",
              parent="bike_lanes", min_zoom=13),
    # Web: parking and rental as one clustered layer, the way Folium's
    # MarkerCluster showed them. Clustering aggregates dense areas instead
    # of hiding them, so this appears earlier than the separate symbol
    # layers the density audit had to hold back to z13 and z17.
    LayerSpec("bike_points", "Bike Parking & Rental", "transport",
              parent="bike_lanes", min_zoom=14),
    LayerSpec("bike_parking_hint", "Bike Parking Hint", "transport",
              parent="bike_lanes", min_zoom=15, max_zoom=17),
    # Parking stands cluster hard: 35% of symbols still collide at z14
    LayerSpec("bike_parking_symbols", "Bike Parking", "transport",
              parent="bike_lanes", min_zoom=17),

    # In the bike group, so the built and proposed networks share one
    # switch — a mode group collapses to a single control over all its
    # layers. The distinction between built and planned is carried by the
    # dash pattern and by its own legend row rather than by a second
    # toggle, which is enough: a reader comparing them wants both on at
    # once, and two switches made that the default-off case.
    LayerSpec("bike_lanes_proposed", "Proposed Bike Lanes", "transport",
              min_zoom=12, group="bike", short="Proposed"),

    LayerSpec("bus_stops", "Bus Stops", "transport",
              group="bus", short="Stops"),
    # Three tiers, handing over cleanly:
    #
    #   12  a plain dot, arriving with the lanes. Lanes at 9 and stops at
    #       13 split one system across four zooms — you could see where
    #       the buses run long before you could see where they stop.
    #   14  the service-intensity halo, sized by how many lines call
    #   15  the type symbol, replacing the dot
    #
    # The dot used to end at 16 while the symbol began at 17, leaving a
    # zoom where a stop showed a halo and nothing in the middle of it.
    #
    # The symbol moves from 17 to 15 to land with the amenity icons.
    # 30% of stop symbols overlap at 16 and more at 15, so this is a
    # deliberate trade: one zoom where every category of thing on the map
    # becomes readable at once is worth more than clean spacing on one
    # layer, and the halo underneath still separates the stops.
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
    # Web: one symbol layer with a zoom-interpolated size, replacing the
    # two fixed size bands Folium needed. 26 features at the top of the
    # transport hierarchy, so they appear close behind the line.
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
    # All six terminals kept, so z12 rather than z11: with the harbour
    # berths present, 50% of symbols collide at 11 and none at 12.
    LayerSpec("ferry_terminals_symbols", "Ferry Terminals Symbols", "transport",
              parent="ferry_terminals", min_zoom=12),

    # Footways, pedestrian streets, paths and hiking routes as one dashed
    # grey line. From 13: 6,136 segments over the study area is a wash at
    # 11 and a street pattern at 13, where a 19 m pixel resolves one way.
    LayerSpec("walkways", "Pedestrian Network", "transport", min_zoom=13),

    LayerSpec("parking", "Parking Places", "services"),
    LayerSpec("parking_hint", "Parking Hint", "services",
              parent="parking", min_zoom=14, max_zoom=15),
    LayerSpec("parking_polygons", "Parking Places Polygons", "services",
              parent="parking", min_zoom=15),
    # 15, with every other icon on the map. Held at 16 before, which put
    # a parking sign a zoom behind the school beside it for no reason a
    # reader could see.
    LayerSpec("parking_symbols", "Parking Places Symbols", "services",
              parent="parking", min_zoom=15),

    # The candidate hub network, on one switch, revealed in two stages
    # that follow the cycling layer exactly.
    #
    #   z12  the bike lanes arrive, and every hub is one plain dot: the
    #        shape of the network, before any question of rank
    #   z14  the bike icons arrive, and the dots resolve into their
    #        tiers — double ring, ring, dot — with the Kinesis mark on
    #        the chosen site
    #
    # Tying it to the bike network is deliberate. A hub is read against
    # the cycling infrastructure around it, so the two should thicken
    # together rather than each on its own schedule.
    #
    # Every tier is drawn at every zoom above 14. An earlier version
    # staggered them by rank — connection at 12, neighbourhood at 13,
    # street at 15 — which meant the network was never visible as a
    # network. Rank is carried by the marks; it does not also need to be
    # carried by absence.
    LayerSpec("mobility_hubs", "Mobility Hubs", "services", show=True),
    LayerSpec("hub_overview", "Hub Sites", "services",
              parent="mobility_hubs", min_zoom=12, max_zoom=14),
    LayerSpec("hub_connection", "Connection Hubs", "services",
              parent="mobility_hubs", min_zoom=14),
    LayerSpec("hub_neighbourhood", "Neighbourhood Hubs", "services",
              parent="mobility_hubs", min_zoom=14),
    LayerSpec("hub_street", "Street-scale Hubs", "services",
              parent="mobility_hubs", min_zoom=14),
    # The one chosen site, carrying the mark, from the minimum zoom: it
    # is the answer the whole project is working toward, not a candidate.
    LayerSpec("hub_selected", "Kinesis City Hub", "services",
              parent="mobility_hubs", min_zoom=14),

    LayerSpec("taxi", "Taxi Spots", "services"),
    LayerSpec("taxi_hint", "Taxi Hint", "services",
              parent="taxi", min_zoom=14, max_zoom=15),
    # Ranks cluster at squares and stations, so spacing argues for 16 —
    # but 15 is where every icon on this map arrives, and a taxi rank
    # appearing a zoom after the supermarket next to it reads as a fault.
    LayerSpec("taxi_symbols", "Taxi Spots Symbols", "services",
              parent="taxi", min_zoom=15),

    # ---------------- amenities ----------------
    LayerSpec("trees", "Trees", "environment"),
    # Canopy density as a heatmap, so a tree-lined street differs from a
    # bare one long before individual trees are legible
    LayerSpec("trees_density", "Tree Density", "environment",
              parent="trees", min_zoom=13, max_zoom=17),
    # Stippled points that grow into the full symbols
    LayerSpec("trees_texture", "Tree Texture", "environment",
              parent="trees", min_zoom=16),
    LayerSpec("trees_symbols", "Trees Symbols", "environment",
              parent="trees", min_zoom=18),

    LayerSpec("education", "Education", "amenities"),
    LayerSpec("education_hint", "Education Hint", "amenities",
              parent="education", min_zoom=14, max_zoom=15),
    LayerSpec("education_polygons", "Education Polygons", "amenities",
              parent="education", min_zoom=15),
    # Well dispersed — only 11% collide at z15, so they join their polygons
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

    # Section 3B destinations, all points-only, all at 15 with a hint
    # from 13 — the same tiers as education and culture.
    #
    # Uniform on purpose, against the density audit rather than with it.
    # Overlap at z15 runs commercial 10%, culture 12%, public services
    # 12%, health 17%, education 22%, sport 36%, so on a 12% budget only
    # three of the six actually qualify. Holding sport back to 16 while
    # waiving education at 22% enforced the rule in one place and not the
    # other, and a sibling layer behaving differently for reasons a
    # reader cannot see registers as a bug, not as cartography. Sport is
    # the crowded case — 731 pitches, several per sports complex, 90% of
    # them unnamed — so the pile-up at 15 is real and accepted.
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

    # The playground AREAS are part of the pinned green ground; these are
    # the points, which say which patch of green is a playground. They
    # belong with the other destination symbols, on their own switch.
    LayerSpec("playgrounds", "Playgrounds", "amenities"),
    LayerSpec("playground_hint", "Playground Hint", "amenities",
              parent="playgrounds", min_zoom=14, max_zoom=15),
    LayerSpec("playground_symbols", "Playground Symbols", "amenities",
              parent="playgrounds", min_zoom=15),
    LayerSpec("commercial_hint", "Commercial Hint", "amenities",
              parent="commercial", min_zoom=14, max_zoom=15),
    LayerSpec("commercial_symbols", "Commercial Symbols", "amenities",
              parent="commercial", min_zoom=15),

    # ---------------- public open space ----------------
    # Parks, green space, recreational space, forest and playground areas
    # in one pinned layer: always drawn, never listed, and from the
    # minimum zoom. This is ground the map is made of — the shape of
    # where the city is not built — so it is there before anything is
    # switched on, the way the coastline is.
    #
    # No popup either: these are a backdrop, and a click landing on a
    # park instead of the thing drawn over it is an interruption, not
    # information.
    LayerSpec("green_spaces", "Green & Open Space", "environment",
              show=True, pinned=True),

    # Paved civic space, same treatment. It keeps its own stone colour
    # because it is not planted.
    LayerSpec("squares", "Squares", "environment", show=True, pinned=True),

]


# ---------------- population ----------------
# Section 2: one choropleth per socio-demographic indicator, over the 14
# municipalities, then the 100 m grid. Coarse to fine, so the list reads
# in the order the brief describes: municipality level for the overall
# picture, the grid for where people actually are.
#
# Nothing here is zoom-tiered. A choropleth is not progressive detail —
# it answers one question at every scale, and hiding it below some zoom
# would just make the layer look broken. Fourteen polygons and one PNG
# cost nothing to keep alive across the whole range.
def _population_layers():
    from .indicators import MAPPED

    density, *rest = MAPPED

    # The 100 m grid sits directly under the municipal density it refines,
    # so the two resolutions of one measure read as a pair rather than
    # bracketing four unrelated indicators.
    return [
        LayerSpec(density.layer_id, f"{density.label} (ELSTAT 2021)",
                  "population", short=density.short),
        # The raster is not clickable, so this label only ever appears as
        # a tooltip and in the active-layer chip — room enough to say
        # where it came from, which is not the same source as above.
        LayerSpec("pop_density_100m",
                  "Population Density \u2013 100 m (GHSL 2020)",
                  "population", short="100 m grid"),
    ] + [
        LayerSpec(indicator.layer_id, indicator.label, "population",
                  short=indicator.short)
        for indicator in rest
    ]


LAYERS += _population_layers()


# Groups within which only one layer may be on at a time.
#
# Six choropleths, a raster and the zone wash all fill the same
# footprint, so switching one on has to switch the others off. Otherwise
# whichever is drawn last silently wins while the sidebar claims two
# contradictory things are visible. Zones belongs in the group for the
# same reason as the rest: it is an area fill over the same polygons,
# and "Urban / Metropolitan / Regional" is itself a classification of
# them.
EXCLUSIVE = [
    ["zones"] + [spec.id for spec in LAYERS if spec.theme == "population"],
]


SPEC = {layer.id: layer for layer in LAYERS}

PARENTS = [layer for layer in LAYERS if not layer.is_detail]

# Always on, never offered. The frontend forces these true so a shared
# URL cannot switch off the ground the map is made of.
PINNED = [layer.id for layer in LAYERS if layer.pinned]

# {layer id: zoom past which it closes itself}
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


def by_theme():
    """Parent layers grouped by theme, for building a menu."""
    return {
        theme: [layer for layer in PARENTS if layer.theme == theme]
        for theme in THEMES
    }


def menu():
    """
    The menu tree: theme -> ordered entries, where an entry is either a
    standalone layer or a mode group holding several.
    """
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
