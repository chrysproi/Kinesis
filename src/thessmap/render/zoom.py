"""Zoom-driven layer visibility.

The original notebook carried four MacroElement classes for this. Two
were never instantiated at all, and a third was a strict subset of the
fourth — so one class does the whole job.

A rule shows its target group only while the parent group is switched on
AND the current zoom sits inside [min_zoom, max_zoom). Either bound may
be None, meaning unbounded on that side.
"""

from dataclasses import dataclass

import folium
from branca.element import MacroElement, Template


@dataclass(frozen=True)
class ZoomRule:
    parent: folium.FeatureGroup
    target: folium.FeatureGroup
    min_zoom: int | None = None
    max_zoom: int | None = None


class ZoomDisplay(MacroElement):
    """Corner box showing the current zoom level."""

    def __init__(self):
        super().__init__()
        self._template = Template("""
        {% macro script(this, kwargs) %}
        var map = {{ this._parent.get_name() }};

        var zoomBox = L.control({position: 'bottomleft'});

        zoomBox.onAdd = function(map) {
            var div = L.DomUtil.create('div', 'zoom-display-box');
            div.style.background = 'white';
            div.style.padding = '6px 8px';
            div.style.border = '1px solid #999';
            div.style.borderRadius = '4px';
            div.style.fontSize = '12px';
            div.style.fontFamily = 'Arial, sans-serif';
            div.style.boxShadow = '0 1px 4px rgba(0,0,0,0.25)';
            div.innerHTML = 'Zoom: ' + map.getZoom();
            return div;
        };

        zoomBox.addTo(map);

        map.on('zoomend', function() {
            var zoomElement = document.querySelector('.zoom-display-box');
            if (zoomElement) {
                zoomElement.innerHTML = 'Zoom: ' + map.getZoom();
            }
        });
        {% endmacro %}
        """)


class ZoomRangeVisibility(MacroElement):
    """Installs every zoom rule as one block of JavaScript."""

    def __init__(self, rules):
        super().__init__()

        def js_value(value):
            return "null" if value is None else str(value)

        self.rules_js = "".join(
            f"""
            {{
                parentGroup: {rule.parent.get_name()},
                targetGroup: {rule.target.get_name()},
                minZoom: {js_value(rule.min_zoom)},
                maxZoom: {js_value(rule.max_zoom)}
            }},
            """
            for rule in rules
        )

        self._template = Template("""
        {% macro script(this, kwargs) %}
        var map = {{ this._parent.get_name() }};

        var zoomRangeRules = [
            {{ this.rules_js | safe }}
        ];

        function updateZoomRangeGroups() {
            var zoom = map.getZoom();

            zoomRangeRules.forEach(function(rule) {
                var parentIsOn = map.hasLayer(rule.parentGroup);

                var aboveMin = rule.minZoom === null || zoom >= rule.minZoom;
                var belowMax = rule.maxZoom === null || zoom < rule.maxZoom;

                var shouldShow = parentIsOn && aboveMin && belowMax;

                if (shouldShow) {
                    if (!map.hasLayer(rule.targetGroup)) {
                        rule.targetGroup.addTo(map);
                    }
                } else {
                    if (map.hasLayer(rule.targetGroup)) {
                        map.removeLayer(rule.targetGroup);
                    }
                }
            });
        }

        map.on('zoomend', updateZoomRangeGroups);

        map.on('overlayadd', function() {
            setTimeout(updateZoomRangeGroups, 150);
        });

        map.on('overlayremove', function() {
            setTimeout(updateZoomRangeGroups, 150);
        });

        setTimeout(updateZoomRangeGroups, 500);
        {% endmacro %}
        """)
