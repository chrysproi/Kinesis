import { Popup, type Map as MapLibreMap, type Point } from "maplibre-gl";

import { MAP_LAYERS, TOGGLE_LAYERS } from "../../generated/layerRegistry";
import { featurePopupHtml } from "./popup";

const LABEL_BY_ID = new Map(TOGGLE_LAYERS.map((l) => [l.id, l.label]));

/** Which sidebar toggle owns a given map layer. */
export const parentOf = (layer: (typeof MAP_LAYERS)[number]) =>
  layer.metadata["thessmap:parent"];

/** The card's eyebrow: what kind of thing was clicked. */
const kindOf = (layer: (typeof MAP_LAYERS)[number]) =>
  LABEL_BY_ID.get(parentOf(layer));

/** The layers a click can land on, topmost last. */
export const clickableLayers = () =>
  MAP_LAYERS.filter((layer) => layer.metadata["thessmap:interactive"]).map(
    (layer) => layer.id,
  );

/**
 * One map-level click handler, not one per layer.
 *
 * Bus stops stack a halo, a dot and a symbol at the same coordinate, so
 * per-layer handlers fired three times for one click and opened three
 * identical popups. Querying at the point instead returns the topmost
 * feature once, and one reused Popup means no stacking.
 */
export function attachInteraction(instance: MapLibreMap, layers: string[]) {
  const popup = new Popup({ closeButton: true, maxWidth: "none", offset: 10 });

  // Keyed by plain string: MAP_LAYERS is `as const`, so inferring the key
  // type would give a literal union a runtime feature.layer.id cannot be
  // assigned to.
  const layerById = new Map<string, (typeof MAP_LAYERS)[number]>(
    MAP_LAYERS.map((layer) => [layer.id, layer]),
  );

  const topmost = (point: Point) => {
    const present = layers.filter((id) => instance.getLayer(id));
    return instance.queryRenderedFeatures(point, { layers: present })[0];
  };

  instance.on("click", (event) => {
    const feature = topmost(event.point);

    if (!feature) {
      popup.remove();
      return;
    }

    const layer = layerById.get(feature.layer.id);
    const html = featurePopupHtml(
      feature.properties ?? {},
      layer ? kindOf(layer) : undefined,
    );

    if (!html) return;

    popup.setLngLat(event.lngLat).setHTML(html).addTo(instance);
  });

  instance.on("mousemove", (event) => {
    instance.getCanvas().style.cursor = topmost(event.point) ? "pointer" : "";
  });
}
