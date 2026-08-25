import {
  AUTO_HIDE,
  EXCLUSIVE_GROUPS,
  PINNED_LAYERS,
  TOGGLE_LAYERS,
} from "../generated/layerRegistry";
import { CONFIG } from "../config/layerConfig";

export type Visible = Record<string, boolean>;

/** What is on when the map opens. */
export const defaultVisibility = (): Visible =>
  Object.fromEntries(
    TOGGLE_LAYERS.map((layer) => [
      layer.id,
      CONFIG.startsOn[layer.id] ?? layer.show,
    ]),
  );

/** The ids of every layer currently switched on. */
export const activeIds = (visible: Visible) =>
  Object.entries(visible)
    .filter(([, on]) => on)
    .map(([id]) => id);

/** Switching a layer on switches off anything it cannot share the map with. */
export function withExclusions(visible: Visible, id: string): Visible {
  const group = EXCLUSIVE_GROUPS.find((ids) => ids.includes(id));
  if (!group) return visible;

  const cleared = { ...visible };
  for (const other of group) if (other !== id) cleared[other] = false;
  return cleared;
}

/** Whether something else in this layer's exclusive group is already on. */
export function occupiedBy(visible: Visible, id: string) {
  const group = EXCLUSIVE_GROUPS.find((ids) => ids.includes(id));
  return group ? group.some((other) => other !== id && visible[other]) : false;
}

/** A layer forced on by being pinned, or asked for by a link. */
export const visibilityFor = (ids: string[]): Visible =>
  Object.fromEntries(
    TOGGLE_LAYERS.map((layer) => [
      layer.id,
      PINNED_LAYERS.includes(layer.id) || ids.includes(layer.id),
    ]),
  );

/** A layer is drawn when it is switched on and deep enough to render. */
export function drawn(visible: Visible, zoom: number, id: string) {
  const layer = TOGGLE_LAYERS.find((entry) => entry.id === id);
  if (!visible[id]) return false;

  return layer?.minZoom == null || zoom >= layer.minZoom;
}

/** Layers that switch themselves off past a zoom, and back on below it. */
export const autoHiding = () =>
  Object.entries(AUTO_HIDE) as [string, number][];
