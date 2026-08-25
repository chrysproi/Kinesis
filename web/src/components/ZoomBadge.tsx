import { useMapStore } from "../store";

/**
 * Current zoom, over the map rather than in the sidebar title.
 *
 * Bottom-left, stacked directly above the scale bar. Zoom and scale
 * answer the same question — how much ground is this — so one corner
 * should hold both; the top right is the legend's and the top left is
 * where the eye starts reading the map itself.
 *
 * `bottom-10` clears MapLibre's own scale control, which sits at a 10 px
 * margin and is about 20 px tall. Sharing the corner without stacking
 * put the two on top of each other.
 *
 * It also belongs on the map because it changes when the map changes.
 * Tucked into the sidebar heading it looked like part of the title and
 * nobody connected it to scrolling the wheel.
 */
export default function ZoomBadge() {
  const zoom = useMapStore((state) => state.zoom);

  return (
    <div
      title="Current zoom level"
      className="pointer-events-none absolute bottom-10 left-3 z-10 rounded-md
                 border border-line bg-white/90 px-2 py-1 text-[0.6875rem]
                 font-medium tabular-nums text-neutral-700 shadow-sm
                 backdrop-blur"
    >
      z{zoom.toFixed(1)}
    </div>
  );
}
