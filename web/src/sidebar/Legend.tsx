import { useState } from "react";
import { ChevronDown } from "lucide-react";

import {
  LEGEND,
  THEMES,
  type LegendBlock as Block,
  type Theme,
} from "../generated/layerRegistry";
import { drawn } from "../layers/visibility";
import { themeOfBlock, themesInOrder } from "../layers/grouping";
import { useMapStore } from "../layers/store";
import LegendBlock from "./LegendBlock";

export default function Legend() {
  const visible = useMapStore((state) => state.visible);
  const zoom = useMapStore((state) => state.zoom);

  const [collapsed, setCollapsed] = useState<Set<Theme>>(new Set());

  const toggle = (theme: Theme) =>
    setCollapsed((current) => {
      const next = new Set(current);
      if (!next.delete(theme)) next.add(theme);
      return next;
    });

  const blocks = Object.entries(LEGEND)
    .map(([key, block]) => [key, prune(block, visible, zoom)] as const)
    .filter((pair): pair is [string, Block] => pair[1] !== null);

  if (blocks.length === 0) return null;

  return (
    <div
      aria-label="Legend"
      role="complementary"
      className="pointer-events-none absolute right-3 top-3 flex
                 max-h-[calc(100%-1.5rem)] w-[10.5rem] flex-col gap-2
                 overflow-y-auto overscroll-contain [scrollbar-width:none]
                 [&::-webkit-scrollbar]:hidden"
    >
      {themesInOrder().map((theme) => {
        const inTheme = blocks.filter(([, block]) => themeOfBlock(block) === theme);
        if (inTheme.length === 0) return null;

        const open = !collapsed.has(theme);
        const rows = inTheme.reduce(
          (total, [, block]) => total + (block.entries?.length ?? 1),
          0,
        );

        return (
          <section
            key={theme}
            className="pointer-events-auto shrink-0 rounded-lg border
                       border-line bg-white/95 px-3 py-2.5 shadow-sm
                       backdrop-blur"
          >
            <button
              type="button"
              onClick={() => toggle(theme)}
              aria-expanded={open}
              className={`flex w-full items-center gap-1 text-left ${
                open ? "mb-1.5" : ""
              }`}
            >
              <span className="legend-theme min-w-0 flex-1 truncate">
                {THEMES[theme]}
              </span>

              {!open && (
                <span className="text-[0.625rem] tabular-nums text-meta">
                  {rows}
                </span>
              )}

              <ChevronDown
                aria-hidden
                size={12}
                className={`shrink-0 text-meta transition-transform
                            ${open ? "" : "-rotate-90"}`}
              />
            </button>

            {open && (
              <div className="space-y-2">
                {inTheme.map(([key, block]) => (
                  <LegendBlock key={key} block={block} />
                ))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}

/** Drops blocks and rows whose layer is switched off. */
function prune(
  block: Block,
  visible: Record<string, boolean>,
  zoom: number,
): Block | null {
  if (block.layer && !drawn(visible, zoom, block.layer)) return null;

  if (block.anyOf && !block.anyOf.some((id) => drawn(visible, zoom, id))) {
    return null;
  }

  if (block.entries?.some((entry) => entry.layer)) {
    const entries = block.entries.filter((entry) =>
      drawn(visible, zoom, entry.layer!),
    );
    return entries.length ? { ...block, entries } : null;
  }

  return block;
}
