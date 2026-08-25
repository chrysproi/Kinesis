"""Every colour and size decision on the map.

Kept apart from layer logic so a restyle never touches rendering code.
When the MapLibre migration happens, this module becomes the input to
the generated style JSON.
"""

# --------------------------------------------------
# Shared colours
# --------------------------------------------------
# Used by more than one layer, so a change stays consistent.

# Monochromatic base, with chroma reserved for marks that carry meaning:
# pink for transit, orange for cycling, green for canopy, blue for water
# and for parking (its signage convention), and the three zone hues.
# Everything without a reason to be coloured is greyscale — ferry, taxi,
# buildings, amenity areas — so a saturated mark always signifies.

# Greyscale ladder, darkening inward
GREY_100 = "#F1F3F5"
GREY_200 = "#E9ECEF"
GREY_300 = "#DEE2E6"
GREY_400 = "#ADB5BD"
GREY_600 = "#868E96"
GREY_700 = "#495057"
GREY_900 = "#212529"

INK = "#000000"             # metro: the one true black
FERRY_INK = GREY_700        # a minor mode, so neutral rather than accented
SYMBOL_GREY = GREY_600      # education symbols
CULTURE_INK = GREY_700      # culture symbols and walls, a step darker
PT_PINK = "#FF0055"         # stops and their symbols, at full strength
# A lighter pink for the lane network and the service halos. Folium had two
# pinks for a reason: the lane is context for the stop, so it must not read
# as strongly as the stop sitting on it. Collapsing them to one colour made
# 5,507 lane segments compete with 1,798 stops.
# Lightened again, from #FF5C8D. With 5,507 lane segments the network is
# the largest coloured thing on the map, and it was reading as the
# subject rather than as the context its stops sit on.
PT_PINK_SOFT = "#FF8FB2"
WATER_FILL = "#E7F5FF"      # light and airy, never competing with transit
WATER_EDGE = "#A5D8FF"

# --------------------------------------------------
# Zones
# --------------------------------------------------

# The three zones keep their hues. They are the organising idea of the
# whole atlas, and at the overview zoom they *are* the foreground — three
# greys eight units apart could not be told apart there, and the legend
# chips went white on white. They recede on their own account: ZONE_FILL_FADE
# drops the fill to 6% by z16, so they never compete with street detail.
ZONE_STYLES = {
    "Urban": {"fillColor": "#f8c1c1", "color": "#ff0000", "fillOpacity": 0.65},
    "Metropolitan": {"fillColor": "#c7dcf3", "color": "#2f75c8", "fillOpacity": 0.55},
    "Regional": {"fillColor": "#c8efd2", "color": "#2f9e5b", "fillOpacity": 0.55},
}

DEFAULT_ZONE_STYLE = {
    "fillColor": "#eeeeee",
    "color": "#999999",
    "fillOpacity": 0.4,
}

# The zone fill is regional context, not foreground. It reads at full
# strength when the whole study area is in view and fades out as street
# detail takes over, otherwise every other layer sits on flat pink.
# (zoom, opacity multiplier)
ZONE_FILL_FADE = [(9, 1.0), (13, 0.45), (16, 0.10)]

# Dissolved outline weight per zone, heavier as the zone narrows
ZONE_OUTLINE_WEIGHTS = {
    "Regional": 1.4,
    "Metropolitan": 1.5,
    "Urban": 1.7,
}

# --------------------------------------------------
# Water and buildings
# --------------------------------------------------

WATER_LINE_COLOR = "#74C0FC"

# Two weights over one colour. A river is a feature of the region and
# draws from the minimum zoom; a field drain is street detail and waits.
# Same hue for both — they are the same thing at different scale, and a
# second blue would have implied otherwise.
WATER_MAJOR_WIDTH = (1.2, 3.2)
WATER_MINOR_WIDTH = (0.5, 1.6)
WATER_LINE_OPACITY = 0.85

# Water bodies: the lake fill, reused so a reservoir and a lake match
WATER_BODY_FILL_OPACITY = 0.75

# Weirs, dams, waterfalls and lock gates — 81 of them, and the only thing
# the third water file uniquely contributes. Small dots rather than an
# icon per type: at this count a five-glyph set would be more legend than
# information, and the popup names the structure.
WATER_STRUCTURE_RADIUS = 2.6
WATER_STRUCTURE_COLOR = "#3B8FD4"
WATER_STRUCTURE_STROKE = "#ffffff"
LAKE_LABEL_COLOR = GREY_700

