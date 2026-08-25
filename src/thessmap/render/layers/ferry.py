"""Ferry routes and terminals."""

import folium

from ... import palette
from ...fields import name_of
from ..markers import points, symbol_marker


def terminal_symbol_html(size=palette.FERRY_TERMINAL_SIZE):
    """Outer ring with a central dot."""

    color = palette.FERRY_TERMINAL_COLOR

    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 20 20" style="display:block;">
        <circle cx="10" cy="10" r="7"
                fill="white" stroke="{color}" stroke-width="1.8"/>
        <circle cx="10" cy="10" r="2.2"
                fill="{color}" stroke="none"/>
    </svg>
    """


def add_routes(builder):
    group = builder.group("ferry_routes")

    folium.GeoJson(
        builder.data.ferry_routes,
        name="Ferry routes",
        style_function=lambda feature: {
            "color": palette.FERRY_ROUTE_COLOR,
            "weight": palette.FERRY_ROUTE_WEIGHT,
            "opacity": palette.FERRY_ROUTE_OPACITY,
            "dashArray": palette.FERRY_ROUTE_DASH,
        },
        tooltip=folium.Tooltip("Ferry route"),
    ).add_to(group)

    group.add_to(builder.map)


def add_terminals(builder):
    parent = builder.group("ferry_terminals")
    symbols = builder.group("ferry_terminals_symbols")

    for row, point in points(builder.data.ferry_terminals):
        terminal_name = name_of(row, "Ferry terminal")

        symbol_marker(
            location=[point.y, point.x],
            html=terminal_symbol_html(),
            size=palette.FERRY_TERMINAL_SIZE,
            group=symbols,
            tooltip=f"""
    <b>{terminal_name}</b><br>
    Ferry terminal
    """,
        )

    parent.add_to(builder.map)
    symbols.add_to(builder.map)
