"""Metro line and stations.

Metro stations sit at the top of the transport hierarchy, so they take
the maximum bus-stop service-intensity radius rather than computing one.
The line itself is drawn twice, in two styles, swapped at zoom 14.
"""

import folium

from ... import palette
from ...fields import name_of
from ..markers import circle, points, symbol_marker
from .bus import outer_radius


def station_symbol_html(size):
    """Circular ring with an M."""

    color = palette.METRO_SYMBOL_COLOR
    font_size = int(size * 0.65)

    return f"""
    <div style="
        width:{size}px;
        height:{size}px;
        border-radius:50%;
        background:white;
        border:2px solid {color};
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:{font_size}px;
        font-weight:bold;
        color:{color};
        font-family:Arial, sans-serif;
        line-height:{size}px;
        box-sizing:border-box;
    ">
        M
    </div>
    """


def add_line(builder):
    parent = builder.group("metro_line")
    zoomout = builder.group("metro_line_zoomout")
    zoomin = builder.group("metro_line_zoomin")

    styles = [
        (zoomout, palette.METRO_LINE_WEIGHT_ZOOMOUT,
         palette.METRO_LINE_OPACITY_ZOOMOUT, palette.METRO_LINE_DASH_ZOOMOUT),
        (zoomin, palette.METRO_LINE_WEIGHT_ZOOMIN,
         palette.METRO_LINE_OPACITY_ZOOMIN, palette.METRO_LINE_DASH_ZOOMIN),
    ]

    for group, weight, opacity, dash in styles:
        folium.GeoJson(
            builder.data.metro_line,
            name="Metro line",
            style_function=lambda feature, weight=weight, opacity=opacity, dash=dash: {
                "color": palette.METRO_LINE_COLOR,
                "weight": weight,
                "opacity": opacity,
                "dashArray": dash,
            },
            tooltip=folium.Tooltip("Metro line"),
        ).add_to(group)

    parent.add_to(builder.map)
    zoomout.add_to(builder.map)
    zoomin.add_to(builder.map)


def add_stations(builder):
    parent = builder.group("metro_stations")
    small = builder.group("metro_stations_small")
    outer = builder.group("metro_stations_outer")
    large = builder.group("metro_stations_large")

    radius = outer_radius(palette.METRO_SERVICE_INTENSITY)

    for row, point in points(builder.data.metro_stations):
        station_name = name_of(row, "Metro station")
        location = [point.y, point.x]

        tooltip = f"""
    <b>{station_name}</b><br>
    Metro station<br>
    Service intensity: maximum PT node
    """

        symbol_marker(
            location=location,
            html=station_symbol_html(palette.METRO_SYMBOL_SIZE_SMALL),
            size=palette.METRO_SYMBOL_SIZE_SMALL,
            group=small,
            tooltip=tooltip,
        )

        circle(
            location=location,
            radius=radius,
            color=palette.BUS_STOP_OUTER_COLOR,
            group=outer,
            tooltip=tooltip,
        )

        symbol_marker(
            location=location,
            html=station_symbol_html(palette.METRO_SYMBOL_SIZE_LARGE),
            size=palette.METRO_SYMBOL_SIZE_LARGE,
            group=large,
            tooltip=tooltip,
        )

    parent.add_to(builder.map)
    small.add_to(builder.map)
    outer.add_to(builder.map)
    large.add_to(builder.map)