BUILDING_FILL = GREY_200
BUILDING_EDGE = GREY_400

# Labels sit clear of the lake outline
LAKE_LABEL_OFFSETS = {
    "Λίμνη Βόλβη": (0.015, -0.080),
    "Λίμνη Κορώνεια": (0.010, -0.03),
    "Λίμνη Πικρολίμνη": (0.006, -0.004),
}

# --------------------------------------------------
# Bike
# --------------------------------------------------

# Burnt orange, and deliberately the only occupant of its hue. Bike lanes
# run along exactly the streets that carry street trees, so a green lane
# sat invisibly on the canopy wash.
#
# Vibrant, and a shade deeper than the original #FF9100. That brighter
# orange was fine alone but not with the bus network on: 1,798 stop halos
# at 0.35 opacity put a wall of pale pink across the centre, and a light
# orange on it differed in hue but barely in value — the eye reads value
# first. Going the other way to #E8590C fixed the contrast and lost the
# colour, reading brown against the black metro line. #FF7300 keeps full
# chroma and buys the value back.
BIKE_COLOR = "#FF7300"

# Proposed lanes take the same orange — they are the same network, just
# not built yet — and are told apart by dash rather than by hue. A second
# colour would have implied a second kind of infrastructure.
#
# A long dash with a wide gap, heavier than the built lanes: a planned
# corridor reads as a route being drawn rather than as a minor lane. The
# secondary lanes are already dashed at (4, 5) and 1.0-2.0 px, so the
# pattern and the weight both have to separate from those.
BIKE_PROPOSED_WIDTH = (2.0, 3.6)
BIKE_PROPOSED_DASH = (9, 6)
BIKE_PROPOSED_OPACITY = 0.9
# Matched to the lanes, and better under white numerals than the old
# lighter orange was.
BIKE_CLUSTER_COLOR = "#FF7300"
PRIMARY_BIKE_WEIGHT = 1.2
SECONDARY_BIKE_WEIGHT = 0.8
SECONDARY_BIKE_DASH = "4,5"
BIKE_SYMBOL_SIZE = 22
BIKE_ICON_SIZE = 20

# --------------------------------------------------
# Bus
# --------------------------------------------------

BUS_STOP_SIMPLE_COLOR = PT_PINK
BUS_STOP_OUTER_COLOR = PT_PINK_SOFT
BUS_STOP_SYMBOL_COLOR = PT_PINK
BUS_LANE_COLOR = PT_PINK_SOFT

# Folium's opacities, which set the hierarchy within the layer:
# stop reads over halo reads over lane.
BUS_LANE_OPACITY = 0.85
BUS_STOP_DOT_OPACITY = 0.9
# Dropped from 0.35. At 1,798 stops the halos overlapped into a
# continuous pale pink field across the centre, and every warm layer —
# bike above all — had to fight it. The halo still reads as service
# weight; it just stops being the ground.
BUS_STOP_HALO_OPACITY = 0.22

# Outer circle radius by number of lines served: (max_lines, radius)
BUS_STOP_OUTER_RADII = [(0, 8), (1, 9), (3, 11), (6, 13)]
BUS_STOP_MAX_RADIUS = 16

# --------------------------------------------------
# Metro
# --------------------------------------------------

# A dark slate rather than pure black. Black is the heaviest mark
# available and the line was using all of it, so a single dashed route
# outweighed the whole bus network beside it. The station symbol keeps
# INK: the node should read stronger than the line through it.
METRO_LINE_COLOR = "#3A4047"
METRO_SYMBOL_COLOR = INK

METRO_LINE_DASH_ZOOMOUT = "3,5"
METRO_LINE_DASH_ZOOMIN = "4,5"
METRO_LINE_WEIGHT_ZOOMOUT = 2
METRO_LINE_OPACITY_ZOOMOUT = 1
METRO_LINE_WEIGHT_ZOOMIN = 3
METRO_LINE_OPACITY_ZOOMIN = 0.55


# --------------------------------------------------
# Line weight hierarchy
# --------------------------------------------------
# Ranked by transport capacity, so the map reads as a hierarchy rather
# than as whichever network happened to get a heavier stroke:
#
#   metro  >  bus lanes  >  bike primary  >  bike secondary
#
# Each entry is (width at the layer's debut zoom, width at MAX_ZOOM).
# Fixed pixel widths look right at one zoom only: 1.2 px reads on a
# 38 m pixel at z12 and vanishes on a 0.2 m pixel at z19.

