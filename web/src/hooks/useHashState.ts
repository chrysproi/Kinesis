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

// Opens at the floor zoom, where the study area fills the view
const DEFAULT_VIEW: View = {
  zoom: MAP_CONFIG.minZoom,
  lat: MAP_CONFIG.center[1],
  lon: MAP_CONFIG.center[0],
};

const KNOWN = new Set(TOGGLE_LAYERS.map((layer) => layer.id));

/**
 * What is on before the URL says anything.
 *
 * The hash carries the difference from this rather than the whole set.
 * Writing every active id put 24 layer names in the address bar for a
 * view one click from the default — 400 characters, past what several
 * chat clients link without truncating, and unreadable as a share.
 *
 * Pinned layers are left out entirely: they have no switch, showOnly
 * forces them on regardless, so naming them says nothing.
 */
const DEFAULT_ON = TOGGLE_LAYERS.filter(
  (layer) => layer.show && !PINNED_LAYERS.includes(layer.id),
).map((layer) => layer.id);

/**
 * The defaults *at a given zoom*, which is not the same list everywhere:
 * an auto-hiding layer is on by default at the overview and off by
 * default below it.
 *
 * Zoom has to enter into this or the deep-link case cannot be written
 * down at all. Held against the flat defaults, "zones on at z14" encodes
 * to nothing — zones is a default — so the first hash rewrite dropped
 * the one fact the link existed to carry, and the layer closed itself on
 * arrival. Against the zoom-aware baseline the same state encodes to
 * `+zones`, which survives every rewrite.
 */
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

/**
 * The active set a layer segment describes.
 *
 * Two forms are read. A signed list is the difference from the defaults,
 * which is what this writes. An unsigned list is the absolute set, which
 * is what it used to write — links already shared in that form keep
 * resolving to the same map.
 */
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

  // Deliberately not null when empty: "everything off" is a state a
  // reader can reach and share, and falling back to the defaults there
  // would switch six layers back on behind their back.
  return [...active];
}

/**
 * Reads the initial view and active layers out of the URL hash, in the
 * form #zoom/lat/lon/-off,+on. Sharing the address bar shares the exact
 * view — the single most useful thing a map app can do.
 */
export function readHash(): {
  view: View;
  layers: string[] | null;
  /** False on a bare URL, so the map can fit the study area instead. */
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

/** Keeps the hash in step with the map view and active layers. */
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
