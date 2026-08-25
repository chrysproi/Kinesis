"""Every colour and size decision on the map."""


GREY_100 = "#F1F3F5"
GREY_200 = "#E9ECEF"
GREY_300 = "#DEE2E6"
GREY_400 = "#ADB5BD"
GREY_600 = "#868E96"
GREY_700 = "#495057"
GREY_900 = "#212529"
INK = "#000000"
FERRY_INK = GREY_700
SYMBOL_GREY = GREY_600
CULTURE_INK = GREY_700
PT_PINK = "#FF0055"
PT_PINK_SOFT = "#FF8FB2"
WATER_FILL = "#E7F5FF"
WATER_EDGE = "#A5D8FF"


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

ZONE_FILL_FADE = [(9, 1.0), (13, 0.45), (16, 0.10)]
ZONE_OUTLINE_WEIGHTS = {
    "Regional": 1.4,
    "Metropolitan": 1.5,
    "Urban": 1.7,
}


WATER_LINE_COLOR = "#74C0FC"
WATER_MAJOR_WIDTH = (1.2, 3.2)
WATER_MINOR_WIDTH = (0.5, 1.6)
WATER_LINE_OPACITY = 0.85
WATER_BODY_FILL_OPACITY = 0.75
WATER_STRUCTURE_RADIUS = 2.6
WATER_STRUCTURE_COLOR = "#3B8FD4"
WATER_STRUCTURE_STROKE = "#ffffff"
LAKE_LABEL_COLOR = GREY_700
BUILDING_FILL = GREY_200
BUILDING_EDGE = GREY_400
LAKE_LABEL_OFFSETS = {
    "Λίμνη Βόλβη": (0.015, -0.080),
    "Λίμνη Κορώνεια": (0.010, -0.03),
    "Λίμνη Πικρολίμνη": (0.006, -0.004),
}


BIKE_COLOR = "#FF7300"
BIKE_PROPOSED_WIDTH = (2.0, 3.6)
BIKE_PROPOSED_DASH = (9, 6)
BIKE_PROPOSED_OPACITY = 0.9
BIKE_CLUSTER_COLOR = "#FF7300"
PRIMARY_BIKE_WEIGHT = 1.2
SECONDARY_BIKE_WEIGHT = 0.8
SECONDARY_BIKE_DASH = "4,5"
BIKE_SYMBOL_SIZE = 22
BIKE_ICON_SIZE = 20


BUS_STOP_SIMPLE_COLOR = PT_PINK
BUS_STOP_OUTER_COLOR = PT_PINK_SOFT
BUS_STOP_SYMBOL_COLOR = PT_PINK
BUS_LANE_COLOR = PT_PINK_SOFT
BUS_LANE_OPACITY = 0.85
BUS_STOP_DOT_OPACITY = 0.9
BUS_STOP_HALO_OPACITY = 0.22
BUS_STOP_OUTER_RADII = [(0, 8), (1, 9), (3, 11), (6, 13)]
BUS_STOP_MAX_RADIUS = 16


METRO_LINE_COLOR = "#3A4047"
METRO_SYMBOL_COLOR = INK
METRO_LINE_DASH_ZOOMOUT = "3,5"
METRO_LINE_DASH_ZOOMIN = "4,5"
METRO_LINE_WEIGHT_ZOOMOUT = 2
METRO_LINE_OPACITY_ZOOMOUT = 1
METRO_LINE_WEIGHT_ZOOMIN = 3
METRO_LINE_OPACITY_ZOOMIN = 0.55


