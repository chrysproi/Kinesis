import { menuByTheme, themesInOrder } from "../layers/grouping";
import { THEMES, type MenuEntry, type MenuLayer } from "../generated/layerRegistry";
import { useMapStore } from "../layers/store";
import ActiveLayers from "./ActiveLayers";
import Toggle from "../ui/Toggle";

interface SidebarProps {
  onFlyToZoom: (zoom: number) => void;
}

export default function Sidebar({ onFlyToZoom }: SidebarProps) {
  const menu = menuByTheme();

  return (
    <nav
      aria-label="Map layers"
      className="flex w-[280px] shrink-0 flex-col overflow-hidden rounded-lg
                 border border-line bg-surface"
    >
      <header className="flex shrink-0 items-center gap-2.5 px-6 pb-3 pt-4">
        <span
          aria-hidden
          className="grid size-9 shrink-0 place-items-center rounded-lg
                     border border-brand"
        >
          <img
            src={`${import.meta.env.BASE_URL}logo.png`}
            alt=""
            width={26}
            height={22}
          />
        </span>

        <div className="min-w-0">
          <h1 className="text-[0.875rem] font-semibold tracking-[0.03em]
                         text-brand [word-spacing:0.12em]">
            Kinesis City Hub
          </h1>
          <p className="text-[0.75rem] leading-4 text-meta">Thessaloniki map</p>
        </div>
      </header>

      <div className="shrink-0 px-6 pb-3">
        <ActiveLayers />
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-6 pb-4 pt-1">
        {themesInOrder().map((theme) => {
          const entries = menu[theme];
          if (!entries?.length) return null;

          return (
            <section key={theme}>
              <h2 className="sidebar-label">{THEMES[theme]}</h2>

              <ul role="group" className="space-y-0.5">
                {entries.map((entry) => (
                  <Entry key={entry.label} entry={entry} onFlyToZoom={onFlyToZoom} />
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </nav>
  );
}

function Entry({ entry, onFlyToZoom }: { entry: MenuEntry } & SidebarProps) {
  return (
    <>
      {entry.layers.map((layer) => (
        <Row key={layer.id} layer={layer} onFlyToZoom={onFlyToZoom} />
      ))}
    </>
  );
}

function Row({ layer, onFlyToZoom }: { layer: MenuLayer } & SidebarProps) {
  const visible = useMapStore((state) => state.visible);
  const zoom = useMapStore((state) => state.zoom);
  const setMany = useMapStore((state) => state.setMany);

  const on = layer.ids.every((id) => visible[id]);

  const tooFarOut = layer.minZoom !== null && zoom < layer.minZoom;
  const dimmed = tooFarOut && on;

  return (
    <li className="flex h-[22px] items-center gap-2.5">
      <label
        htmlFor={`layer-${layer.id}`}
        title={layer.fullLabel}
        className={`min-w-0 flex-1 cursor-pointer truncate text-[0.8125rem] ${
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
                     tabular-nums text-meta hover:bg-line"
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
