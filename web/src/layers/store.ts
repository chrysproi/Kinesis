import { create } from "zustand";

import { AUTO_HIDE } from "../generated/layerRegistry";
import {
  autoHiding,
  defaultVisibility,
  occupiedBy,
  visibilityFor,
  withExclusions,
  type Visible,
} from "./visibility";

interface MapState {
  visible: Visible;
  zoom: number;
  /** Auto-hiding layers closed by zoom, so zooming out can restore them. */
  autoClosed: string[];
  /** Auto-hiding layers switched by hand, which zoom leaves alone. */
  claimed: string[];

  toggle: (id: string) => void;
  setVisible: (visible: Visible) => void;
  setMany: (ids: string[], on: boolean) => void;
  setZoom: (zoom: number) => void;
  showOnly: (ids: string[], zoom?: number) => void;
}

/** Hand-switching an auto-hiding layer takes it out of the zoom rule. */
const claim = (claimed: string[], ids: string[]) => {
  const mine = ids.filter((id) => id in AUTO_HIDE && !claimed.includes(id));
  return mine.length ? [...claimed, ...mine] : claimed;
};

export const useMapStore = create<MapState>((set) => ({
  visible: defaultVisibility(),
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

      for (const [id, threshold] of autoHiding()) {
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
      visible: visibilityFor(ids),
      claimed: claim(
        state.claimed,
        ids.filter((id) => id in AUTO_HIDE && (zoom ?? 0) > AUTO_HIDE[id]),
      ),
      autoClosed: [],
    })),
}));

export { activeIds } from "./visibility";
