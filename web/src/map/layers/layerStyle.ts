import { CONFIG } from "../../config/layerConfig";
import { ownerOf } from "../../layers/zoom";

/**
 * Multiplies a paint value that may be a number or an expression.
 *
 * A zoom expression cannot simply be wrapped: MapLibre only allows
 * `["zoom"]` as the input to a *top-level* step or interpolate, so
 * `["*", ["interpolate", …], 0.5]` is rejected and the layer never
 * draws. The factor therefore goes into the outputs instead, which is
 * the same arithmetic one level down. Anything else — a match on a
 * feature property, a literal — has no zoom in it and can be wrapped.
 */
export function scale(value: unknown, factor: number): unknown {
  if (typeof value === "number") return value * factor;
  if (!Array.isArray(value)) return value;

  const [kind] = value;

  if (
    kind === "interpolate" ||
    kind === "interpolate-hcl" ||
    kind === "interpolate-lab"
  ) {
    // ["interpolate", type, input, stop, output, stop, output, …]
    return value.map((item, index) =>
      index >= 4 && index % 2 === 0 ? scale(item, factor) : item,
    );
  }

  if (kind === "step") {
    // ["step", input, output, stop, output, …]
    return value.map((item, index) =>
      index >= 2 && index % 2 === 0 ? scale(item, factor) : item,
    );
  }

  return ["*", value, factor];
}

/** A map layer, as much of one as the paint model needs to see. */
export interface PaintedLayer {
  metadata: Record<string, string>;
  paint?: Record<string, unknown>;
}

/** Paint with the config's opacity multiplier folded in. */
export function paintFor(layer: PaintedLayer) {
  const factor = CONFIG.opacity[ownerOf(layer)];
  if (factor === undefined || factor === 1 || !layer.paint) return layer.paint;

  const paint: Record<string, unknown> = { ...layer.paint };

  for (const [property, value] of Object.entries(paint)) {
    if (!property.endsWith("-opacity")) continue;
    paint[property] = scale(value, factor);
  }

  return paint;
}
