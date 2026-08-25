"""Education and culture.

Both arrive as a mix of polygons and points from several sources, so the
preparation step derives one symbol point per feature. Polygons show from
zoom 15, symbols from 17.
"""

import folium

from ... import config, palette
from ...fields import name_of
from .. import svg
from ..markers import image_symbol, points, symbol_marker

EDUCATION_POLYGON_PANE = "education_polygon_pane"
EDUCATION_SYMBOL_PANE = "education_symbol_pane"
CULTURE_POLYGON_PANE = "culture_polygon_pane"
CULTURE_LINE_PANE = "culture_line_pane"
CULTURE_SYMBOL_PANE = "culture_symbol_pane"


def add_education(builder):
    parent = builder.group("education")
    polygon_group = builder.group("education_polygons")
    symbol_group = builder.group("education_symbols")

    folium.GeoJson(
        builder.data.education_polygons,
        name="Education polygons",
        control=False,
        pane=EDUCATION_POLYGON_PANE,
        style_function=lambda feature: {
            "fillColor": palette.EDUCATION_COLOR,
            "color": palette.EDUCATION_COLOR,
            "weight": 1,
            "fillOpacity": palette.EDUCATION_FILL_OPACITY,
            "opacity": 0.45,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["education_type"], aliases=["Type:"], sticky=True
        ),
    ).add_to(polygon_group)

    icon = svg.recolor_params(
        config.ICONS / "education-svgrepo-com.svg", palette.EDUCATION_SYMBOL_COLOR
    )
    html = image_symbol(icon, palette.EDUCATION_SYMBOL_SIZE)

    for row, point in points(builder.data.education_symbols):
        symbol_marker(
            location=[point.y, point.x],
            html=html,
            size=palette.EDUCATION_SYMBOL_SIZE,
            group=symbol_group,
            tooltip=f"""
    <b>{name_of(row, "Education facility")}</b><br>
    Type: {row.get("education_type", "Education")}
    """,
            pane=EDUCATION_SYMBOL_PANE,
        )

    parent.add_to(builder.map)
    polygon_group.add_to(builder.map)
    symbol_group.add_to(builder.map)


def culture_icons():
    """One recoloured data URI per culture subtype."""

    return {
        subtype: svg.recolor_all(
            config.ICONS / "culture" / filename, palette.CULTURE_SYMBOL_COLOR
        )
        for subtype, filename in palette.CULTURE_ICON_FILES.items()
    }


def add_culture(builder):
    parent = builder.group("culture")
    polygon_group = builder.group("culture_polygons")
    line_group = builder.group("culture_lines")
    symbol_group = builder.group("culture_symbols")

    folium.GeoJson(
        builder.data.culture_polygons,
        name="Culture polygons",
        control=False,
        pane=CULTURE_POLYGON_PANE,
        style_function=lambda feature: {
            "fillColor": palette.CULTURE_COLOR,
            "color": "transparent",
            "weight": 0,
            "fillOpacity": palette.CULTURE_FILL_OPACITY,
            "opacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["culture_subtype"], aliases=["Type:"], sticky=True
        ),
    ).add_to(polygon_group)

    folium.GeoJson(
        builder.data.culture_lines,
        name="Culture lines",
        control=False,
        pane=CULTURE_LINE_PANE,
        style_function=lambda feature: {
            "color": palette.CULTURE_LINE_COLOR,
            "weight": palette.CULTURE_LINE_WEIGHT,
            "opacity": palette.CULTURE_LINE_OPACITY,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["culture_subtype"], aliases=["Type:"], sticky=True
        ),
    ).add_to(line_group)

    icons = culture_icons()
    unknown_subtypes = set()

    for row, point in points(builder.data.culture_symbols):
        subtype = row.get("culture_subtype", "Culture")

        if subtype not in icons:
            unknown_subtypes.add(subtype)
            subtype = palette.CULTURE_FALLBACK_SUBTYPE

        symbol_marker(
            location=[point.y, point.x],
            html=image_symbol(
                icons[subtype],
                palette.CULTURE_SYMBOL_SIZE,
                opacity=palette.CULTURE_SYMBOL_OPACITY,
            ),
            size=palette.CULTURE_SYMBOL_SIZE,
            group=symbol_group,
            tooltip=f"""
    <b>{name_of(row, "Culture place")}</b><br>
    Type: {row.get("culture_subtype", "Culture")}<br>
    Origin: {row.get("symbol_origin", "")}
    """,
            pane=CULTURE_SYMBOL_PANE,
        )

    if unknown_subtypes:
        # Reported once rather than per feature, as the notebook did
        print(f"  culture subtypes without an icon: {sorted(unknown_subtypes)}")

    parent.add_to(builder.map)
    polygon_group.add_to(builder.map)
    line_group.add_to(builder.map)
    symbol_group.add_to(builder.map)
