"""Parking places and taxi ranks."""

import folium

from ... import config, palette
from ...fields import TAXI_NAME_FIELDS, first_non_empty
from .. import svg
from ..markers import image_symbol, points, polygons, symbol_marker

PARKING_PANE = "parking_pane"
TRANSPORT_PANE = "transport_points_pane"


def parking_symbol_html(size=palette.PARKING_SYMBOL_SIZE):
    """Square P sign."""

    color = palette.PARKING_COLOR
    font_size = int(size * 0.72)

    return f"""
    <div style="
        width:{size}px;
        height:{size}px;
        background:transparent;
        border:1.8px solid {color};
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:{font_size}px;
        font-weight:bold;
        color:{color};
        font-family:Arial, sans-serif;
        box-sizing:border-box;
        border-radius:2px;
    ">
        P
    </div>
    """


def add_parking(builder):
    parent = builder.group("parking")
    polygon_group = builder.group("parking_polygons")
    symbol_group = builder.group("parking_symbols")

    folium.GeoJson(
        builder.data.parking_places,
        name="Parking places polygons",
        pane=PARKING_PANE,
        style_function=lambda feature: {
            "fillColor": palette.PARKING_COLOR,
            "color": palette.PARKING_COLOR,
            "weight": 1,
            "fillOpacity": palette.PARKING_FILL_OPACITY,
            "opacity": 0.9,
        },
    ).add_to(polygon_group)

    for _row, point in polygons(builder.data.parking_places):
        symbol_marker(
            location=[point.y, point.x],
            html=parking_symbol_html(),
            size=palette.PARKING_SYMBOL_SIZE,
            group=symbol_group,
            tooltip="""
    <b>Parking place</b>
    """,
            pane=PARKING_PANE,
        )

    parent.add_to(builder.map)
    polygon_group.add_to(builder.map)
    symbol_group.add_to(builder.map)


def add_taxi(builder):
    parent = builder.group("taxi")
    symbols = builder.group("taxi_symbols")

    icon = svg.transparent_background(
        config.ICONS / "taxi-taxi-stop-svgrepo-com.svg"
    )
    html = image_symbol(icon, palette.TAXI_SYMBOL_SIZE)

    for row, point in points(builder.data.taxi_spots):
        taxi_name = first_non_empty(row, TAXI_NAME_FIELDS, "Taxi spot")

        symbol_marker(
            location=[point.y, point.x],
            html=html,
            size=palette.TAXI_SYMBOL_SIZE,
            group=symbols,
            tooltip=f"""
    <b>{taxi_name}</b><br>
    Taxi spot
    """,
            pane=TRANSPORT_PANE,
        )

    parent.add_to(builder.map)
    symbols.add_to(builder.map)
