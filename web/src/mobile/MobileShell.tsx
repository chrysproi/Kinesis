import { useState } from "react";
import { Layers, Minus, Plus, X } from "lucide-react";

import { menuByTheme, themesInOrder } from "../layers/grouping";
import { useMapStore } from "../layers/store";
import Legend from "../sidebar/Legend";
import LayerList from "../sidebar/LayerList";
import BottomSheet from "./BottomSheet";
import { DETENTS, type Detent } from "./detents";

interface MobileShellProps {
  onFlyToZoom: (zoom: number) => void;
  onZoomBy: (delta: number) => void;
  /** Keeps the map's centre in the part the sheet does not cover. */
  onSheetHeight: (fraction: number) => void;
  children: React.ReactNode;
}

export default function MobileShell({
  onFlyToZoom,
  onZoomBy,
  onSheetHeight,
  children,
}: MobileShellProps) {
  const [detent, setDetent] = useState<Detent>(0);
  const [showLegend, setShowLegend] = useState(false);
  const [collapsed, setCollapsed] = useState<Set<string>>(
    () => new Set(themesInOrder()),
  );

  const visible = useMapStore((state) => state.visible);
  const zoom = useMapStore((state) => state.zoom);

  const menu = menuByTheme();
  const count = themesInOrder()
    .flatMap((theme) => menu[theme] ?? [])
    .flatMap((entry) => entry.layers)
    .filter((layer) => layer.ids.every((id) => visible[id])).length;

  const move = (next: Detent) => {
    setDetent(next);
    onSheetHeight(DETENTS[next]);
  };

  const toggleTheme = (theme: string) =>
    setCollapsed((current) => {
      const next = new Set(current);
      if (!next.delete(theme)) next.add(theme);
      return next;
    });

  return (
    <div className="flex h-full flex-col bg-ground">
      <header className="flex shrink-0 items-center gap-2 px-4 py-2.5">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center rounded-md
                     border border-brand"
        >
          <img
            src={`${import.meta.env.BASE_URL}logo.png`}
            alt=""
            width={20}
            height={17}
          />
        </span>
        <h1 className="text-[0.8125rem] font-semibold tracking-[0.06em]
                       text-brand [word-spacing:0.1em]">
          KINESIS CITY HUB
        </h1>
      </header>

      <main className="relative min-h-0 flex-1 overflow-hidden">
        {children}

        <div className="pointer-events-none absolute right-3 top-3 z-10 flex
                        flex-col gap-2">
          <ControlButton
            label={showLegend ? "Hide the key" : "Show the key"}
            onClick={() => setShowLegend(!showLegend)}
            active={showLegend}
          >
            {showLegend ? <X size={16} /> : <Layers size={16} />}
          </ControlButton>

          <div className="pointer-events-auto overflow-hidden rounded-lg border
                          border-line bg-white/95 shadow-sm backdrop-blur">
            <button
              type="button"
              aria-label="Zoom in"
              onClick={() => onZoomBy(1)}
              className="grid size-9 place-items-center border-b border-line
                         active:bg-ground"
            >
              <Plus size={16} />
            </button>
            <button
              type="button"
              aria-label="Zoom out"
              onClick={() => onZoomBy(-1)}
              className="grid size-9 place-items-center active:bg-ground"
            >
              <Minus size={16} />
            </button>
          </div>
        </div>

        {showLegend && <Legend position="right-[3.5rem] top-3" />}

        <span
          className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-md
                     border border-line bg-white/90 px-2 py-1 text-[0.6875rem]
                     font-medium tabular-nums text-neutral-700 shadow-sm"
        >
          z{zoom.toFixed(1)}
        </span>

        <BottomSheet
          detent={detent}
          onDetent={move}
          title="Layers"
          badge={count}
        >
          <LayerList
            onFlyToZoom={onFlyToZoom}
            collapsible
            collapsed={collapsed}
            onToggleTheme={toggleTheme}
          />
        </BottomSheet>
      </main>
    </div>
  );
}

function ControlButton({
  label,
  onClick,
  active,
  children,
}: {
  label: string;
  onClick: () => void;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className={`pointer-events-auto grid size-9 place-items-center rounded-lg
                  border border-line shadow-sm backdrop-blur active:bg-ground
                  ${active ? "bg-brand text-white" : "bg-white/95"}`}
    >
      {children}
    </button>
  );
}