METRO_LINE_WIDTH = (2.0, 4.2)        # rapid transit, the structuring line
# Starts finer than before now that it debuts at 9 rather than 12: at
# the overview 5,507 segments are the armature of the region, and 1.8 px
# of pink across 100 km read as a wash rather than a network.
BUS_LANE_WIDTH = (1.1, 3.4)          # high-capacity surface transit
# Widened with the colour change. Hue alone could not hold a 1.3 px line
# against a bus network drawn at 1.1-3.4 with halos over it; the two
# together can.
BIKE_PRIMARY_WIDTH = (1.8, 3.4)
BIKE_SECONDARY_WIDTH = (1.3, 2.6)    # dashed, lightest of the networks
FERRY_ROUTE_WIDTH = (1.3, 2.2)       # distinct mode, set apart by dashes
CULTURE_LINE_WIDTH = (1.2, 2.2)      # heritage walls, not transit

# Dash patterns in pixels at the debut zoom
METRO_DASH = (4, 5)
FERRY_DASH = (4, 6)
BIKE_SECONDARY_DASH = (4, 5)

# The metro line stays solid enough to read as the spine, easing back
# slightly so it does not overpower street detail close in.
METRO_LINE_OPACITY = (1.0, 0.8)

METRO_SYMBOL_SIZE_SMALL = 13
METRO_SYMBOL_SIZE_LARGE = 19

# Metro stations are the top of the transport hierarchy, so they take the
# maximum bus-stop service-intensity bucket.
METRO_SERVICE_INTENSITY = 7

# --------------------------------------------------
# Ferry
# --------------------------------------------------

FERRY_ROUTE_COLOR = FERRY_INK
FERRY_ROUTE_WEIGHT = 0.8
FERRY_ROUTE_OPACITY = 0.75
FERRY_ROUTE_DASH = "4,6"
FERRY_TERMINAL_COLOR = FERRY_INK
FERRY_TERMINAL_SIZE = 15

# --------------------------------------------------
# Parking and taxi
# --------------------------------------------------

# Blue because that is the parking signage convention — a white P on blue
# is read without reference to a legend. Distinct from the water blue
# (much lighter) and the Metropolitan zone blue (much darker, and faded
# to 6% by the zoom parking appears at).
PARKING_COLOR = "#8AA8FF"
PARKING_FILL_OPACITY = 0.25
PARKING_SYMBOL_SIZE = 15

TAXI_COLOR = GREY_900
TAXI_SYMBOL_SIZE = 22

# --------------------------------------------------
# Trees
# --------------------------------------------------

TREE_EDGE_COLOR = "#2B8A3E"

# Individual tree dots, scaled together. The class radii below read as
# ground size at z18 (see TREE_RADIUS_ANCHOR_ZOOM in webexport), which is
# honest but leaves them very small on screen at the zoom they debut.
TREE_DOT_SCALE = 1.6

# Vegetation reads as density long before individual trees are legible.
# The heatmap ramp reuses the height-class greens so the two tiers of the
# same layer look related.
#
# Deliberately light: canopy is context you read *through*, not the
# subject. At full strength it swamped the transport networks, and the map
# read as a vegetation study rather than an infrastructure one. The ramp
# stays transparent for longer and tops out short of the darkest green.
TREE_HEAT_RAMP = [
    (0.0, "rgba(211, 249, 216, 0)"),
    (0.25, "rgba(211, 249, 216, 0.6)"),
    (0.55, "#B2F2BB"),
    (0.8, "#8CE99A"),
    (1.0, "#51CF66"),
]

# (at the layer's debut zoom, at its densest)
TREE_HEAT_OPACITY = (0.28, 0.38)

# A hint dot marks a dataset's presence before its icon is readable.
# Small and muted: it should register as texture, not compete.
HINT_RADIUS = 3.0
HINT_OPACITY = 0.55

