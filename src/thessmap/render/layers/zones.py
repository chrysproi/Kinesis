"""The Urban / Metropolitan / Regional frame.

The spine of the project: these units dissolve into the study boundary
that every other layer is clipped to.
"""

import folium

from ... import palette


def zone_style(feature):
    style = palette.ZONE_STYLES.get(
        feature["properties"]["zone"], palette.DEFAULT_ZONE_STYLE
    )
    return {"weight": 0.5, **style}


def add(builder):
    data = builder.data
    group = builder.group("zones")

    folium.GeoJson(
        data.units_4326,
        name="Zone polygons",
        style_function=zone_style,
        highlight_function=lambda feature: {
            "weight": 4,
            "color": "#ffffff",
            "fillOpacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME_ENG", "zone"],
            aliases=["Area:", "Zone:"],
            sticky=True,
        ),
    ).add_to(group)

    # Dissolved outline per zone, heavier as the zone narrows
    for zone_name, weight in palette.ZONE_OUTLINE_WEIGHTS.items():
        folium.GeoJson(
            data.zone_outline(zone_name),
            name=f"{zone_name} outer outline",
            style_function=lambda feature,
            color=palette.ZONE_STYLES[zone_name]["color"],
            weight=weight: {
                "fillOpacity": 0,
                "color": color,
                "weight": weight,
                "opacity": 1,
            },
            control=False,
        ).add_to(group)

    group.add_to(builder.map)


def add_hover_layer(builder):
    """
    Invisible layer on top of everything, so area identification keeps
    working once other layers are switched on.

    Added after the themed layers, which is why it is separate.
    """

    folium.GeoJson(
        builder.data.units_4326,
        name="Hover / Identify areas",
        style_function=lambda feature: {
            "fillColor": "#000000",
            "color": "#000000",
            "weight": 0,
            "fillOpacity": 0,
            "opacity": 0,
        },
        highlight_function=lambda feature: {
            "fillColor": "#ffffff",
            "color": "#ffffff",
            "weight": 4,
            "fillOpacity": 0.35,
            "opacity": 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME_ENG", "zone"],
            aliases=["Area:", "Zone:"],
            sticky=True,
        ),
        control=False,
    ).add_to(builder.map)
