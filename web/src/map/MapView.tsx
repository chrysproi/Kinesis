import { useEffect, useRef, useState } from "react";
import { Map as MapLibreMap, NavigationControl, ScaleControl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// Must run before a Map is constructed
import "./worker";

import { MAP_CONFIG, MAP_LAYERS } from "../generated/layerRegistry";
import { readHash, useHashState, type View } from "../url/useHashState";
import { useMapStore } from "../layers/store";
import { basemapStyle } from "./basemap";
import { loadIcons } from "./icons/registerIcons";
import {
  addDeferred,
  addThematicLayers,
  clusterSyncs,
} from "./layers/addLayers";
import {
  attachInteraction,
  clickableLayers,
  parentOf,
} from "./interactions/featureClick";

interface MapViewProps {
  onReady?: (flyToZoom: (zoom: number) => void) => void;
}

/** The map's lifecycle: create it, fill it, keep it in step with the store. */
export default function MapView({ onReady }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [ready, setReady] = useState(false);

  const visible = useMapStore((state) => state.visible);
  const setZoom = useMapStore((state) => state.setZoom);
  const showOnly = useMapStore((state) => state.showOnly);

  useHashState(view);

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

    instance.addControl(
      new NavigationControl({ visualizePitch: true }),
      "bottom-right",
    );
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
      attachInteraction(instance, clickableLayers());
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const instance = map.current;
    if (!instance || !ready) return;

    for (const layer of MAP_LAYERS) {
      const on = visible[parentOf(layer)];

      // A deferred source is fetched the first time its layer is asked
      // for, and never if it is not. Switching one off does not unload
      // it: a toggle flicked twice should not re-download 61 MB.
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