# Height class -> (fill colour, dot radius), in legend order
# One hue, luminance only: a step scale, not a set of colours. Reads as
# data rather than as drawing.
TREE_CLASSES = {
    "0 - 1.8": ("#D3F9D8", 2.2),
    "1.8 - 3.7": ("#B2F2BB", 3),
    "3.7 - 4.9": ("#8CE99A", 3.8),
    "4.9 - 6.1": ("#51CF66", 4.4),
    "6.1 - 24.1": ("#2F9E44", 5.0),
    "Unknown": (GREY_300, 2.0),
}

# --------------------------------------------------
# Education and culture
# --------------------------------------------------

EDUCATION_COLOR = GREY_300
EDUCATION_FILL_OPACITY = 0.25
EDUCATION_SYMBOL_COLOR = SYMBOL_GREY
EDUCATION_SYMBOL_SIZE = 20

CULTURE_COLOR = GREY_200
CULTURE_LINE_COLOR = CULTURE_INK
CULTURE_SYMBOL_COLOR = CULTURE_INK
CULTURE_FILL_OPACITY = 0.35
CULTURE_LINE_WEIGHT = 2
CULTURE_LINE_OPACITY = 0.85
CULTURE_SYMBOL_SIZE = 17
CULTURE_SYMBOL_OPACITY = 0.65

CULTURE_ICON_FILES = {
    "Religious heritage": "religious_heritage.svg",
    "Theatre": "theatre.svg",
    "Historic site": "historic_site.svg",
    "Museum": "museum.svg",
    "Historic monument": "historic_monument.svg",
    "Library": "library.svg",
    "Art & Exhibition Space": "art_exhibition.svg",
    "Castle / fortification": "castle.svg",
}

CULTURE_FALLBACK_SUBTYPE = "Museum"


# --------------------------------------------------
# Icons
# --------------------------------------------------
# Lucide replaces the mixed-provenance SVGs the Folium map used, so every
# symbol comes from one drawing system with a consistent stroke weight.
# Names are lucide icon ids; see lucide.dev.

# Geometric marks rather than pictograms, the way the Folium map drew
# them. At 1,798 stops a dot, a ring and a bullseye read instantly and
# stay legible when small; five different vehicle glyphs at the same
# density are noise. This is also the transit-map convention: filled dot
# for an ordinary stop, ring for information, bullseye for a terminus,
# split circle for an interchange.
#
# Drawn in web/src/map/icons.ts — see BUILT there.
BUS_STOP_ICONS = {
    "Regular Stop": "stop-dot",
    "Info Stop": "stop-ring",
    "Transfer Station": "stop-split",
    "Terminal Stop": "stop-bullseye",
    "Operational Facility": "stop-minor",
}

BUS_STOP_FALLBACK_CATEGORY = "Regular Stop"

ICON_BUS_STOP = "bus-front"
# Not a lucide icon: a ring enclosing an M, drawn in icons.ts. The letter
# is the metro's own mark in Thessaloniki and reads faster than a vehicle
# pictogram, which is also what the Folium map used.
ICON_METRO_STATION = "metro-m"
ICON_FERRY_TERMINAL = "ship"
ICON_TAXI = "car-taxi-front"
ICON_PARKING = "square-parking"
ICON_EDUCATION = "graduation-cap"

# One icon per derived category. education_type used to hold the source
# filename, so a single glyph was all it could support; now that the
# tags are classified, the five real categories can be told apart.
EDUCATION_ICONS = {
    "School": "school",
    "University": "graduation-cap",
    "College": "graduation-cap",
    "Research institute": "flask-conical",
    "Training institute": "book-open",
    "Kindergarten": "school",
    "Education": "school",
}
EDUCATION_FALLBACK_CATEGORY = "Education"

# Composed marks, as the Folium icons were: a bicycle plus a qualifier.
# A bare P loses the bicycle and a bare bicycle loses the distinction
# between storing one and hiring one — the original icons carried both.
# Drawn in web/src/map/icons.ts; see BUILT there.
ICON_BIKE_PARKING = "bike-parking"   # bicycle + P
ICON_BIKE_RENTAL = "bike-rental"     # bicycle + key

# One icon per culture subtype, matching the eight SVGs used before.
# amphora reads as a museum in a Greek context far better than a
# generic building glyph.
CULTURE_ICONS = {
    "Religious heritage": "church",
    "Theatre": "drama",
    # Both historic categories take landmark — a pediment on four
    # columns, which reads as classical heritage in a Greek context far
    # better than the pyramid that used to stand in for "monument".
    # The distinction between a site and a monument is a cataloguing one,
    # not something a 14 px glyph can carry.
    "Historic site": "landmark",
    "Museum": "amphora",
    "Historic monument": "landmark",
    "Library": "library",
    "Art & Exhibition Space": "frame",
    "Castle / fortification": "castle",
}

