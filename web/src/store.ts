import { create } from "zustand";

import {
  AUTO_HIDE,
  EXCLUSIVE_GROUPS,
  PINNED_LAYERS,
  TOGGLE_LAYERS,
} from "./generated/layers";

interface MapState {
  visible: Record<string, boolean>;
  zoom: number;
  /** Auto-hiding layers closed by zoom, so zooming out can restore them. */
  autoClosed: string[];
  /** Auto-hiding layers switched by hand, which zoom leaves alone. */
  claimed: string[];

  toggle: (id: string) => void;
  setVisible: (visible: Record<string, boolean>) => void;
  setMany: (ids: string[], on: boolean) => void;
  setZoom: (zoom: number) => void;
  showOnly: (ids: string[], zoom?: number) => void;
}

const defaults = Object.fromEntries(
  TOGGLE_LAYERS.map((layer) => [layer.id, layer.show]),
);

/** Switching a layer on switches off anything it cannot share the map with. */
const withExclusions = (
  visible: Record<string, boolean>,
  id: string,
): Record<string, boolean> => {
  const group = EXCLUSIVE_GROUPS.find((ids) => ids.includes(id));
  if (!group) return visible;

  const cleared = { ...visible };
  for (const other of group) if (other !== id) cleared[other] = false;
  return cleared;
};

/** Hand-switching an auto-hiding layer takes it out of the zoom rule. */
const claim = (claimed: string[], ids: string[]) => {
  const mine = ids.filter((id) => id in AUTO_HIDE && !claimed.includes(id));
  return mine.length ? [...claimed, ...mine] : claimed;
};

const occupiedBy = (visible: Record<string, boolean>, id: string) => {
  const group = EXCLUSIVE_GROUPS.find((ids) => ids.includes(id));
  return group ? group.some((other) => other !== id && visible[other]) : false;
};

export const useMapStore = create<MapState>((set) => ({
  visible: defaults,
  zoom: 10,
  autoClosed: [],
  claimed: [],

  toggle: (id) =>
    set((state) => {
      const on = !state.visible[id];
      const base = on ? withExclusions(state.visible, id) : state.visible;
      return {
        visible: { ...base, [id]: on },
        claimed: claim(state.claimed, [id]),
        autoClosed: state.autoClosed.filter((closed) => closed !== id),
      };
    }),

  setVisible: (visible) => set({ visible }),

  setMany: (ids, on) =>
    set((state) => ({
      visible: {
        ...(on ? ids.reduce(withExclusions, state.visible) : state.visible),
        ...Object.fromEntries(ids.map((id) => [id, on])),
      },
      claimed: claim(state.claimed, ids),
      autoClosed: state.autoClosed.filter((closed) => !ids.includes(closed)),
    })),

  setZoom: (zoom) =>
    set((state) => {
      let visible = state.visible;
      let autoClosed = state.autoClosed;

      for (const [id, threshold] of Object.entries(AUTO_HIDE)) {
        if (state.claimed.includes(id)) continue;

        const past = zoom > threshold;

        if (past && visible[id]) {
          visible = { ...visible, [id]: false };
          autoClosed = [...autoClosed, id];
        } else if (
          !past &&
          autoClosed.includes(id) &&
          !visible[id] &&
          !occupiedBy(visible, id)
        ) {
          visible = { ...visible, [id]: true };
          autoClosed = autoClosed.filter((closed) => closed !== id);
        }
      }

      return { zoom, visible, autoClosed };
    }),

  showOnly: (ids, zoom) =>
    set((state) => ({
      visible: Object.fromEntries(
        TOGGLE_LAYERS.map((layer) => [
          layer.id,
          PINNED_LAYERS.includes(layer.id) || ids.includes(layer.id),
        ]),
      ),
      claimed: claim(
        state.claimed,
        ids.filter((id) => id in AUTO_HIDE && (zoom ?? 0) > AUTO_HIDE[id]),
      ),
      autoClosed: [],
    })),
}));

export const activeIds = (visible: Record<string, boolean>) =>
  Object.entries(visible)
    .filter(([, on]) => on)
    .map(([id]) => id);
