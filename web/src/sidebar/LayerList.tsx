import { ChevronDown } from "lucide-react";

import {
  THEMES,
  type MenuEntry,
  type MenuLayer,
} from "../generated/layerRegistry";
import { menuByTheme, themesInOrder } from "../layers/grouping";
import { useMapStore } from "../layers/store";
import Toggle from "../ui/Toggle";

interface LayerListProps {
  onFlyToZoom: (zoom: number) => void;
  collapsible?: boolean;
  collapsed?: Set<string>;
  onToggleTheme?: (theme: string) => void;
}

export default function LayerList({
  onFlyToZoom,
  collapsible = false,
  collapsed,
  onToggleTheme,
}: LayerListProps) {
  const menu = menuByTheme();

  return (
    <>
      {themesInOrder().map((theme) => {
        const entries = menu[theme];
        if (!entries?.length) return null;

        const open = !collapsible || !collapsed?.has(theme);
        const count = entries.reduce((n, entry) => n + entry.layers.length, 0);

        return (
          <section key={theme}>
            {collapsible ? (
              <button
                type="button"
                onClick={() => onToggleTheme?.(theme)}
                aria-expanded={open}
                className="flex w-full items-center gap-2 py-2 text-left"
              >
                <span className="sidebar-label !mb-0 flex-1">
                  {THEMES[theme]}
                </span>
                <span className="text-[0.6875rem] tabular-nums text-meta">
                  {count}
                </span>
                <ChevronDown
                  aria-hidden
                  size={14}
                  className={`shrink-0 text-meta transition-transform ${
                    open ? "" : "-rotate-90"
                  }`}
                />
              </button>
            ) : (
              <h2 className="sidebar-label">{THEMES[theme]}</h2>
            )}

            {open && (
              <ul role="group" className="space-y-0.5">
                {entries.map((entry) => (
                  <Entry
                    key={entry.label}
                    entry={entry}
                    onFlyToZoom={onFlyToZoom}
                  />
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </>
  );
}

function Entry({
  entry,
  onFlyToZoom,
}: {
  entry: MenuEntry;
  onFlyToZoom: (zoom: number) => void;
}) {
  return (
    <>
      {entry.layers.map((layer) => (
        <Row key={layer.id} layer={layer} onFlyToZoom={onFlyToZoom} />
      ))}
    </>
  );
}

function Row({
  layer,
  onFlyToZoom,
}: {
  layer: MenuLayer;
  onFlyToZoom: (zoom: number) => void;
}) {
  const visible = useMapStore((state) => state.visible);
  const zoom = useMapStore((state) => state.zoom);
  const setMany = useMapStore((state) => state.setMany);

  const on = layer.ids.every((id) => visible[id]);

  const tooFarOut = layer.minZoom !== null && zoom < layer.minZoom;
  const dimmed = tooFarOut && on;

  return (
    <li className="flex h-[22px] items-center gap-2.5 [@media(pointer:coarse)]:h-11">
      <label
        htmlFor={`layer-${layer.id}`}
        title={layer.fullLabel}
        className={`min-w-0 flex-1 cursor-pointer truncate text-[0.8125rem]
                    [@media(pointer:coarse)]:text-[0.9375rem] ${
                      dimmed ? "text-neutral-400" : "text-neutral-900"
                    }`}
      >
        {layer.label}
      </label>

      {tooFarOut && (
        <button
          type="button"
          onClick={() => onFlyToZoom(layer.minZoom!)}
          title={`Visible from zoom ${layer.minZoom} — click to zoom in`}
          className="shrink-0 rounded bg-ground px-1.5 text-[0.625rem] font-medium
                     tabular-nums text-meta hover:bg-line
                     [@media(pointer:coarse)]:px-2 [@media(pointer:coarse)]:py-1"
        >
          z{layer.minZoom}
        </button>
      )}

      <Toggle
        id={`layer-${layer.id}`}
        checked={on}
        onChange={() => setMany(layer.ids, !on)}
        label={layer.fullLabel}
      />
    </li>
  );
}
