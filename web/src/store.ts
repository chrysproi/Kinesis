import { create } from "zustand";

import {
  AUTO_HIDE,
  EXCLUSIVE_GROUPS,
  PINNED_LAYERS,
  TOGGLE_LAYERS,
} from "./generated/layers";

interface MapState {
  /** Which sidebar toggles are on, keyed by layer id. */
  visible: Record<string, boolean>;
  zoom: number;
  /**
   * Auto-hiding layers this session has closed by zoom rather than by
   * choice. Held so zooming back out can restore exactly those, and
   * emptied for a layer the moment the reader works its switch.
   */
  autoClosed: string[];
  /** Auto-hiding layers the reader has taken over, which zoom leaves alone. */
  claimed: string[];

  toggle: (id: string) => void;
  setVisible: (visible: Record<string, boolean>) => void;
  /** One switch over several layers: a mode's network and its nodes. */
  setMany: (ids: string[], on: boolean) => void;
  setZoom: (zoom: number) => void;
  /** `zoom` is the view the link asks for, which decides what it claims. */
  showOnly: (ids: string[], zoom?: number) => void;
}

const defaults = Object.fromEntries(
  TOGGLE_LAYERS.map((layer) => [layer.id, layer.show]),
);

/**
 * Switching a layer on switches off anything it cannot share the map
 * with. The six indicator choropleths and the 100 m grid all fill the
 * same 14 polygons, so two of them on means reading neither — the top
 * one silently wins while the sidebar claims both are visible.
 *
 * Only applied when turning something ON: switching a layer off should
 * never reach across and change another.
 */
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

/**
 * An auto-hiding layer the reader has switched by hand is theirs from
 * then on: the zoom rule stops applying to it for the session.
 *
 * Without this the frame would close itself again the next time the map
 * moved, one zoom step after being deliberately switched back on — a
 * switch that appears not to work.
 */
const claim = (claimed: string[], ids: string[]) => {
  const mine = ids.filter((id) => id in AUTO_HIDE && !claimed.includes(id));
  return mine.length ? [...claimed, ...mine] : claimed;
};

/** Whether something else in this layer's exclusive group is already on. */
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

  /**
   * Zoom also opens and closes the overview layers.
   *
   * Symmetrical on purpose: a frame that closed on the way in and stayed
   * closed on the way back out would leave the reader at the opening
   * view with the opening layer missing and no hint that zoom was what
   * took it. Only layers *this rule* closed are restored — one the
   * reader switched off stays off.
   */
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
          // Not back over something that took its place. Zones shares an
          // exclusive group with the choropleths, so a reader who
          // switched one on at depth and zoomed back out would otherwise
          // find the frame reopened on top of it.
          !occupiedBy(visible, id)
        ) {
          visible = { ...visible, [id]: true };
          autoClosed = autoClosed.filter((closed) => closed !== id);
        }
      }

      return { zoom, visible, autoClosed };
    }),

  // A pinned layer stays on whatever the URL says. It has no switch, so
  // letting a shared link turn it off would leave no way to get it back.
  showOnly: (ids, zoom) =>
    set((state) => ({
      visible: Object.fromEntries(
        TOGGLE_LAYERS.map((layer) => [
          layer.id,
          PINNED_LAYERS.includes(layer.id) || ids.includes(layer.id),
        ]),
      ),
      // A link claims an auto-hiding layer only where naming it means
      // something: past the threshold, where the layer would not be on
      // by itself. At or below it, every link naming the frame is just
      // the default state written down — which is what the absolute
      // form this map used to emit wrote on every share — and treating
      // that as an override left the frame pinned open for the whole
      // session.
      claimed: claim(
        state.claimed,
        ids.filter((id) => id in AUTO_HIDE && (zoom ?? 0) > AUTO_HIDE[id]),
      ),
      autoClosed: [],
    })),
}));

/** The ids of every layer currently switched on. */
export const activeIds = (visible: Record<string, boolean>) =>
  Object.entries(visible)
    .filter(([, on]) => on)
    .map(([id]) => id);
