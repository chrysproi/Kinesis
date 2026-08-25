import { useEffect, useRef, useState } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  Popup,
  ScaleControl,
} from "maplibre-gl";
// Point is a type only: MapLibre v6 has no default export, so it must
// never be imported as a value.
import type { LayerSpecification, Point } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import {
  CLUSTER_COLOR,
  CLUSTERED_SOURCES,
  LAZY_SOURCES,
  MAP_CONFIG,
  MAP_LAYERS,
  RASTER_SOURCES,
  SOURCE_NAMES,
  TOGGLE_LAYERS,
} from "../generated/layers";
import { readHash, useHashState, type View } from "../hooks/useHashState";
import { useMapStore } from "../store";
import { basemapStyle } from "./basemap";
import { attachClusters } from "./clusters";
import { loadIcons } from "./icons";
import { featurePopupHtml } from "./popup";

const DATA_URL = (name: string) => `${import.meta.env.BASE_URL}data/${name}.geojson`;
const ASSET_URL = (file: string) => `${import.meta.env.BASE_URL}data/${file}`;

/** Which sidebar toggle owns a given map layer. */
const parentOf = (layer: (typeof MAP_LAYERS)[number]) =>
  layer.metadata["thessmap:parent"];

const LABEL_BY_ID = new Map(TOGGLE_LAYERS.map((l) => [l.id, l.label]));

/** The card's eyebrow: what kind of thing was clicked. */
const kindOf = (layer: (typeof MAP_LAYERS)[number]) =>
  LABEL_BY_ID.get(parentOf(layer));

interface MapViewProps {
  /** Hands the parent a way to change zoom, for the sidebar's z-buttons. */
  onReady?: (flyToZoom: (zoom: number) => void) => void;
}