METRO_LINE_WIDTH = (2.0, 4.2)
BUS_LANE_WIDTH = (1.1, 3.4)
BIKE_PRIMARY_WIDTH = (1.8, 3.4)
BIKE_SECONDARY_WIDTH = (1.3, 2.6)
FERRY_ROUTE_WIDTH = (1.3, 2.2)
CULTURE_LINE_WIDTH = (1.2, 2.2)
METRO_DASH = (4, 5)
FERRY_DASH = (4, 6)
BIKE_SECONDARY_DASH = (4, 5)
METRO_LINE_OPACITY = (1.0, 0.8)
METRO_SYMBOL_SIZE_SMALL = 13
METRO_SYMBOL_SIZE_LARGE = 19
METRO_SERVICE_INTENSITY = 7


FERRY_ROUTE_COLOR = FERRY_INK
FERRY_ROUTE_WEIGHT = 0.8
FERRY_ROUTE_OPACITY = 0.75
FERRY_ROUTE_DASH = "4,6"
FERRY_TERMINAL_COLOR = FERRY_INK
FERRY_TERMINAL_SIZE = 15


PARKING_COLOR = "#8AA8FF"
PARKING_FILL_OPACITY = 0.25
PARKING_SYMBOL_SIZE = 15
TAXI_COLOR = GREY_900
TAXI_SYMBOL_SIZE = 22


TREE_EDGE_COLOR = "#2B8A3E"
TREE_DOT_SCALE = 1.6
TREE_HEAT_RAMP = [
    (0.0, "rgba(211, 249, 216, 0)"),
    (0.25, "rgba(211, 249, 216, 0.6)"),
    (0.55, "#B2F2BB"),
    (0.8, "#8CE99A"),
    (1.0, "#51CF66"),
]

TREE_HEAT_OPACITY = (0.28, 0.38)
HINT_RADIUS = 3.0
HINT_OPACITY = 0.55
TREE_CLASSES = {
    "0 - 1.8": ("#D3F9D8", 2.2),
    "1.8 - 3.7": ("#B2F2BB", 3),
    "3.7 - 4.9": ("#8CE99A", 3.8),
    "4.9 - 6.1": ("#51CF66", 4.4),
    "6.1 - 24.1": ("#2F9E44", 5.0),
    "Unknown": (GREY_300, 2.0),
}


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


BUS_STOP_ICONS = {
    "Regular Stop": "stop-dot",
    "Info Stop": "stop-ring",
    "Transfer Station": "stop-split",
    "Terminal Stop": "stop-bullseye",
    "Operational Facility": "stop-minor",
}

BUS_STOP_FALLBACK_CATEGORY = "Regular Stop"
ICON_BUS_STOP = "bus-front"
ICON_METRO_STATION = "metro-m"
ICON_FERRY_TERMINAL = "ship"
ICON_TAXI = "car-taxi-front"
ICON_PARKING = "square-parking"
ICON_EDUCATION = "graduation-cap"
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
ICON_BIKE_PARKING = "bike-parking"
ICON_BIKE_RENTAL = "bike-rental"
CULTURE_ICONS = {
    "Religious heritage": "church",
    "Theatre": "drama",
    "Historic site": "landmark",
    "Museum": "amphora",
    "Historic monument": "landmark",
    "Library": "library",
    "Art & Exhibition Space": "frame",
    "Castle / fortification": "castle",
}

ICON_PLATE_COLOR = "#ffffff"
ICON_SCALE = 1.35
PLATE_SCALE = 1.35


POP_DENSITY_RAMP = [
    "#F3F0FF",
    "#D0BFFF",
    "#A98EDA",
    "#7C5BB0",
    "#4A2E7A",
]

POP_DENSITY_CLASSES = len(POP_DENSITY_RAMP)
POP_DENSITY_FILL_OPACITY = [(9, 0.80), (14, 0.55), (17, 0.40)]
POP_DENSITY_OUTLINE = "#FFFFFF"
POP_DENSITY_OUTLINE_WIDTH = (0.6, 1.4)
POP_DENSITY_OUTLINE_OPACITY = 0.7


POP_RASTER_SCALE = "classes"
POP_RASTER_ALPHA = (55, 105, 155, 200, 235)


POP_RASTER_OPACITY = [(9, 0.90), (13, 0.70), (16, 0.55)]


