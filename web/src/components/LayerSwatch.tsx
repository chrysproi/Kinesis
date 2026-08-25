import { Bike } from "lucide-react";

import type { Swatch } from "../generated/layers";
import { lucideFor } from "./lucide";

interface LayerSwatchProps {
  swatch: Swatch;
  /**
   * Smaller mark, for the active-layer chips. The default 18 px box was
   * set for a standalone row; inside a 24 px chip it was the largest
   * thing in it and the chips read as swatches with a label attached.
   */
  compact?: boolean;
}

export default function LayerSwatch({ swatch, compact }: LayerSwatchProps) {
  const color = swatch.color ?? "#737373";
  const box = compact ? "size-3.5" : "h-[18px] w-[18px]";
  const glyph = compact ? 11 : 14;

  if (swatch.kind === "point") {
    // Drawn rather than imported: see BUILT in map/icons.ts
    if (swatch.icon?.startsWith("stop-")) {
      return (
        <span aria-hidden className={`grid ${box} shrink-0 place-items-center`}>
          <svg width="14" height="14" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="4.5" fill={color} />
          </svg>
        </span>
      );
    }

    // Composed marks are drawn, not imported: see BUILT in map/icons.ts.
    // The menu shows the bicycle alone, which is enough at 14 px.
    if (swatch.icon?.startsWith("bike-")) {
      return (
        <span aria-hidden className={`grid ${box} shrink-0 place-items-center`}>
          <Bike size={glyph} strokeWidth={2} color={color} />
        </span>
      );
    }

    if (swatch.icon === "metro-m") {
      return (
        <span aria-hidden className={`grid ${box} shrink-0 place-items-center`}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
               stroke={color} strokeWidth="2" strokeLinecap="round"
               strokeLinejoin="round">
            <circle cx="12" cy="12" r="9.5" fill="#fff" />
            <path d="M7.5 16.5V8l4.5 5.5L16.5 8v8.5" />
          </svg>
        </span>
      );
    }

    const Icon = lucideFor(swatch.icon);

    if (Icon) {
      return (
        <span aria-hidden className={`grid ${box} shrink-0 place-items-center`}>
          <Icon size={glyph} strokeWidth={2} color={color} />
        </span>
      );
    }

    return (
      <span aria-hidden className={`grid ${box} shrink-0 place-items-center`}>
        <span
          className="size-2.5 rounded-full"
          style={{ background: color }}
        />
      </span>
    );
  }

  if (swatch.kind === "line") {
    return (
      <span aria-hidden className={`grid ${box} shrink-0 place-items-center`}>
        <svg width="18" height="18" viewBox="0 0 18 18">
          <line
            x1="1"
            y1="13"
            x2="17"
            y2="5"
            stroke={color}
            strokeWidth="2.25"
            strokeLinecap="round"
            strokeDasharray={swatch.dashed ? "3 2.5" : undefined}
          />
        </svg>
      </span>
    );
  }

  return (
    <span
      aria-hidden
      className={`${box} shrink-0 rounded-[3px] border`}
      style={{ background: color, borderColor: color }}
    />
  );
}
