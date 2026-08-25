import { useState } from "react";
import { ChevronDown } from "lucide-react";

import {
  LEGEND,
  THEMES,
  TOGGLE_LAYERS,
  type LegendBlock,
  type Theme,
} from "../generated/layers";
import { builtSvg } from "../map/icons";
import { useMapStore } from "../store";
import { lucideFor } from "./lucide";

/**
 * Legend, as one card per theme — the sidebar's own grouping.
 *
 * A card per *block* was the previous shape, and with every amenity on
 * it made sixteen bordered boxes down the right edge: more height spent
 * on chrome than on rows, and nothing to say that Education and Health
 * are the same kind of thing. One card per theme mirrors the sidebar
 * exactly, so a layer switched on over there is keyed here under the
 * same heading.
 *
 * Cards still appear and disappear with their layers, so the stack only
 * ever explains what is on screen.
 *
 * Tree height is a gradient rather than a list: it is one hue varying by
 * luminance, which is a scale, and a scale reads as a bar.
 */
/** Lowest zoom at which each toggle draws anything. */
const MIN_ZOOM = new Map(TOGGLE_LAYERS.map((l) => [l.id, l.minZoom]));

/**
 * A layer counts as shown only when it is switched on *and* deep enough
 * to draw. Gating on the switch alone put six amenity cards on screen at
 * z12, explaining symbols that do not appear until 14 — a legend for an
 * empty map. The sidebar already greys those rows and shows their zoom;
 * the legend has to agree with it.
 */
const drawn = (
  visible: Record<string, boolean>,
  zoom: number,
  id: string,
) => {
  if (!visible[id]) return false;
  const min = MIN_ZOOM.get(id);
  return min == null || zoom >= min;
};

