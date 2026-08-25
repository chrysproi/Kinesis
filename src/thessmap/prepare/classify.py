"""Classification rules turning raw attributes into map categories.

Pure functions with no I/O, so they are cheap to test — which matters,
because the bus stop rules match Greek strings including a tolerance for
a known typo in the source data.
"""

import re

import pandas as pd

# --------------------------------------------------
# Bus stops
# --------------------------------------------------

REGULAR_STOP = "ΣΤΑΣΗ"
PORTABLE_STOP = "ΦΟΡΗΤΗ ΣΤΑΣΗ"
OPERATIONAL_FACILITIES = ["ΑΜΑΞΟΣΤΑΣΙΟ", "ΣΤΑΘΜΑΡΧΕΙΟ", "ΣΤΑΘΜΑΡΧΕΙΟ ΤΕΣ"]


def bus_stop_symbol_category(raw_type):
    """
    Map the official station type onto a symbol category.

    Uses the raw `type` field rather than the prepared category, so a
    Portable Stop keeps its own symbol instead of collapsing into
    Regular Stop the way `classify_stop_type` does.
    """

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

    # The source data contains both spellings; ΤΕΣΜΑΤΙΚΟΣ is a typo
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


# --------------------------------------------------
# Trees
# --------------------------------------------------

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


# --------------------------------------------------
# Culture
# --------------------------------------------------

CULTURE_FIELDS = ["path", "amenity", "tourism", "historic", "religion",
                  "museum", "theatre_ty", "library_ty",
                  "name", "Name", "NAME", "name_el", "name:el", "name_en"]

# Order matters: the first match wins, so specific types precede general
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
    """
    Assign a culture subtype by scanning several attributes at once.

    Sources tag inconsistently, so all candidate fields are concatenated
    and matched as one blob of text.
    """

    text = " ".join(
        str(row.get(field)).lower()
        for field in CULTURE_FIELDS
        if field in row.index and row.get(field) is not None
    )

    for keywords, subtype in CULTURE_RULES:
        if any(keyword in text for keyword in keywords):
            return subtype

    return CULTURE_DEFAULT


# --------------------------------------------------
# Destination categories (section 3B)
# --------------------------------------------------
# Derived from the OSM tags rather than from the files' own SUBCATEGORY
# column. SUBCATEGORY is 82% empty on commercial and 71% empty on public
# services, and what survives was truncated to ten characters by a
# shapefile round-trip (" SUPERMARK", "FIRE_STATI", "POST_OFFIC"). The
# OSM tags underneath are complete, so they are the reliable source and
# SUBCATEGORY is ignored.

# amenity / office / government -> category, in priority order. `amenity`
# is checked first because it is the specific claim; office=government
# is the catch-all 110 features fall back to.
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

# leisure=stadium is a city-scale attractor; leisure=pitch is a local
# facility. Keeping them apart matters more than splitting by sport,
# which would need twenty icons for a layer that is 90% unnamed.
SPORT_BY_LEISURE = {
    "stadium": "Stadium",
    "pitch": "Sports pitch",
}

# Entrances tagged onto a mall or a public building are not destinations
# in their own right — they are the same place mapped twice.
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

    # office=government covers 110 features that carry no amenity tag.
    # The `government` sub-tag distinguishes tax from customs from
    # ministry, but 234 of 279 are empty, so they stay one category.
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
    """
    Category for a health facility.

    Every feature in both source files is amenity=hospital or
    healthcare=hospital, so this exists to keep the shape of the other
    four rather than to make a distinction the data supports.
    """

    if _tag(row, "emergency") == "yes":
        return "Hospital with emergency"

    return "Hospital"


# --------------------------------------------------
# Education categories
# --------------------------------------------------
# The nine source files carry no type of their own, so education_type
# used to hold the filename — which surfaced in the popup as
# "Type: education_8". Derived from the OSM tags instead.
#
# The files are really five categories split arbitrarily: 1 and 7 are
# both amenity=college, 8 and 9 both amenity=school, 4 and 5 both
# office=educational_institution, and 6 is empty.

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

    # office=educational_institution covers the language schools and
    # training centres in education_4 and education_5
    if _tag(row, "office") == "educational_institution":
        return "Training institute"

    return "Education"


# --------------------------------------------------
# Stop rank
# --------------------------------------------------
# A functional hierarchy over stop_type_cat, 1 being the most important.
# Ranked by interchange role rather than by passenger volume, which the
# source does not carry:
#
#   1  transfer station     where a rider changes line
#   2  terminal             where a line begins or ends, so every rider
#                           on it boards or alights here
#   3  info stop            a staffed or signed stop, above a plain pole
#   4  regular stop         the default
#   5  operational facility a depot: not a passenger stop at all, ranked
#                           last so hub scoring never rewards one
STOP_TYPE_RANK = {
    "Transfer Station": 1,
    "Terminal Stop": 2,
    "Info Stop": 3,
    "Regular Stop": 4,
    "Operational Facility": 5,
}

# Anything unrecognised sorts below every known type
STOP_RANK_FALLBACK = max(STOP_TYPE_RANK.values()) + 1


def classify_stop_rank(category):
    """Rank a stop by its functional category. Lower is more important."""
    return STOP_TYPE_RANK.get(category, STOP_RANK_FALLBACK)


# --------------------------------------------------
# Waterways
# --------------------------------------------------
# Two tiers, because 3,031 segments at the overview zoom is a mesh and
# only a few of them are rivers anyone would name. A river or canal is a
# feature of the region; a field drain is street-scale detail.
MAJOR_WATERWAYS = {"river", "canal", "riverbank"}


def classify_waterway(value):
    """"major" for a river or canal, "minor" for everything else."""
    text = str(value).strip().lower() if value is not None else ""
    return "major" if text in MAJOR_WATERWAYS else "minor"
