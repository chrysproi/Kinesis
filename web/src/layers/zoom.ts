import { CONFIG } from "../config/layerConfig";

/** A map layer, as much of one as the zoom model needs to see. */
export interface ZoomedLayer {
  metadata: Record<string, string>;
  minzoom?: number;
  maxzoom?: number;
}

/** The toggle a map layer belongs to, which is what CONFIG is keyed by. */
export const ownerOf = (layer: { metadata: Record<string, string> }) =>
  layer.metadata["thessmap:parent"];

const clamp = (value: number) => Math.max(0, Math.min(24, value));

/**
 * The zoom range a layer should draw in, config applied.
 *
 * `shift` moves every tier together so the staircase survives; `min` and
 * `max` clamp afterwards. Only the bounds that exist are returned: an
 * explicit `minzoom: undefined` is not the same as no minzoom to
 * MapLibre's style validator, which rejects the layer outright.
 */
export function zoomRange(layer: ZoomedLayer) {
  const rule = CONFIG.zoom[ownerOf(layer)];

  const shift = rule?.shift ?? 0;
  let min = layer.minzoom === undefined ? undefined : layer.minzoom + shift;
  let max = layer.maxzoom === undefined ? undefined : layer.maxzoom + shift;

  if (rule?.min !== undefined) min = Math.max(min ?? rule.min, rule.min);
  if (rule?.max !== undefined) max = Math.min(max ?? rule.max, rule.max);

  return {
    ...(min === undefined ? {} : { minzoom: clamp(min) }),
    ...(max === undefined ? {} : { maxzoom: clamp(max) }),
  };
}
