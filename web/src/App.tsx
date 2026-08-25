import { useCallback, useRef } from "react";

import MapView from "./map/MapView";
import MobileShell from "./mobile/MobileShell";
import { useIsMobile } from "./mobile/useIsMobile";
import Legend from "./sidebar/Legend";
import Sidebar from "./sidebar/Sidebar";
import ZoomBadge from "./sidebar/ZoomBadge";

export default function App() {
  const isMobile = useIsMobile();

  const flyToZoom = useRef<(zoom: number) => void>(() => {});
  const zoomBy = useRef<(delta: number) => void>(() => {});
  const setPadding = useRef<(bottom: number) => void>(() => {});

  const registerMap = useCallback(
    (controls: {
      flyToZoom: (zoom: number) => void;
      zoomBy: (delta: number) => void;
      setBottomPadding: (bottom: number) => void;
    }) => {
      flyToZoom.current = controls.flyToZoom;
      zoomBy.current = controls.zoomBy;
      setPadding.current = controls.setBottomPadding;
    },
    [],
  );

  const map = <MapView onReady={registerMap} chrome={!isMobile} />;

  if (isMobile) {
    return (
      <MobileShell
        onFlyToZoom={(zoom) => flyToZoom.current(zoom)}
        onZoomBy={(delta) => zoomBy.current(delta)}
        onSheetHeight={(fraction) => setPadding.current(fraction)}
      >
        {map}
      </MobileShell>
    );
  }

  return (
    <div className="flex h-full gap-2 bg-ground p-2">
      <Sidebar onFlyToZoom={(zoom) => flyToZoom.current(zoom)} />

      <main
        className="relative min-w-0 flex-1 overflow-hidden rounded-xl border
                   border-neutral-200 bg-white shadow-sm"
      >
        {map}
        <Legend />
        <ZoomBadge />
      </main>
    </div>
  );
}
