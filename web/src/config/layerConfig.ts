import type { Theme } from "../generated/layerRegistry";

/**
 * Frontend presentation overrides — the human-owned half of the layer
 * model. `generated/layerRegistry.ts` is the other half, written by
 * Python; nothing here is generated, and nothing there is hand-edited.
 *
 * Everything is optional and starts empty. Leave a layer out and it
 * keeps the value it was generated with; name it and yours wins.
 *
 * Keys are the ids you see in the sidebar and the URL — `trees`,
 * `bus_stops`, `parking` — never the internal per-zoom layer ids, so
 * one line covers every tier a layer draws.
 *
 * Edit, save, and Vite reloads. Nothing here needs Python.
 */
export const CONFIG = {
  /**
   * Opacity multiplier, applied to every opacity a layer paints — fill,
   * line, circle, halo, heatmap. 1 is unchanged, 0.5 is half, 0 hides.
   *
   *   trees: 0.5,        the canopy wash, at half strength
   *   bus_stops: 0.8,
   */
  opacity: {} as Record<string, number>,

  /**
   * When a layer draws.
   *
   * `shift` moves every tier by the same amount, keeping the staircase
   * intact — bus stops go dot → sized circle → symbol whatever you set.
   * `min` and `max` clamp afterwards, as hard bounds.
   *
   *   trees: { shift: -2 },          two zooms earlier, all tiers
   *   bus_stops: { min: 11 },        never before 11
   *   buildings: { min: 13, max: 18 },
   */
  zoom: {} as Record<string, { shift?: number; min?: number; max?: number }>,

  /**
   * Which sidebar and legend group a layer belongs to. Any theme key:
   * zones, environment, fabric, transport, services, amenities,
   * population.
   *
   *   parking: "transport",
   *   trees: "fabric",
   */
  theme: {} as Record<string, Theme>,

  /**
   * Order of the groups. List the ones you care about; anything left
   * out keeps its generated position, after the ones listed.
   *
   *   themeOrder: ["transport", "services"],
   */
  themeOrder: [] as Theme[],

  /**
   * What is on when the map opens, overriding the generated default. A
   * URL with a layer segment still wins over this.
   *
   *   trees: true,
   *   ferry_routes: false,
   */
  startsOn: {} as Record<string, boolean>,
};
