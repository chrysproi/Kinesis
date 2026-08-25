import type { LayerSpecification, Map as MapLibreMap } from "maplibre-gl";

import {
  CLUSTER_COLOR,
  CLUSTERED_SOURCES,
  LAZY_SOURCES,
  MAP_LAYERS,
  RASTER_SOURCES,
  SOURCE_NAMES,
} from "../../generated/layerRegistry";
import { zoomRange } from "../../layers/zoom";
import { attachClusters } from "./clusters";
import { paintFor } from "./layerStyle";

export type Layer = (typeof MAP_LAYERS)[number];

const DATA_URL = (name: string) =>
  `${import.meta.env.BASE_URL}data/${name}.json`;

const ASSET_URL = (file: string) => `${import.meta.env.BASE_URL}data/${file}`;

/** Cluster badge controllers, so a visibility change can re-sync them. */
export const clusterSyncs: Array<
  { sync: () => void; clear: () => void } | undefined
> = [];

export function addGeoJsonSource(instance: MapLibreMap, name: string) {
  if (instance.getSource(name)) return;

  const cluster = CLUSTERED_SOURCES[name];

  instance.addSource(name, {
    type: "geojson",
    data: DATA_URL(name),
    ...(cluster
      ? {
          cluster: true,
          clusterRadius: cluster.radius,
          clusterMaxZoom: cluster.maxZoom,
        }
      : {}),
  });
}

/**
 * Rasters ship as pre-coloured PNGs behind an image source: MapLibre
 * reads no GeoTIFF, and the PNG is already in Web Mercator, so the four
 * corners place it without any warping in the browser.
 */
function addRasterSources(instance: MapLibreMap) {
  for (const [name, raster] of Object.entries(RASTER_SOURCES)) {
    if (instance.getSource(name)) continue;

    instance.addSource(name, {
      type: "image",
      url: ASSET_URL(raster.url),
      coordinates: raster.coordinates as [
        [number, number],
        [number, number],
        [number, number],
        [number, number],
      ],
    });
  }
}

/**
 * Adds a layer in its generated position rather than on top.
 *
 * A deferred layer arrives after its neighbours, so `addLayer` alone
 * would stack it above everything — putting buildings over the transit
 * network. The `beforeId` is the next already-present layer in generated
 * order, which restores the intended draw order whenever it is added.
 */
export function addLayerAt(instance: MapLibreMap, layer: Layer) {
  if (instance.getLayer(layer.id)) return;

  const index = MAP_LAYERS.indexOf(layer);
  const before = MAP_LAYERS.slice(index + 1).find((next) =>
    instance.getLayer(next.id),
  );

  // Merge into any generated layout rather than replacing it: symbol
  // layers carry icon-image and icon-size there, and overwriting the
  // whole object silently strips the icon with no MapLibre warning.
  const generated = (layer as { layout?: Record<string, unknown> }).layout;
  const tuned = layer as unknown as Parameters<typeof paintFor>[0] &
    Parameters<typeof zoomRange>[0];

  // A symbol layer can carry no paint at all, and MapLibre rejects an
  // explicit `paint: undefined` rather than ignoring it — which drops
  // the layer with a validation error instead of drawing it.
  const paint = paintFor(tuned);

  instance.addLayer(
    {
      ...layer,
      ...zoomRange(tuned),
      ...(paint ? { paint } : {}),
      layout: { ...generated, visibility: "none" },
    } as unknown as LayerSpecification,
    before?.id,
  );
}

/** Fetches a deferred source and adds its layer, on first use. */
export function addDeferred(instance: MapLibreMap, layer: Layer) {
  if (!LAZY_SOURCES.includes(layer.source)) return;

  addGeoJsonSource(instance, layer.source);
  addLayerAt(instance, layer);
}

/** Every generated source and layer, in generated order. */
export function addThematicLayers(instance: MapLibreMap) {
  for (const name of SOURCE_NAMES) {
    if (LAZY_SOURCES.includes(name)) continue;
    addGeoJsonSource(instance, name);
  }

  addRasterSources(instance);

  for (const layer of MAP_LAYERS) {
    if (LAZY_SOURCES.includes(layer.source)) continue;
    addLayerAt(instance, layer);
  }

  for (const name of Object.keys(CLUSTERED_SOURCES)) {
    const owner = MAP_LAYERS.find((layer) => layer.source === name);
    if (!owner) continue;

    clusterSyncs.push(
      attachClusters(instance, name, {
        color: CLUSTER_COLOR,
        isVisible: () =>
          instance.getLayer(owner.id)
            ? instance.getLayoutProperty(owner.id, "visibility") !== "none"
            : false,
      }),
    );
  }
}