export default function MapView({ onReady }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [ready, setReady] = useState(false);

  const visible = useMapStore((state) => state.visible);
  const setZoom = useMapStore((state) => state.setZoom);
  const showOnly = useMapStore((state) => state.showOnly);

  useHashState(view);

  // ---------------------------------------------- create the map once
  useEffect(() => {
    if (!container.current || map.current) return;

    const { view: initial, layers } = readHash();
    if (layers) showOnly(layers, initial.zoom);

    const instance = new MapLibreMap({
      container: container.current,
      style: basemapStyle(),
      center: [initial.lon, initial.lat],
      zoom: initial.zoom,
      // Clamped to the study area: without this the map happily fetches
      // world tiles for regions we hold no data for.
      maxBounds: MAP_CONFIG.bounds,
      minZoom: MAP_CONFIG.minZoom,
      maxZoom: MAP_CONFIG.maxZoom,
      attributionControl: { compact: true },
    });


    // Bottom-right: the legend occupies the top-right corner
    instance.addControl(new NavigationControl({ visualizePitch: true }), "bottom-right");
    instance.addControl(new ScaleControl({ maxWidth: 120 }), "bottom-left");

    const syncView = () => {
      const centre = instance.getCenter();
      setView({ zoom: instance.getZoom(), lat: centre.lat, lon: centre.lng });
      setZoom(instance.getZoom());
    };

    instance.on("load", async () => {
      // Icons must exist before layers reference them by icon-image
      await loadIcons(instance);
      addThematicLayers(instance);
      setReady(true);
      syncView();
      onReady?.((zoom) => instance.easeTo({ zoom, duration: 600 }));
    });

    instance.on("moveend", syncView);
    instance.on("zoom", () => setZoom(instance.getZoom()));

    map.current = instance;

    return () => {
      instance.remove();
      map.current = null;
    };
    // Basemap changes are handled separately, below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------------------------- visibility
  useEffect(() => {
    const instance = map.current;
    if (!instance || !ready) return;

    for (const layer of MAP_LAYERS) {
      const on = visible[parentOf(layer)];

      // A deferred source is fetched the first time its layer is asked
      // for, and never if it is not. Switching one off does not unload
      // it: a toggle the user flicks twice should not re-download 64 MB.
      if (on && !instance.getLayer(layer.id)) addDeferred(instance, layer);
      if (!instance.getLayer(layer.id)) continue;

      instance.setLayoutProperty(layer.id, "visibility", on ? "visible" : "none");
    }

    for (const controller of clusterSyncs) controller?.sync();
  }, [visible, ready]);


  // Sized directly rather than with `absolute inset-0`: MapLibre's own
  // stylesheet sets `.maplibregl-map { position: relative }` and is
  // injected after Tailwind, so it wins and the inset stops applying.
  return <div ref={container} className="h-full w-full" />;
}

/** Adds every generated source and layer, then wires up click popups. */
function addThematicLayers(instance: MapLibreMap) {
  // Interactive layers, topmost last — the order they were added.
  const clickable = MAP_LAYERS.filter(
    (layer) => layer.metadata["thessmap:interactive"],
  ).map((layer) => layer.id);

  for (const name of SOURCE_NAMES) {
    if (LAZY_SOURCES.includes(name)) continue;
    addGeoJsonSource(instance, name);
  }

  // Rasters ship as pre-coloured PNGs behind an image source: MapLibre
  // reads no GeoTIFF, and the PNG is already in Web Mercator, so the
  // four corners place it without any warping in the browser.
  for (const [name, raster] of Object.entries(RASTER_SOURCES)) {
    if (instance.getSource(name)) continue;

    instance.addSource(name, {
      type: "image",
      url: ASSET_URL(raster.url),
      // Exactly four corners, which the generated type guarantees
      coordinates: raster.coordinates as [
        [number, number],
        [number, number],
        [number, number],
        [number, number],
      ],
    });
  }

  for (const layer of MAP_LAYERS) {
    if (LAZY_SOURCES.includes(layer.source)) continue;
    addLayerAt(instance, layer);
  }

  attachInteraction(instance, clickable);

  // Cluster badges for any source that clusters
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

type Layer = (typeof MAP_LAYERS)[number];

function addGeoJsonSource(instance: MapLibreMap, name: string) {
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
 * Adds a layer in its generated position rather than on top.
 *
 * A deferred layer arrives after its neighbours, so `addLayer` alone
 * would stack it above everything — putting buildings over the transit
 * network. The `beforeId` is the next already-present layer in generated
 * order, which restores the intended draw order whenever it is added.
 */
function addLayerAt(instance: MapLibreMap, layer: Layer) {
  if (instance.getLayer(layer.id)) return;

  const index = MAP_LAYERS.indexOf(layer);
  const before = MAP_LAYERS.slice(index + 1).find((next) =>
    instance.getLayer(next.id),
  );

  // Merge into any generated layout rather than replacing it: symbol
  // layers carry icon-image and icon-size there, and overwriting the
  // whole object silently strips the icon with no MapLibre warning.
  const generated = (layer as { layout?: Record<string, unknown> }).layout;

  instance.addLayer(
    {
      ...layer,
      layout: { ...generated, visibility: "none" },
    } as unknown as LayerSpecification,
    before?.id,
  );
}

/** Fetches a deferred source and adds its layer, on first use. */
function addDeferred(instance: MapLibreMap, layer: Layer) {
  if (!LAZY_SOURCES.includes(layer.source)) return;

  addGeoJsonSource(instance, layer.source);
  addLayerAt(instance, layer);
}

/** Cluster badge controllers, so a visibility change can re-sync them. */
const clusterSyncs: Array<{ sync: () => void; clear: () => void } | undefined> = [];



/**
 * A single map-level click, rather than a handler per layer.
 *
 * Bus stops stack a halo, a dot and a symbol at the same coordinate, so
 * per-layer handlers fired three times for one click and opened three
 * identical popups. Querying at the point instead returns the topmost
 * feature once, and one reused Popup means no stacking.
 */
function attachInteraction(instance: MapLibreMap, layers: string[]) {
  const popup = new Popup({ closeButton: true, maxWidth: "none", offset: 10 });
  // Keyed by plain string: MAP_LAYERS is `as const`, so inferring the
  // key type would give a literal union that a runtime feature.layer.id
  // cannot be assigned to.
  const layerById = new Map<string, (typeof MAP_LAYERS)[number]>(
    MAP_LAYERS.map((layer) => [layer.id, layer]),
  );

  // queryRenderedFeatures returns topmost first, and only from layers
  // that are currently visible.
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
