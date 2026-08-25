import type { LegendBlock as Block } from "../generated/layerRegistry";
import LegendMark from "./LegendMark";

/** One keyed block: a title, an optional unit, then rows or a gradient. */
export default function LegendBlock({ block }: { block: Block }) {
  return (
    <div>
      <h3 className="legend-title">{block.title}</h3>

      {block.unit && (
        <p className="mb-1 text-[0.625rem] leading-3 text-meta">{block.unit}</p>
      )}

      {block.kind === "gradient" ? (
        <Gradient block={block} />
      ) : (
        <ul className="space-y-px">
          {block.entries?.map((entry) => (
            <li key={entry.label} className="flex items-center gap-1.5">
              <LegendMark kind={block.kind} entry={entry} />
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

function Gradient({ block }: { block: Block }) {
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