# Icons sit on a white plate so they stay legible over any basemap,
# the same trick the Folium symbols used.
ICON_PLATE_COLOR = "#ffffff"

# One multiplier over every plated symbol, so icons scale together rather
# than eight per-layer numbers drifting apart. Applied on top of each
# layer's own size and of the zoom growth curve, so the proportion between
# a glyph and its plate is preserved.
ICON_SCALE = 1.35
PLATE_SCALE = 1.35


# --------------------------------------------------
# Population density
# --------------------------------------------------

# Violet, and the last free hue on the map. Pink is transit, orange is
# cycling, green is canopy, blue is water and parking, and the three
# zone hues are spoken for. A sequential ramp needs a hue nothing else
# occupies, or a mid-class polygon reads as some other layer's fill.
#
# Five steps, light to dark, at low chroma so a dense municipality never
# competes with the transit network drawn over it.
POP_DENSITY_RAMP = [
    "#F3F0FF",
    "#D0BFFF",
    "#A98EDA",
    "#7C5BB0",
    "#4A2E7A",
]

# Five classes, per the spec. Jenks; see classify.py for why the scheme
# is a switch rather than a constant.
POP_DENSITY_CLASSES = len(POP_DENSITY_RAMP)

# The choropleth is an area fill under everything else, so it holds back
# further than the zone wash does. It stays legible across all zooms —
# unlike zones it is the answer to a question, not background context —
# but never at a strength that buries a bus lane.
POP_DENSITY_FILL_OPACITY = [(9, 0.80), (14, 0.55), (17, 0.40)]

POP_DENSITY_OUTLINE = "#FFFFFF"
POP_DENSITY_OUTLINE_WIDTH = (0.6, 1.4)
POP_DENSITY_OUTLINE_OPACITY = 0.7

# --------------------------------------------------
# Population density, 100 m raster
# --------------------------------------------------

# The raster is classified with the *same* Jenks breaks as the municipal
# choropleth, and coloured from the same ramp. That is the whole point of
# having both: a cell darker than its municipality is denser than that
# municipality's average, which is the question the 100 m grid exists to
# answer. Two independent scales would have made them incomparable.
#
# A continuous ramp was tried first and was actively misleading. Density
# spans four orders of magnitude, so any smooth transfer function has to
# compress somewhere: with a log stretch the median cell (184/km2, which
# is rural) landed at 52% of the ramp and half the region read as
# mid-violet. Classes put the breaks where the meaning is.
POP_RASTER_SCALE = "classes"

# Alpha per class, low to high. The lightest class covers most of the
# region's area, so it stays faint enough to read streets through; the
# top classes are nearly opaque because that is the signal.
POP_RASTER_ALPHA = (55, 105, 155, 200, 235)

# Cells with no data at all stay fully clear — roughly two thirds of the
# grid's bounding box lies outside the study area, and a wash there would
# read as a measured zero.

# Eased back as you zoom in: at the overview the grid is the subject, but
# at street scale the streets underneath it are the context that makes a
# concentration mean something.
POP_RASTER_OPACITY = [(9, 0.90), (13, 0.70), (16, 0.55)]


# --------------------------------------------------
# Destinations (section 3B)
# --------------------------------------------------

# Grey, like education and culture. These are attractors, not networks:
# the icon says what the place is and the colour says nothing, which is
# the rule that keeps a saturated mark on this map always meaningful.
# A red cross for health was the temptation and the trap — red sits eight
# units from PT_PINK (#FF0055) and on top of the Urban zone outline.
DESTINATION_INK = GREY_700

# One icon per derived category. Categories come from the OSM tags, so
# these are the values classify.py actually produces — a fallback entry
# exists for each layer because a handful of features carry no usable tag.
HEALTH_ICONS = {
    "Hospital": "hospital",
    "Hospital with emergency": "hospital",
}
HEALTH_FALLBACK_CATEGORY = "Hospital"

# trophy for the 27 stadiums, goal for the 874 pitches: a stadium is a
# city-scale destination and a pitch is a local facility, and that is the
# only distinction this layer's attributes actually support.
SPORT_ICONS = {
    "Stadium": "trophy",
    "Sports pitch": "goal",
    "Sports facility": "goal",
}
SPORT_FALLBACK_CATEGORY = "Sports facility"

