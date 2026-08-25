import { useEffect, useRef, useState, type ReactNode } from "react";

import { DETENTS, type Detent } from "./detents";


interface BottomSheetProps {
  detent: Detent;
  onDetent: (detent: Detent) => void;
  title: string;
  badge?: number;
  children: ReactNode;
}

export default function BottomSheet({
  detent,
  onDetent,
  title,
  badge,
  children,
}: BottomSheetProps) {
  const [drag, setDrag] = useState<{ from: number; delta: number } | null>(null);
  const sheet = useRef<HTMLDivElement>(null);

  const height = DETENTS[detent];
  const live = drag
    ? Math.min(0.96, Math.max(0.06, height - drag.delta / window.innerHeight))
    : height;

  const nearest = (fraction: number): Detent => {
    let best: Detent = 0;
    for (let index = 0; index < DETENTS.length; index++) {
      if (
        Math.abs(DETENTS[index] - fraction) <
        Math.abs(DETENTS[best] - fraction)
      ) {
        best = index as Detent;
      }
    }
    return best;
  };

  useEffect(() => {
    if (!drag) return;

    const move = (event: PointerEvent) =>
      setDrag((current) =>
        current ? { ...current, delta: event.clientY - current.from } : null,
      );

    // Snapping inside a setDrag updater reaches the map's setState
    // during React's update phase; the closure is current anyway.
    const end = () => {
      onDetent(nearest(height - drag.delta / window.innerHeight));
      setDrag(null);
    };

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", end);
    window.addEventListener("pointercancel", end);

    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", end);
      window.removeEventListener("pointercancel", end);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drag, height]);

  return (
    <div
      ref={sheet}
      role="dialog"
      aria-label={title}
      style={{ height: `${live * 100}%` }}
      className={`pointer-events-auto absolute inset-x-0 bottom-0 z-20 flex
                  flex-col rounded-t-2xl border-t border-line bg-surface
                  shadow-[0_-8px_24px_-12px_rgb(0_0_0/0.25)]
                  ${drag ? "" : "transition-[height] duration-300 ease-out"}`}
    >
      <button
        type="button"
        onPointerDown={(event) =>
          setDrag({ from: event.clientY, delta: 0 })
        }
        onClick={() => onDetent(detent === 0 ? 1 : 0)}
        aria-expanded={detent > 0}
        className="shrink-0 cursor-grab touch-none select-none px-5 pb-2 pt-2.5
                   active:cursor-grabbing"
      >
        <span
          aria-hidden
          className="mx-auto mb-2.5 block h-1 w-9 rounded-full bg-neutral-300"
        />
        <span className="flex items-center gap-2">
          <span className="flex-1 text-left text-[0.9375rem] font-semibold
                           text-neutral-900">
            {title}
          </span>
          {badge !== undefined && badge > 0 && (
            <span
              className="inline-flex h-5 min-w-5 items-center justify-center
                         rounded-full bg-neutral-900 px-1.5 text-[0.6875rem]
                         font-semibold leading-none tabular-nums text-white"
            >
              {badge}
            </span>
          )}
        </span>
      </button>

      <div
        className={`min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 pb-6
                    ${detent === 0 ? "invisible" : ""}`}
      >
        {children}
      </div>
    </div>
  );
}
