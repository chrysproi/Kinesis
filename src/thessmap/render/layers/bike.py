"""Bike lanes, parking and rental.

Primary lanes show whenever the layer is on. Secondary lanes and the
clustered bike points are street-level detail, gated by the registry.
"""

import folium
from folium.plugins import MarkerCluster

from ... import config, palette
from .. import svg
from ..markers import icon_container, points, symbol_marker

CLUSTER_ICON_JS = """
    function(cluster) {
        var count = cluster.getChildCount();

        return L.divIcon({
            html: '<div style="background:%s; color:white; width:26px; height:26px; border-radius:50%%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:bold; border:2px solid white; box-shadow:0 1px 4px rgba(0,0,0,0.35);">' + count + '</div>',
            className: 'bike-cluster-icon',
            iconSize: L.point(26, 26)
        });
    }
    """ % palette.BIKE_CLUSTER_COLOR


def add(builder):
    data = builder.data
    lanes = builder.group("bike_lanes")
    detail = builder.group("bike_detail")

    folium.GeoJson(
        data.bike_lanes_primary,
        name="Primary bike lanes",
        style_function=lambda feature: {
            "color": palette.BIKE_COLOR,
            "weight": palette.PRIMARY_BIKE_WEIGHT,
            "opacity": 1,
        },
    ).add_to(lanes)

    folium.GeoJson(
        data.bike_lanes_secondary,
        name="Secondary bike lanes",
        style_function=lambda feature: {
            "color": palette.BIKE_COLOR,
            "weight": palette.SECONDARY_BIKE_WEIGHT,
            "opacity": 1,
            "dashArray": palette.SECONDARY_BIKE_DASH,
        },
    ).add_to(detail)

    cluster = MarkerCluster(
        name="Bike parking / rental",
        overlay=True,
        control=False,
        show=True,
        max_cluster_radius=30,
        disable_clustering_at_zoom=18,
        spiderfy_on_max_zoom=True,
        show_coverage_on_hover=False,
        zoom_to_bounds_on_click=True,
        icon_create_function=CLUSTER_ICON_JS,
    ).add_to(detail)

    icons = {
        "parking": svg.inline(
            config.ICONS / "bike_parking.svg",
            palette.BIKE_COLOR,
            size=palette.BIKE_ICON_SIZE,
            viewbox="0 0 14 14",
        ),
        "rental": svg.inline(
            config.ICONS / "bike_rental.svg",
            palette.BIKE_COLOR,
            size=palette.BIKE_ICON_SIZE,
            viewbox="0 0 14 14",
        ),
    }

    for layer, kind in [(data.bike_parking, "parking"), (data.bike_rental, "rental")]:
        for _row, point in points(layer):
            symbol_marker(
                location=[point.y, point.x],
                html=icon_container(palette.BIKE_SYMBOL_SIZE, icons[kind]),
                size=palette.BIKE_SYMBOL_SIZE,
                group=cluster,
                class_name=f"bike-{kind}-icon",
            )

    lanes.add_to(builder.map)
    detail.add_to(builder.map)
