"""The map builder.

Holds the Folium map, the data source and the feature groups, and wires
zoom rules automatically from the registry. Layer modules never mention a
zoom number: they ask for a group by id, and the threshold comes from
`registry.py`.
"""

import folium

from .. import registry
from ..data import MapData
from .basemap import create_map
from .zoom import ZoomDisplay, ZoomRangeVisibility, ZoomRule


class MapBuilder:
    """Assembles the map one themed layer at a time."""

    def __init__(self, data=None, center=None, zoom=None, show_all=False):
        self.data = data if data is not None else MapData()
        self.map = create_map(center=center, zoom=zoom)
        self.groups = {}

        # Most layers default to off, which is right for the finished map
        # but useless in a preview of one theme. show_all switches every
        # parent layer on so a subset is visible without clicking.
        self.show_all = show_all

    # ---------------------------------------------- groups

    def group(self, layer_id):
        """
        Feature group for a registry layer, created on first request.

        Parent layers appear in the layer menu. Detail layers are hidden
        from it and driven by zoom instead.
        """

        if layer_id in self.groups:
            return self.groups[layer_id]

        spec = registry.spec(layer_id)

        group = folium.FeatureGroup(
            name=spec.label,
            show=spec.show or (self.show_all and not spec.is_detail),
            control=not spec.is_detail,
        )

        self.groups[layer_id] = group

        return group

    def add_groups(self, *layer_ids):
        """Attach groups to the map, in the order given."""

        for layer_id in layer_ids:
            self.group(layer_id).add_to(self.map)

    # ---------------------------------------------- assembly

    def zoom_rules(self):
        """Build zoom rules from the registry for whatever was created."""

        rules = []

        for spec in registry.DETAILS:
            if spec.id not in self.groups or spec.parent not in self.groups:
                continue

            rules.append(
                ZoomRule(
                    parent=self.groups[spec.parent],
                    target=self.groups[spec.id],
                    min_zoom=spec.min_zoom,
                    max_zoom=spec.max_zoom,
                )
            )

        return rules

    def finish(self, zoom_display=True, layer_control=True):
        """Install zoom rules and the layer control. Call once, last."""

        if zoom_display:
            self.map.add_child(ZoomDisplay())

        rules = self.zoom_rules()

        if rules:
            self.map.add_child(ZoomRangeVisibility(rules))

        if layer_control:
            folium.LayerControl(position="bottomright", collapsed=False).add_to(self.map)

        return self.map

    def save(self, path=None):
        """Write the map to HTML and return the path."""

        from .. import config

        path = path or config.OUTPUTS / config.MAP_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)

        self.map.save(str(path))

        return path