# building-2 rather than landmark for the town hall: landmark already
# means "historic site" in the culture layer, and two meanings for one
# glyph is worse than a duller glyph.
PUBLIC_SERVICE_ICONS = {
    "Town hall": "building-2",
    "Police": "shield",
    "Fire station": "flame",
    "Post office": "mail",
    "Courthouse": "scale",
    "Government office": "briefcase",
    "Public service": "briefcase",
}
PUBLIC_SERVICE_FALLBACK_CATEGORY = "Public service"

COMMERCIAL_ICONS = {
    "Supermarket": "shopping-cart",
    "Shopping mall": "store",
    "Department store": "shopping-bag",
    "Retail": "store",
}
COMMERCIAL_FALLBACK_CATEGORY = "Retail"

# Where two real categories deliberately share a glyph, the legend needs
# a name covering both — otherwise the deduplicated row is labelled with
# whichever category happened to come first. Keyed by lucide name.
#
# Only for genuine merges. Pairs where the second value is a fallback
# ("Hospital with emergency", "Public service", "Retail") are correctly
# represented by the primary label and are absent here.
AMENITY_LEGEND_LABELS = {
    "landmark": "Historic site or monument",
    "graduation-cap": "University or college",
}


# --------------------------------------------------
# Socio-demographic indicators (section 2)
# --------------------------------------------------

# Every indicator uses the same violet ramp. They are all choropleths on
# the same 14 polygons, so only one can be read at a time — which makes a
# shared ramp an advantage, not a compromise: light-is-low reads
# identically whichever indicator is on, and the legend names the measure
# and its unit. Five more hues would have been five more things competing
# with the transit accents for no gain.
INDICATOR_RAMP = POP_DENSITY_RAMP
INDICATOR_FILL_OPACITY = POP_DENSITY_FILL_OPACITY


# --------------------------------------------------
# Land use
# --------------------------------------------------

# Eight categories, and the one place on this map where several hues have
# to coexist: land use is a nominal classification, so the categories
# cannot be ranked and a sequential ramp would lie about them.
#
# Kept desaturated and low-contrast against everything else. This is a
# background layer describing the functional character of an area, not a
# criterion for siting anything, and it must never compete with the
# transit networks drawn over it. The hues borrow the conventional
# planning palette — residential warm, commercial red, industrial
# violet-grey, institutional blue, green space green — so a reader who
# has seen a zoning map does not need the legend.
LANDUSE_COLORS = {
    "RESIDENTIAL": "#F2E3C6",
    "COMMERCIAL": "#EFC3B4",
    "INDUSTRIAL": "#D9D2E0",
    "PUBLIC_INSTITUTIONAL": "#C9D9E8",
    "TRANSPORT_LOGISTICS": "#DCDCDC",
    "GREEN_RECREATION": "#CFE3C4",
    "AGRICULTURAL_NATURAL": "#EAEFE3",
    "OTHER_TRANSITION": "#E8E8E4",
}

LANDUSE_FALLBACK_COLOR = GREY_200

# Human labels for the legend and the popup: the source values are
# SHOUTING_SNAKE_CASE, which is a database convention, not a map one.
LANDUSE_LABELS = {
    "RESIDENTIAL": "Residential",
    "COMMERCIAL": "Commercial",
    "INDUSTRIAL": "Industrial",
    "PUBLIC_INSTITUTIONAL": "Public & institutional",
    "TRANSPORT_LOGISTICS": "Transport & logistics",
    "GREEN_RECREATION": "Green & recreation",
    "AGRICULTURAL_NATURAL": "Agricultural & natural",
    "OTHER_TRANSITION": "Other / transitional",
}

# Fades as street detail takes over, the same way the zone wash does:
# full strength when the functional pattern of the city is the subject,
# well back once individual buildings and stops are legible.
LANDUSE_FILL_OPACITY = [(11, 0.85), (15, 0.55), (18, 0.35)]

# A hairline edge so adjacent parcels of one category stay countable
# without the outline reading as a feature in its own right.
LANDUSE_EDGE_OPACITY = 0.35
LANDUSE_EDGE_WIDTH = (0.3, 0.7)


