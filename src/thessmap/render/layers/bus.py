"""Bus lanes and bus stops."""

import folium

from ... import palette
from ...prepare.classify import bus_stop_symbol_category
from ..markers import circle, points, symbol_marker

TRANSPORT_PANE = "transport_points_pane"


def outer_radius(line_count):
    """Circle radius from the number of lines served."""

    try:
        line_count = int(line_count)
    except (TypeError, ValueError):
        line_count = 0

    for max_lines, radius in palette.BUS_STOP_OUTER_RADII:
        if line_count <= max_lines:
            return radius

    return palette.BUS_STOP_MAX_RADIUS


_COLOR = palette.BUS_STOP_SYMBOL_COLOR
_ASTERISK_IN_CIRCLE = f"""
    <circle cx="10" cy="10" r="7"
            fill="white" stroke="{_COLOR}" stroke-width="2"/>
    <line x1="10" y1="4.8" x2="10" y2="15.2"
          stroke="{_COLOR}" stroke-width="2.1" stroke-linecap="round"/>
    <line x1="5.5" y1="7.4" x2="14.5" y2="12.6"
          stroke="{_COLOR}" stroke-width="2.1" stroke-linecap="round"/>
    <line x1="14.5" y1="7.4" x2="5.5" y2="12.6"
          stroke="{_COLOR}" stroke-width="2.1" stroke-linecap="round"/>
"""

SYMBOLS = {
    "Regular Stop": f"""
    <circle cx="10" cy="10" r="4.5"
            fill="{_COLOR}" stroke="{_COLOR}" stroke-width="2"/>
    """,
    "Portable Stop": _ASTERISK_IN_CIRCLE,
    "Info Stop": f"""
    <circle cx="10" cy="10" r="5"
            fill="white" stroke="{_COLOR}" stroke-width="3"/>
    """,
    "Transfer Station": f"""
    <circle cx="10" cy="10" r="7"
            fill="white" stroke="{_COLOR}" stroke-width="3"/>
    <path d="M 10 3
             A 7 7 0 0 0 10 17
             Z"
          fill="{_COLOR}"/>
    <line x1="10" y1="3" x2="10" y2="17"
          stroke="{_COLOR}" stroke-width="1.2"/>
    """,
    "Terminal Stop": f"""
    <circle cx="10" cy="10" r="7"
            fill="white" stroke="{_COLOR}" stroke-width="2.2"/>
    <circle cx="10" cy="10" r="2.6"
            fill="{_COLOR}" stroke="white" stroke-width="0.8"/>
    """,
    "Operational Facility": f"""
    <circle cx="10" cy="10" r="2.4"
            fill="{_COLOR}"/>
    """,
}


def symbol_html(category):
    """Station-type symbol, falling back to the asterisk for unknowns."""

    body = SYMBOLS.get(category, _ASTERISK_IN_CIRCLE)

    return f"""
        <svg width="20" height="20" viewBox="0 0 20 20" style="display:block;">
        {body}
        </svg>
        """


def add_lanes(builder):
    group = builder.group("bus_lanes")

    folium.GeoJson(
        builder.data.bus_lanes,
        name="Bus lanes",
        style_function=lambda feature: {
            "color": palette.BUS_LANE_COLOR,
            "weight": 0.9,
            "opacity": 1,
        },
    ).add_to(group)

    group.add_to(builder.map)


def add_stops(builder):
    parent = builder.group("bus_stops")
    simple = builder.group("bus_stops_simple")
    outer = builder.group("bus_stops_outer")
    symbols = builder.group("bus_stops_symbols")

    for row, point in points(builder.data.bus_stops):
        line_count = row.get("line_count", 0)
        raw_type = row.get("type", "")
        category = bus_stop_symbol_category(raw_type)

        tooltip = f"""
    <b>{row.get("onomastasi", "")}</b><br>
    Code: {row.get("code", "")}<br>
    Type: {raw_type}<br>
    Symbol category: {category}<br>
    Prepared category: {row.get("stop_type_cat", "Unknown")}<br>
    Municipality / area: {row.get("dimoskal", "")}<br>
    Lines: {row.get("lines_ejyp", "")}<br>
    Line count: {line_count}<br>
    Service level: {row.get("service_level", "Unknown service")}
    """

        location = [point.y, point.x]

        folium.CircleMarker(
            location=location,
            pane=TRANSPORT_PANE,
            radius=2.3,
            color=palette.BUS_STOP_SIMPLE_COLOR,
            weight=0.8,
            fill=True,
            fill_color=palette.BUS_STOP_SIMPLE_COLOR,
            fill_opacity=0.85,
            opacity=0.9,
            tooltip=folium.Tooltip(tooltip, sticky=True),
        ).add_to(simple)

        circle(
            location=location,
            radius=outer_radius(line_count),
            color=palette.BUS_STOP_OUTER_COLOR,
            group=outer,
            tooltip=tooltip,
            pane=TRANSPORT_PANE,
        )

        symbol_marker(
            location=location,
            html=symbol_html(category),
            size=20,
            group=symbols,
            tooltip=tooltip,
            pane=TRANSPORT_PANE,
        )

    parent.add_to(builder.map)
    simple.add_to(builder.map)
    outer.add_to(builder.map)
    symbols.add_to(builder.map)
