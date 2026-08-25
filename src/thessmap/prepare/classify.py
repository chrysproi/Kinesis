"""Classification rules turning raw attributes into map categories."""

import re

import pandas as pd


REGULAR_STOP = "ΣΤΑΣΗ"
PORTABLE_STOP = "ΦΟΡΗΤΗ ΣΤΑΣΗ"
OPERATIONAL_FACILITIES = ["ΑΜΑΞΟΣΤΑΣΙΟ", "ΣΤΑΘΜΑΡΧΕΙΟ", "ΣΤΑΘΜΑΡΧΕΙΟ ΤΕΣ"]


def bus_stop_symbol_category(raw_type):
    """Map the official station type onto a symbol category."""

    if raw_type is None:
        return "Unknown"

    value = str(raw_type).strip().upper()

    if value == REGULAR_STOP:
        return "Regular Stop"

    if value == PORTABLE_STOP:
        return "Portable Stop"

    if "ΤΕΣ ΠΛΗΡΟΦΟΡΗΣΗ" in value:
        return "Info Stop"

    if "ΣΤΑΘΜΟΣ ΜΕΤΕΠΙΒΙΒΑΣΗΣ" in value:
        return "Transfer Station"

    if "ΤΕΡΜΑΤΙΚΟΣ ΣΤΑΘΜΟΣ" in value or "ΤΕΣΜΑΤΙΚΟΣ ΣΤΑΘΜΟΣ" in value:
        return "Terminal Stop"

    if value in OPERATIONAL_FACILITIES:
        return "Operational Facility"

    return "Unknown"


def classify_stop_type(value):
    """Functional category. Groups portable stops with regular ones."""

    if pd.isna(value):
        return "Unknown"

    value = str(value).strip().upper()

    if value in (REGULAR_STOP, PORTABLE_STOP):
        return "Regular Stop"

    return bus_stop_symbol_category(value)


def count_lines(value):
    """Number of distinct bus lines listed in the `lines_ejyp` field."""

    if pd.isna(value):
        return 0

    text = str(value).strip()

    if text == "":
        return 0

    parts = re.split(r"[,;/|]+", text)
    lines = {part.strip() for part in parts if part.strip()}

    return len(lines)


SERVICE_LEVELS = [(0, "Unknown service"), (1, "Local stop"),
                  (3, "Multi-line stop"), (6, "High-service stop")]
MAJOR_NODE = "Major PT node"


def classify_service_level(line_count):
    """Service intensity band from the number of lines served."""

    for threshold, label in SERVICE_LEVELS:
        if line_count <= threshold:
            return label

    return MAJOR_NODE


TREE_BREAKS = [(1.8, "0 - 1.8"), (3.7, "1.8 - 3.7"), (4.9, "3.7 - 4.9"),
               (6.1, "4.9 - 6.1")]
TREE_TOP_CLASS = "6.1 - 24.1"


def classify_tree_value(value):
    """Height class from the `mo_rd` measurement."""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Unknown"

    for threshold, label in TREE_BREAKS:
        if value <= threshold:
            return label

    return TREE_TOP_CLASS


CULTURE_FIELDS = ["path", "amenity", "tourism", "historic", "religion",
                  "museum", "theatre_ty", "library_ty",
                  "name", "Name", "NAME", "name_el", "name:el", "name_en"]

CULTURE_RULES = [
    (["theatre", "theater"], "Theatre"),
    (["library"], "Library"),
    (["arts_centre", "art centre", "art_center", "arts center", "gallery"],
     "Art & Exhibition Space"),
    (["museum"], "Museum"),
    (["castle", "fortification"], "Castle / fortification"),
    (["archaeological", "historic site", "ruins"], "Historic site"),
    (["monument", "memorial"], "Historic monument"),
    (["religion", "place_of_worship", "church", "mosque", "monastery",
      "synagogue", "chapel"], "Religious heritage"),
]

CULTURE_DEFAULT = "Historic site"


def classify_culture_subtype(row):
    """Assign a culture subtype by scanning several attributes at once."""

    text = " ".join(
        str(row.get(field)).lower()
        for field in CULTURE_FIELDS
        if field in row.index and row.get(field) is not None
    )

    for keywords, subtype in CULTURE_RULES:
        if any(keyword in text for keyword in keywords):
            return subtype

    return CULTURE_DEFAULT


PUBLIC_SERVICE_BY_AMENITY = {
    "post_office": "Post office",
    "police": "Police",
    "townhall": "Town hall",
    "fire_station": "Fire station",
    "courthouse": "Courthouse",
}

COMMERCIAL_BY_SHOP = {
    "supermarket": "Supermarket",
    "mall": "Shopping mall",
    "department_store": "Department store",
}

SPORT_BY_LEISURE = {
    "stadium": "Stadium",
    "pitch": "Sports pitch",
}

DROP_AMENITIES = {"parking_entrance", "parking"}


def _tag(row, key):
    """A tag's value as a clean string, or None when absent or blank."""
    value = row.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text if text and text.lower() != "nan" else None


def classify_public_service(row):
    """Category for a public-service point."""

    amenity = _tag(row, "amenity")
    if amenity in PUBLIC_SERVICE_BY_AMENITY:
        return PUBLIC_SERVICE_BY_AMENITY[amenity]

    if _tag(row, "office") == "government" or _tag(row, "government"):
        return "Government office"

    return "Public service"


def classify_commercial(row):
    """Category for a major commercial destination."""

    shop = _tag(row, "shop")
    if shop in COMMERCIAL_BY_SHOP:
        return COMMERCIAL_BY_SHOP[shop]

    return "Retail"


def classify_sport(row):
    """Category for a sports facility."""

    return SPORT_BY_LEISURE.get(_tag(row, "leisure"), "Sports facility")


def classify_health(row):
    """Category for a health facility."""

    if _tag(row, "emergency") == "yes":
        return "Hospital with emergency"

    return "Hospital"


EDUCATION_BY_AMENITY = {
    "school": "School",
    "university": "University",
    "college": "College",
    "research_institute": "Research institute",
    "kindergarten": "Kindergarten",
    "arts_centre": "Training institute",
}


def classify_education(row):
    """Category for an education feature."""

    amenity = _tag(row, "amenity")
    if amenity in EDUCATION_BY_AMENITY:
        return EDUCATION_BY_AMENITY[amenity]

    if _tag(row, "office") == "educational_institution":
        return "Training institute"

    return "Education"


STOP_TYPE_RANK = {
    "Transfer Station": 1,
    "Terminal Stop": 2,
    "Info Stop": 3,
    "Regular Stop": 4,
    "Operational Facility": 5,
}

STOP_RANK_FALLBACK = max(STOP_TYPE_RANK.values()) + 1


def classify_stop_rank(category):
    """Rank a stop by its functional category. Lower is more important."""
    return STOP_TYPE_RANK.get(category, STOP_RANK_FALLBACK)