# --------------------------------------------------
# Pedestrian network
# --------------------------------------------------

# Light grey and dashed, as the source files were styled in QGIS
# (`*_dashed_lightgrey`). Grey because this is the substrate every other
# layer sits on rather than a mode competing with them, and dashed
# because a footway is not a carriageway.
#
# GREY_400 rather than a lighter grey: GREY_300 against a GREY_100
# basemap is two shades apart and reads as nothing, and a layer nobody
# can see cannot do the one job it has.
WALKWAY_COLOR = GREY_400
WALKWAY_WIDTH = (0.9, 1.9)
WALKWAY_DASH = (4, 3)
WALKWAY_OPACITY = 0.95


# --------------------------------------------------
# Buildings by height
# --------------------------------------------------

# Five classes on round metre breaks rather than Jenks. Height has a
# natural unit that population density does not: "6 - 12 m" is a
# quantity a reader holds, where a Jenks bound of 7.3 is an artefact of
# the distribution. The breaks also fall where the data does — the
# classes come out 19 / 25 / 33 / 18 / 5 percent.
#
# Labelled in metres only, deliberately. The temptation was to name
# storeys, but MAX_FLOOR in this dataset gives a median of 1, 1, 2, 4
# and 7 floors per class, so a "~3 m per storey" label would have been
# wrong for the two lowest classes. The popup carries the surveyed floor
# count, which is the honest place for it.
BUILDING_HEIGHT_BREAKS = [3, 6, 12, 20]

BUILDING_HEIGHT_LABELS = [
    "Under 3 m",
    "3 \u2013 6 m",
    "6 \u2013 12 m",
    "12 \u2013 20 m",
    "Over 20 m",
]

# Slate, light to near-black. A sequential ramp has to be one hue, and
# slate is the convention for built mass — it also stays clear of the
# violet the population choropleths own and of the pale WATER_FILL,
# which is far lighter than even the first class here.
BUILDING_HEIGHT_RAMP = [
    "#DDE3EA",
    "#B4C4D4",
    "#7C9DC0",
    "#4A6E96",
    "#22405F",
]

# Solid enough to read as mass at z16, eased back at the overview where
# 192,565 footprints would otherwise become a single dark field.
BUILDING_HEIGHT_OPACITY = [(12, 0.55), (15, 0.80), (18, 0.90)]

# No outline. At z16 a hairline per footprint doubles the ink on the
# densest layer on the map, and the fill boundaries already separate
# adjacent buildings because the classes differ.


# --------------------------------------------------
# Mobility hubs
# --------------------------------------------------

# The one icon on this map that is not a lucide glyph: the Kinesis City
# Hub mark, shipped as a PNG and registered with addImage directly. It
# keeps its own colours — a hub is the subject of the project, not
# another category of street furniture, so it is the single mark allowed
# to sit outside the palette.
#
# The bare glyph, and the same artwork the sidebar shows, so the mark in
# the header and the mark on the map are one thing. No tile: the runner
# alone is what identifies a hub here.
HUB_ICON = "mobility-hub"
HUB_ICON_FILE = "mobility-hub.png"

# The mark inside the same rounded blue frame the sidebar shows, so the
# logo in the header and the marker on the map are one object rather
# than two versions of a drawing. The frame also gives the glyph an edge:
# unframed it had no boundary against a park or a car park.
#
# 176 px square at pixelRatio 2, so 88 px at icon-size 1 — twice the old
# asset, hence half the old multipliers. Still lands at 26 px growing to
# 42 px, alongside the bike icons.
HUB_ICON_SIZE = (0.30, 0.48)

