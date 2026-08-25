import { useState } from "react";

import { MENU, THEMES, type MenuLayer, type Theme } from "../generated/layers";
import { useMapStore } from "../store";
import LayerSwatch from "./LayerSwatch";

const ALL: MenuLayer[] = (Object.keys(THEMES) as Theme[]).flatMap((theme) =>
  (MENU[theme] ?? []).flatMap((entry) => entry.layers),
);

const COLLAPSED_CHIPS = 4;

export default function ActiveLayers() {
  const visible = useMapStore((state) => state.visible);
  const setMany = useMapStore((state) => state.setMany);
  const [expanded, setExpanded] = useState(false);

  const chips = ALL.filter((layer) => layer.ids.every((id) => visible[id]));

  const hidden = expanded ? 0 : Math.max(0, chips.length - COLLAPSED_CHIPS);
  const shown = expanded ? chips : chips.slice(0, COLLAPSED_CHIPS);

  if (chips.length === 0) return null;

  return (
    <section className="-mx-6 border-y border-line bg-ground px-6 py-3">
      <div className="mb-2 flex items-center">
        <h2 className="sidebar-label !mb-0">Active layers</h2>
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