DESTINATION_INK = GREY_700
HEALTH_ICONS = {
    "Hospital": "hospital",
    "Hospital with emergency": "hospital",
}
HEALTH_FALLBACK_CATEGORY = "Hospital"
SPORT_ICONS = {
    "Stadium": "trophy",
    "Sports pitch": "goal",
    "Sports facility": "goal",
}
SPORT_FALLBACK_CATEGORY = "Sports facility"
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
AMENITY_LEGEND_LABELS = {
    "landmark": "Historic site or monument",
    "graduation-cap": "University or college",
}


INDICATOR_RAMP = POP_DENSITY_RAMP
INDICATOR_FILL_OPACITY = POP_DENSITY_FILL_OPACITY


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

LANDUSE_FILL_OPACITY = [(11, 0.85), (15, 0.55), (18, 0.35)]
LANDUSE_EDGE_OPACITY = 0.35
LANDUSE_EDGE_WIDTH = (0.3, 0.7)


WALKWAY_COLOR = GREY_400
WALKWAY_WIDTH = (0.9, 1.9)
WALKWAY_DASH = (4, 3)
WALKWAY_OPACITY = 0.95


BUILDING_HEIGHT_BREAKS = [3, 6, 12, 20]
BUILDING_HEIGHT_LABELS = [
    "Under 3 m",
    "3 \u2013 6 m",
    "6 \u2013 12 m",
    "12 \u2013 20 m",
    "Over 20 m",
]

BUILDING_HEIGHT_RAMP = [
    "#DDE3EA",
    "#B4C4D4",
    "#7C9DC0",
    "#4A6E96",
    "#22405F",
]

BUILDING_HEIGHT_OPACITY = [(12, 0.55), (15, 0.80), (18, 0.90)]


HUB_ICON = "mobility-hub"
HUB_ICON_FILE = "mobility-hub.png"
HUB_ICON_SIZE = (0.30, 0.48)
HUB_CONNECTION_COLOR = "#005DC1"
HUB_CONNECTION_CORE_COLOR = "#4EC5AF"
HUB_CONNECTION_RADIUS = (7.0, 11.5)
HUB_CONNECTION_MID_RATIO = 0.66
HUB_CONNECTION_CORE_RATIO = 0.34
HUB_NEIGHBOURHOOD_COLOR = "#005DC1"
HUB_NEIGHBOURHOOD_RADIUS = (5.4, 9.2)
HUB_NEIGHBOURHOOD_CORE = "#FFFFFF"
HUB_NEIGHBOURHOOD_CORE_RATIO = 0.42
HUB_STREET_COLOR = "#6FA8DC"
HUB_STREET_RADIUS = (4.2, 7.4)
HUB_OVERVIEW_COLOR = "#3F86D6"
HUB_OVERVIEW_RADIUS = (3.4, 4.6)
HUB_DOT_STROKE = "#FFFFFF"
HUB_DOT_STROKE_WIDTH = 1.4
HUB_SWATCH_ICON = "person-standing"
HUB_SWATCH_COLOR = "#005DC1"


GREEN_SPACE_COLORS = {
    "Forest": "#B7DABE",
    "Park": "#CBE6C7",
    "Playground": "#D4ECD7",
    "Green space": "#E0EFDB",
    "Recreational space": "#CFE6DC",
}
GREEN_SPACE_FALLBACK = "Green space"
GREEN_SPACE_EDGE = "#8FBE99"
GREEN_SPACE_FILL_OPACITY = [(13, 0.55), (16, 0.40)]
SQUARE_FILL = "#F0EADF"
SQUARE_EDGE = "#CBBFA7"
SQUARE_FILL_OPACITY = [(13, 0.70), (16, 0.50)]
PLAYGROUND_SYMBOL_COLOR = DESTINATION_INK
PLAYGROUND_ICONS = {"Playground": "toy-brick"}
