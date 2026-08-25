"""Lakes, water network, buildings and street trees."""

import folium

from ... import palette


def add_lakes(builder):
    data = builder.data
    group = builder.group("lakes")

    folium.GeoJson(
        data.selected_lakes,
        name="Lake polygons",
        style_function=lambda feature: {
            "fillColor": palette.WATER_FILL,
            "color": palette.WATER_EDGE,
            "weight": 1,
            "fillOpacity": 0.8,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name"], aliases=["Lake:"], sticky=True
        ),
    ).add_to(group)

    for _, row in data.selected_lakes.iterrows():
        point = row.geometry.representative_point()
        lat_offset, lon_offset = palette.LAKE_LABEL_OFFSETS.get(row["name"], (0, 0))

        folium.Marker(
            location=[point.y + lat_offset, point.x + lon_offset],
            icon=folium.DivIcon(
                html=f"""
            <div style="
                font-size: 10px;
                color: {palette.LAKE_LABEL_COLOR};
                font-style: italic;
                font-weight: 500;
                white-space: nowrap;
                text-shadow: 1px 1px 2px white;
            ">
                {row['name']}
            </div>
            """
            ),
        ).add_to(group)

    group.add_to(builder.map)


def add_water(builder):
    data = builder.data
    group = builder.group("water")

    folium.GeoJson(
        data.water_lines,
        name="Water lines",
        style_function=lambda feature: {
            "color": palette.WATER_LINE_COLOR,
            "weight": 0.7,
            "opacity": 0.8,
        },
    ).add_to(group)

    folium.GeoJson(
        data.water_polygons,
        name="Water polygons",
        style_function=lambda feature: {
            "fillColor": palette.WATER_FILL,
            "color": palette.WATER_EDGE,
            "weight": 0.8,
            "fillOpacity": 0.85,
            "opacity": 1,
        },
    ).add_to(group)

    group.add_to(builder.map)


def add_buildings(builder):
    group = builder.group("buildings")

    folium.GeoJson(
        builder.data.buildings,
        name="Building footprints",
        style_function=lambda feature: {
            "fillColor": palette.BUILDING_FILL,
            "color": palette.BUILDING_EDGE,
            "weight": 0.2,
            "fillOpacity": 0.45,
            "opacity": 0.6,
        },
    ).add_to(group)

    group.add_to(builder.map)


def add_trees(builder):
    """
    One GeoJson layer per height class.

    The densest layer on the map, so the registry gates it to zoom 18.
    """

    trees = builder.data.trees

    if "tree_class" not in trees.columns:
        raise RuntimeError(
            "trees layer has no tree_class column. "
            "Re-run the preparation step that classifies trees."
        )

    group = builder.group("trees")
    symbols = builder.group("trees_symbols")

    usable = trees[["tree_class", "geometry"]].copy()
    usable = usable[
        usable.geometry.notna()
        & ~usable.geometry.is_empty
        & usable.geom_type.isin(["Point"])
    ].copy()

    for tree_class, (fill_color, radius) in palette.TREE_CLASSES.items():
        class_trees = usable[usable["tree_class"] == tree_class][["geometry"]].copy()

        if len(class_trees) == 0:
            continue

        folium.GeoJson(
            class_trees,
            name=f"Trees {tree_class}",
            control=False,
            marker=folium.CircleMarker(
                radius=radius,
                color=palette.TREE_EDGE_COLOR,
                weight=0.35,
                fill=True,
                fill_color=fill_color,
                fill_opacity=0.72,
                opacity=0.8,
            ),
        ).add_to(symbols)

    group.add_to(builder.map)
    symbols.add_to(builder.map)