# One mark at three sizes, not three marks. The tiers are a hierarchy —
# 8 connection hubs on 0.95 median public-transport access, 44
# neighbourhood on 0.25, 170 street-scale on 0.17 — and size is how a
# reader takes in rank without consulting a legend. Multipliers on the
# ramp above.
# The 222 scored sites are candidates, so only the chosen one carries the
# Kinesis mark — 222 logos would have said every candidate was decided.
#
# The tiers are 8 / 44 / 170, and that inequality sets the design: give
# the 8 a symbol and the 170 a dot, the way a transit map names its
# interchanges and dots its stops. 170 line-drawn glyphs would be noise,
# and 8 dots would waste the one tier worth identifying.
#
# Three axes move together — structure, size and value — so a mark is
# placeable on the ranking in isolation, not only when two sit side by
# side. Three near-identical blues 1.8 px apart were not.
# Connection hubs: a double ring — blue, white, blue. The transit
# convention for a major interchange, and it separates from the single
# ring below by structure rather than by yet another size step.
HUB_CONNECTION_COLOR = "#005DC1"
# The centre takes the runner's head teal — the same colour the switches
# use for "on". Blue on blue made the double ring read as one thick ring
# with a hole; the teal core makes the top tier unmistakable, and it is
# already in the mark the map is named after.
HUB_CONNECTION_CORE_COLOR = "#4EC5AF"
HUB_CONNECTION_RADIUS = (7.0, 11.5)
# Fractions of the outer radius, so the rings hold their proportions
# across the zoom ramp instead of closing up at one end of it.
HUB_CONNECTION_MID_RATIO = 0.66
HUB_CONNECTION_CORE_RATIO = 0.34

# A single ring: one step of structure below the double.
HUB_NEIGHBOURHOOD_COLOR = "#005DC1"
HUB_NEIGHBOURHOOD_RADIUS = (5.4, 9.2)
HUB_NEIGHBOURHOOD_CORE = "#FFFFFF"
HUB_NEIGHBOURHOOD_CORE_RATIO = 0.42

# The texture tier: quietest by colour, and the smallest of the three —
# but not so small it disappears, which is what a 2.4 px dot did.
HUB_STREET_COLOR = "#6FA8DC"
HUB_STREET_RADIUS = (4.2, 7.4)

# Before the tiers resolve, every hub is one plain dot. At the zoom the
# bike lanes arrive, the question is "where is the network" — rank is a
# question you only ask once you can see the sites individually, and
# three marks answering it from z12 was detail before the outline.
HUB_OVERVIEW_COLOR = "#3F86D6"
HUB_OVERVIEW_RADIUS = (3.4, 4.6)

HUB_DOT_STROKE = "#FFFFFF"
HUB_DOT_STROKE_WIDTH = 1.4

# The sidebar chip is drawn with lucide-react, which has no way to show a
# supplied PNG, so the chip uses the nearest glyph. Only the chip — the
# map still draws the real logo.
HUB_SWATCH_ICON = "person-standing"
HUB_SWATCH_COLOR = "#005DC1"   # the logo blue

# Above everything. A candidate hub is the thing the reader is being
# asked to judge, so nothing occludes it.


# --------------------------------------------------
# Public open space
# --------------------------------------------------

# Green for what is planted, stone for what is paved. That is the whole
# scheme, and it is the distinction a reader of an open-space map needs:
# a park and a square are both public, but only one of them has grass.
#
# These greens sit between the tree canopy (saturated, a texture) and the
# land-use wash (very pale, a background). Open space is the subject
# here, so it is more present than land use and flatter than canopy —
# and it must never be mistaken for either when both are on.
GREEN_SPACE_COLORS = {
    # Deepest for the most enclosed canopy, lightest for open grass, so
    # the five subtypes read as one gradient of how planted a place is
    # rather than as five unrelated categories.
    #
    # Each mixed 40% toward white from the original set. Lightened by
    # moving the colours rather than by dropping the opacity: this layer
    # is drawn from the minimum zoom under everything else, and fading it
    # instead would have let the basemap tint every subtype differently,
    # pulling the gradient apart.
    "Forest": "#B7DABE",
    "Park": "#CBE6C7",
    "Playground": "#D4ECD7",
    "Green space": "#E0EFDB",
    "Recreational space": "#CFE6DC",
}
GREEN_SPACE_FALLBACK = "Green space"
GREEN_SPACE_EDGE = "#8FBE99"
GREEN_SPACE_FILL_OPACITY = [(13, 0.55), (16, 0.40)]

# Warm stone: a square is hard landscape, and colouring it green would
# have said the opposite of what it is.
SQUARE_FILL = "#F0EADF"
SQUARE_EDGE = "#CBBFA7"
SQUARE_FILL_OPACITY = [(13, 0.70), (16, 0.50)]

# The same grey as education, culture, health and the rest. A playground
# icon is a destination symbol like any other; giving it a green of its
# own made it read as part of the fill underneath rather than as a
# marker on top of it.
PLAYGROUND_SYMBOL_COLOR = DESTINATION_INK

PLAYGROUND_ICONS = {"Playground": "toy-brick"}