export default function Legend() {
  const visible = useMapStore((state) => state.visible);
  const zoom = useMapStore((state) => state.zoom);

  // Which themes the reader has folded away. Held as the exception, not
  // as the state of every card: a theme that is not in the set is open,
  // so a card appearing for a newly switched-on layer arrives readable.
  const [collapsed, setCollapsed] = useState<Set<Theme>>(new Set());

  const toggle = (theme: Theme) =>
    setCollapsed((current) => {
      const next = new Set(current);
      if (!next.delete(theme)) next.add(theme);
      return next;
    });

  const blocks = Object.entries(LEGEND)
    .map(([key, block]) => [key, prune(block, visible, zoom)] as const)
    .filter((pair): pair is [string, LegendBlock] => pair[1] !== null);

  if (blocks.length === 0) return null;

  return (
    <div
      aria-label="Legend"
      role="complementary"
      // Scrolls rather than running off the bottom, and stays
      // click-through so the map underneath still takes clicks; each
      // card re-enables pointer events, which is enough for a wheel over
      // a card to bubble here and scroll. Making the container itself
      // interactive would block map clicks down the whole right column.
      className="pointer-events-none absolute right-3 top-3 flex
                 max-h-[calc(100%-1.5rem)] w-[10.5rem] flex-col gap-2
                 overflow-y-auto overscroll-contain [scrollbar-width:none]
                 [&::-webkit-scrollbar]:hidden"
    >
      {(Object.keys(THEMES) as Theme[]).map((theme) => {
        const inTheme = blocks.filter(([, block]) => block.theme === theme);
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
            {/* The heading is the control. A separate chevron button
                would be a 12 px target beside a word that looks just as
                clickable, so the whole row takes the click and the
                chevron only reports the state. */}
            <button
              type="button"
              onClick={() => toggle(theme)}
              aria-expanded={open}
              // The heading's spacing belongs to the open state: kept on
              // the label itself it left a collapsed card padded at the
              // bottom for rows that are not there.
              className={`flex w-full items-center gap-1 text-left ${
                open ? "mb-1.5" : ""
              }`}
            >
              <span className="legend-theme min-w-0 flex-1 truncate">
                {THEMES[theme]}
              </span>

              {/* The row count stands in for the rows while they are
                  folded away, so a collapsed card still says how much is
                  under it rather than reading as an empty heading. */}
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

            {/* Blocks inside a theme are separated by space alone. A rule
                between them would have re-drawn the card boundary this
                grouping exists to remove. */}
            {open && (
              <div className="space-y-2">
                {inTheme.map(([key, block]) => (
                  <Block key={key} block={block} />
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
  block: LegendBlock,
  visible: Record<string, boolean>,
  zoom: number,
): LegendBlock | null {
  if (block.layer && !drawn(visible, zoom, block.layer)) return null;

  // A block shared by layers on one scale survives while any of them is
  // on: the municipal choropleth and the 100 m grid use identical
  // classes, so two cards would have repeated each other row for row.
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

function Block({ block }: { block: LegendBlock }) {
  return (
    <div>
      <h3 className="legend-title">{block.title}</h3>

      {/* The unit belongs once above the rows, not repeated on five of
          them — the labels are already ranges and long enough. */}
      {block.unit && (
        <p className="mb-1 text-[0.625rem] leading-3 text-meta">{block.unit}</p>
      )}

      {block.kind === "gradient" ? (
        <Gradient block={block} />
      ) : (
        <ul className="space-y-px">
          {block.entries?.map((entry) => (
            <li key={entry.label} className="flex items-center gap-1.5">
              <Mark kind={block.kind} entry={entry} />
              <span className="truncate text-[0.6875rem] leading-4 text-neutral-800">
                {entry.label}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Gradient({ block }: { block: LegendBlock }) {
  return (
    <div>
      <div
        className="h-2 w-full rounded-sm"
        style={{
          background: `linear-gradient(to right, ${block.stops?.join(", ")})`,
        }}
      />
      <div className="mt-0.5 flex justify-between text-[0.625rem] tabular-nums text-meta">
        <span>{block.min}</span>
        <span>{block.max}</span>
      </div>
    </div>
  );
}

function Mark({
  kind,
  entry,
}: {
  kind: LegendBlock["kind"];
  entry: NonNullable<LegendBlock["entries"]>[number];
}) {
  // The hub tiers differ by structure, not only by colour, so the legend
  // draws the marks the map draws — a plated glyph, a ring, a dot and the
  // Kinesis logo — rather than four chips of the same blue.
  if (kind === "marks") {
    const colour = entry.color ?? "#737373";

    if (entry.mark === "logo") {
      return (
        <img
          aria-hidden
          src={`${import.meta.env.BASE_URL}mobility-hub.png`}
          alt=""
          className="size-3.5 shrink-0 object-contain"
        />
      );
    }

    // Three stacked circles for the double ring, one for the single, one
    // for the dot — the same construction the map layers use, at the
    // same proportions.
    const outer = entry.mark === "double-ring" ? 5 : entry.mark === "ring" ? 4.2 : 3.2;

    return (
      <span aria-hidden className="grid size-3.5 shrink-0 place-items-center">
        <svg width="12" height="12" viewBox="0 0 12 12">
          <circle cx="6" cy="6" r={outer} fill={colour} stroke="#fff" strokeWidth="1" />
          {entry.mark === "double-ring" && (
            <>
              <circle cx="6" cy="6" r={outer * 0.66} fill="#fff" />
              <circle cx="6" cy="6" r={outer * 0.34} fill={entry.core ?? colour} />
            </>
          )}
          {entry.mark === "ring" && (
            <circle cx="6" cy="6" r={outer * 0.42} fill="#fff" />
          )}
        </svg>
      </span>
    );
  }

  if (kind === "icons") {
    const Icon = lucideFor(entry.icon);

    // Bus stop marks and the metro M are drawn rather than taken from
    // lucide, so they miss the React set and come from the same source
    // the map rasterises. Checked before the fallback dot, or five stop
    // categories would key as five identical dots.
    const drawnSvg = Icon ? null : builtSvg(entry.icon, entry.color ?? "#404040");

    // Falls back to a dot rather than a gap: a row with a label and no
    // mark reads as a missing icon, which is worse than a generic one.
    return (
      <span aria-hidden className="grid size-3.5 shrink-0 place-items-center">
        {Icon ? (
          <Icon size={13} strokeWidth={2} color={entry.color} />
        ) : drawnSvg ? (
          <span
            className="grid size-3.5 place-items-center [&>svg]:size-3.5"
            dangerouslySetInnerHTML={{ __html: drawnSvg }}
          />
        ) : (
          <span className="size-2 rounded-full"
                style={{ background: entry.color }} />
        )}
      </span>
    );
  }

  if (kind === "lines") {
    return (
      <svg width="14" height="10" viewBox="0 0 14 10" className="shrink-0">
        <line
          x1="0.5"
          y1="5"
          x2="13.5"
          y2="5"
          stroke={entry.color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={entry.dashed ? "3 2.5" : undefined}
        />
      </svg>
    );
  }


  return (
    <span
      className="h-2.5 w-3.5 shrink-0 rounded-sm border border-black/10"
      style={{ background: entry.color }}
    />
  );
}
