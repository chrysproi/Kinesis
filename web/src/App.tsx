import { useCallback, useRef } from "react";

import Legend from "./components/Legend";
import Sidebar from "./components/Sidebar";
import ZoomBadge from "./components/ZoomBadge";
import MapView from "./map/MapView";

/**
 * Two panels on a soft ground: controls and the map.
 *
 * No app header — the title belongs to the sidebar, and every row of
 * chrome above the map is height the map does not get. The map keeps its
 * own border and radius so it reads as a figure, not a viewport.
 */
export default function App() {
  // Lets the sidebar's "z15" buttons drive the map without prop-drilling
  // a map instance through every component.
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
