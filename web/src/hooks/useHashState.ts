import { useEffect, useRef } from "react";

import {
  AUTO_HIDE,
  MAP_CONFIG,
  PINNED_LAYERS,
  TOGGLE_LAYERS,
} from "../generated/layers";
import { activeIds, useMapStore } from "../store";

export interface View {
  zoom: number;
  lat: number;
  lon: number;
}

const DEFAULT_VIEW: View = {
  zoom: MAP_CONFIG.minZoom,
  lat: MAP_CONFIG.center[1],
  lon: MAP_CONFIG.center[0],
};

const KNOWN = new Set(TOGGLE_LAYERS.map((layer) => layer.id));

const DEFAULT_ON = TOGGLE_LAYERS.filter(
  (layer) => layer.show && !PINNED_LAYERS.includes(layer.id),
).map((layer) => layer.id);

/** An auto-hiding layer is a default at the overview and not below it. */
const defaultsAt = (zoom: number) =>
  DEFAULT_ON.filter((id) => !(id in AUTO_HIDE) || zoom <= AUTO_HIDE[id]);

/** The layer segment: `-off,+on`, empty when nothing differs. */
function encodeLayers(active: string[], zoom: number) {
  const on = new Set(active);
  const base = defaultsAt(zoom);
  const isDefault = new Set(base);

  return [
    ...base.filter((id) => !on.has(id)).map((id) => `-${id}`),
    ...active
      .filter((id) => !isDefault.has(id) && !PINNED_LAYERS.includes(id))
      .map((id) => `+${id}`),
  ].join(",");
}

/** Signed tokens are a difference from the defaults; unsigned is the whole set. */
function decodeLayers(segment: string, zoom: number): string[] | null {
  const tokens = segment.split(",").filter(Boolean);
  if (tokens.length === 0) return null;

  if (!tokens.some((token) => token[0] === "+" || token[0] === "-")) {
    const known = tokens.filter((id) => KNOWN.has(id));
    return known.length ? known : null;
  }

  const active = new Set(defaultsAt(zoom));

  for (const token of tokens) {
    const id = token.slice(1);
    if (!KNOWN.has(id)) continue;
    if (token[0] === "-") active.delete(id);
    else active.add(id);
  }

  return [...active];
}

/** Reads #zoom/lat/lon/-off,+on. */
export function readHash(): {
  view: View;
  layers: string[] | null;
  fromHash: boolean;
} {
  const raw = window.location.hash.replace(/^#/, "");
  if (!raw) return { view: DEFAULT_VIEW, layers: null, fromHash: false };

  const [zoom, lat, lon, layers] = raw.split("/");
  const numbers = [zoom, lat, lon].map(Number);

  const view = numbers.every((n) => Number.isFinite(n))
    ? { zoom: numbers[0], lat: numbers[1], lon: numbers[2] }
    : DEFAULT_VIEW;

  return {
    view,
    layers: layers ? decodeLayers(layers, view.zoom) : null,
    fromHash: true,
  };
}

export function useHashState(view: View | null) {
  const visible = useMapStore((state) => state.visible);
  const frame = useRef<number>(0);

  useEffect(() => {
    if (!view) return;

    cancelAnimationFrame(frame.current);
    frame.current = requestAnimationFrame(() => {
      const ids = encodeLayers(activeIds(visible), view.zoom);
      const hash =
        `#${view.zoom.toFixed(2)}/${view.lat.toFixed(5)}/` +
        `${view.lon.toFixed(5)}${ids ? `/${ids}` : ""}`;

      window.history.replaceState(null, "", hash);
    });

    return () => cancelAnimationFrame(frame.current);
  }, [view, visible]);
}
