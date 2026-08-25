"""Attribute access helpers."""

NAME_FIELDS = [
    "name", "Name", "NAME",
    "name_el", "name:el", "name_en",
    "station", "Station", "STATION",
    "terminal", "Terminal",
    "onomasia", "onomastasi", "ΟΝΟΜΑΣΙΑ",
    "operator",
]

TAXI_NAME_FIELDS = [
    "name", "Name", "NAME",
    "taxi", "amenity", "type", "operator",
    "ΟΝΟΜΑΣΙΑ", "onomasia", "onomastasi",
]


def first_non_empty(row, fields, default):
    """Return the first non-empty value among `fields`, else `default`."""

    for field in fields:
        if field in row.index:
            value = row.get(field)
            if value is not None and str(value).strip() != "":
                return str(value)

    return default


def name_of(row, default):
    """Best available name for a feature."""
    return first_non_empty(row, NAME_FIELDS, default)
