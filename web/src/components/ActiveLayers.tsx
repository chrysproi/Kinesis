import { useState } from "react";

import { MENU, THEMES, type MenuLayer, type Theme } from "../generated/layers";
import { useMapStore } from "../store";
import LayerSwatch from "./LayerSwatch";

/** Every toggle, flattened, so chips can be looked up by id. */
const ALL: MenuLayer[] = (Object.keys(THEMES) as Theme[]).flatMap((theme) =>
  (MENU[theme] ?? []).flatMap((entry) => entry.layers),
);

/**
 * What is on, as removable chips.
 *
 * With fourteen toggles across four themes, the sidebar answers "can I
 * see X" but not "what am I looking at". This does — and each chip is
 * also the fastest way to switch something off.
 */
/** Roughly two rows at these label lengths. */
const COLLAPSED_CHIPS = 4;

export default function ActiveLayers() {
  const visible = useMapStore((state) => state.visible);
  const setMany = useMapStore((state) => state.setMany);
  const [expanded, setExpanded] = useState(false);

  const chips = ALL.filter((layer) => layer.ids.every((id) => visible[id]));

  // Capped by default: with everything on this panel ran to four rows and
  // pushed the layer list into scrolling.
  const hidden = expanded ? 0 : Math.max(0, chips.length - COLLAPSED_CHIPS);
  const shown = expanded ? chips : chips.slice(0, COLLAPSED_CHIPS);

  // Nothing on: no band. A ruled panel saying "Nothing shown" is a
  // heading, a badge and two rules spent on the absence of content, and
  // the layer list below already makes it obvious that everything is off.
  if (chips.length === 0) return null;

  return (
    // A full-width band on a darker ground, bled to the panel edges and
    // ruled top and bottom, so "what am I looking at" reads as its own
    // register rather than another list of controls.
    <section className="-mx-6 border-y border-line bg-ground px-6 py-3">
      <div className="mb-2 flex items-center">
        <h2 className="sidebar-label !mb-0">Active layers</h2>
        {/* Right-aligned: the count belongs to the whole band, not to the
            word next to it, and pinned to the edge it lines up with the
            switches below.

            `leading-none` is what centres the digit. Without it the
            inherited line-height sits taller than the 16 px circle and
            pushes the number down off centre — which is why it looked
            misaligned at 9 px. Back up to 10 px, since a count nobody
            can read is not worth the circle around it. */}
        <span
          className="ml-auto inline-flex h-4 min-w-4 items-center justify-center
                     rounded-full bg-neutral-900 px-[3px] text-[0.625rem]
                     font-semibold leading-none tabular-nums text-white"
        >
          {chips.length}
        </span>
      </div>

      <ul className="flex flex-wrap gap-1">
          {shown.map((layer) => (
            <li key={layer.id}>
              <button
                type="button"
                onClick={() => setMany(layer.ids, false)}
                title={`Hide ${layer.fullLabel}`}
                className="flex items-center gap-1 rounded border border-line
                           bg-white py-0.5 pl-1 pr-1.5 text-[0.6875rem]
                           leading-4 text-neutral-900 hover:border-neutral-300
                           hover:bg-ground"
              >
                <LayerSwatch swatch={layer.swatch} compact />
                <span className="max-w-[8.5rem] truncate">{layer.label}</span>
              </button>
            </li>
          ))}

          {(hidden > 0 || expanded) && (
            <li>
              <button
                type="button"
                onClick={() => setExpanded(!expanded)}
                className="rounded border border-dashed border-neutral-300 px-1.5
                           py-0.5 text-[0.6875rem] leading-4 tabular-nums
                           text-meta hover:bg-white"
              >
                {hidden > 0 ? `+${hidden}` : "Less"}
              </button>
            </li>
          )}
      </ul>
    </section>
  );
}
