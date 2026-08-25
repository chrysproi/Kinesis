import { useMapStore } from "../layers/store";

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
