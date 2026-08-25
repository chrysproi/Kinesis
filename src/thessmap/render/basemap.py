"""Base map creation and draw-order panes."""

import folium

from .. import config

PANES = [
    ("zones_fill_pane", 350),
    ("culture_polygon_pane", 550),
    ("culture_line_pane", 560),
    ("education_polygon_pane", 580),
    ("transport_points_pane", 600),
    ("culture_symbol_pane", 605),
    ("education_symbol_pane", 610),
    ("parking_pane", 620),
    ("zones_outline_pane", 700),
]

FOCUS_OUTLINE_CSS = """
<style>
.leaflet-interactive:focus {
    outline: none !important;
}
</style>
"""


def create_map(center=None, zoom=None):
    """Base map with the Positron no-labels basemap and custom panes."""

    m = folium.Map(
        location=list(center or config.MAP_CENTER),
        zoom_start=zoom or config.DEFAULT_ZOOM,
        tiles=None,
    )

    folium.TileLayer(
        tiles=config.BASEMAP_TILES,
        attr=config.BASEMAP_ATTRIBUTION,
        name=config.BASEMAP_NAME,
        control=True,
    ).add_to(m)

    m.get_root().html.add_child(folium.Element(FOCUS_OUTLINE_CSS))

    for pane_name, z_index in PANES:
        folium.map.CustomPane(pane_name, z_index=z_index).add_to(m)

    return m
