import { useCallback, useRef } from "react";

import Legend from "./sidebar/Legend";
import Sidebar from "./sidebar/Sidebar";
import ZoomBadge from "./sidebar/ZoomBadge";
import MapView from "./map/MapView";

export default function App() {
  const flyToZoom = useRef<(zoom: number) => void>(() => {});

  const registerFlyTo = useCallback((fly: (zoom: number) => void) => {
    flyToZoom.current = fly;
  }, []);

  return (
    <div className="flex h-full gap-2 bg-ground p-2">
      <Sidebar onFlyToZoom={(zoom) => flyToZoom.current(zoom)} />

      <main
        className="relative min-w-0 flex-1 overflow-hidden rounded-xl border
                   border-neutral-200 bg-white shadow-sm"
      >
        <MapView onReady={registerFlyTo} />
        <Legend />
        <ZoomBadge />
      </main>
    </div>
  );
}
