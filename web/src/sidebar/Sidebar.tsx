import ActiveLayers from "./ActiveLayers";
import LayerList from "./LayerList";

interface SidebarProps {
  onFlyToZoom: (zoom: number) => void;
}

export default function Sidebar({ onFlyToZoom }: SidebarProps) {
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
        <LayerList onFlyToZoom={onFlyToZoom} />
      </div>
    </nav>
  );
}
