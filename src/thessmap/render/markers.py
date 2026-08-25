"""Marker and symbol construction.

Replaces the Marker + DivIcon block that was repeated for metro, ferry,
parking, taxi, education, culture and bus stop symbols.
"""

import folium


def icon_container(size, inner_html, opacity=None):
    """Square flexbox wrapper centring a symbol inside a DivIcon."""

    opacity_css = "" if opacity is None else f"opacity:{opacity};"

    return f"""
    <div style="
        width:{size}px;
        height:{size}px;
        display:flex;
        align-items:center;
        justify-content:center;
        box-sizing:border-box;
        {opacity_css}
    ">
        {inner_html}
    </div>
    """


def image_symbol(data_uri, size, opacity=None):
    """Icon container holding a data-URI image."""

    opacity_css = "" if opacity is None else f"opacity:{opacity};"

    image = f"""<img src="{data_uri}"
             style="
                width:{size}px;
                height:{size}px;
                display:block;
                {opacity_css}
             ">"""

    return icon_container(size, image, opacity=opacity)


def symbol_marker(location, html, size, group, tooltip=None, pane=None,
                  class_name=None):
    """Add a DivIcon marker centred on `location`."""

    icon_kwargs = {
        "icon_size": (size, size),
        "icon_anchor": (int(size / 2), int(size / 2)),
        "html": html,
    }

    if class_name is not None:
        icon_kwargs["class_name"] = class_name

    marker_kwargs = {"location": location, "icon": folium.DivIcon(**icon_kwargs)}

    if tooltip is not None:
        marker_kwargs["tooltip"] = folium.Tooltip(tooltip, sticky=True)

    if pane is not None:
        marker_kwargs["pane"] = pane

    return folium.Marker(**marker_kwargs).add_to(group)


def circle(location, radius, color, group, tooltip=None, pane=None,
           fill_opacity=0.35, opacity=0, weight=0):
    """Filled circle marker, used for service-intensity halos."""

    kwargs = {
        "location": location,
        "radius": radius,
        "color": color,
        "weight": weight,
        "fill": True,
        "fill_color": color,
        "fill_opacity": fill_opacity,
        "opacity": opacity,
    }

    if tooltip is not None:
        kwargs["tooltip"] = folium.Tooltip(tooltip, sticky=True)

    if pane is not None:
        kwargs["pane"] = pane

    return folium.CircleMarker(**kwargs).add_to(group)


def points(gdf):
    """Iterate rows carrying a usable Point geometry."""

    for _, row in gdf.iterrows():
        geom = row.geometry

        if geom is None or geom.is_empty or geom.geom_type != "Point":
            continue

        yield row, geom


def polygons(gdf):
    """Iterate rows carrying polygon geometry, with an interior point."""

    for _, row in gdf.iterrows():
        geom = row.geometry

        if geom is None or geom.is_empty:
            continue

        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            continue

        yield row, geom.representative_point()
