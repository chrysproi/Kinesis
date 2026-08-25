import type { LegendBlock } from "../generated/layerRegistry";
import { builtSvg } from "../map/icons/sprites";
import { lucideFor } from "../ui/lucide";

/** The mark for one legend row: a drawn hub tier, an icon, a line, a swatch. */
export default function LegendMark({
  kind,
  entry,
}: {
  kind: LegendBlock["kind"];
  entry: NonNullable<LegendBlock["entries"]>[number];
}) {
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

    const drawnSvg = Icon ? null : builtSvg(entry.icon, entry.color ?? "#404040");

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
