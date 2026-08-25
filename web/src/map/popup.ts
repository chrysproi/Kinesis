/**
 * Feature cards.
 *
 * Styled as an annotation on an architectural drawing rather than a web
 * tooltip: a letterspaced eyebrow naming the layer, one strong title, a
 * hairline rule, then a label/value grid with figures set in mono.
 *
 * Styles live in index.css under `.tm-*` because MapLibre injects this
 * HTML into its own DOM, outside React and outside Tailwind's reach.
 */

import { VALUE_LABELS } from "../generated/layers";

/**
 * Fields worth showing, in the order they should appear.
 *
 * `symbol_origin` is deliberately absent. It records whether a symbol
 * came from a polygon or a standalone node — bookkeeping the thinning
 * step needs and a reader never does. It surfaced as a "Derived from"
 * row on most amenities, and on an unnamed playground node it was the
 * only field present, so it became the card's heading: a popup whose
 * entire content was the word "node".
 *
 * With it gone, a feature carrying nothing else returns null and no card
 * opens at all, which is the right answer.
 */
const PREFERRED = [
  "name",
  "name:el",
  "NAME_ENG",
  "DIMOS",
  "POP_2021",
  "AREA_KM2",
  "POP_DENS",
  "onomastasi",
  "zone",
  "education_type",
  "culture_subtype",
  "hub_tier",
  "hub_tier_el",
  "hub_space",
  "PT_ACCESS_SCORE",
  "dest_category",
  "walk_class",
  "waterway",
  "fclass",
  "ROOF_H",
  "MAX_FLOOR",
  "NO_APPART",
  "LU_GROUP",
  "landuse",
  "sport",
  "beds",
  "emergency",
  "operator",
  "opening_hours",
  "tree_class",
  "stop_type_cat",
  "service_level",
  "line_count",
  "lines_ejyp",
  "type",
  "code",
  "dimoskal",
];

const LABELS: Record<string, string> = {
  "name:el": "Greek name",
  DIMOS: "\u0394\u03ae\u03bc\u03bf\u03c2",
  NAME_ENG: "Area",
  POP_2021: "Population 2021",
  AREA_KM2: "Area",
  POP_DENS: "Population density",
  onomastasi: "Stop",
  zone: "Zone",
  education_type: "Type",
  culture_subtype: "Type",
  hub_tier: "Hub tier",
  hub_tier_el: "\u039f\u03bd\u03bf\u03bc\u03b1\u03c3\u03af\u03b1",
  hub_space: "Site today",
  PT_ACCESS_SCORE: "PT access",
  dest_category: "Type",
  walk_class: "Way",
  waterway: "Waterway",
  fclass: "Class",
  ROOF_H: "Roof height",
  MAX_FLOOR: "Floors",
  NO_APPART: "Apartments",
  LU_GROUP: "Land use",
  landuse: "Detail",
  sport: "Sport",
  beds: "Beds",
  emergency: "Emergency dept.",
  operator: "Operator",
  opening_hours: "Opening hours",
  tree_class: "Height",
  stop_type_cat: "Category",
  service_level: "Service",
  line_count: "Lines",
  lines_ejyp: "Routes",
  dimoskal: "Municipality",
  code: "Code",
  type: "Class",
};

/** Values that read as measurements rather than labels. */
const UNITS: Record<string, string> = {
  tree_class: "m",
  AREA_KM2: "km\u00b2",
  ROOF_H: "m",
  POP_DENS: "inhab./km\u00b2",
};

/**
 * How to render a figure. Census counts and densities are read as
 * magnitudes, so they take thousands separators; an area of 21.36 km2
 * would be false precision at more than two decimals, and a density
 * estimate at any.
 */
const FIGURES: Record<string, (value: number) => string> = {
  POP_2021: (value) => value.toLocaleString("en-GB"),
  POP_DENS: (value) => Math.round(value).toLocaleString("en-GB"),
  AREA_KM2: (value) => value.toFixed(2),
  PT_ACCESS_SCORE: (value) => value.toFixed(2),
  ROOF_H: (value) => value.toFixed(1),
};

/** Formats a value for display, falling through to the raw string. */
const format = (key: string, value: unknown) => {
  // Coded values get their display label from Python, so the popup and
  // the legend can never disagree about what RESIDENTIAL is called.
  const labelled = VALUE_LABELS[key]?.[String(value)];
  if (labelled) return labelled;

  const figure = FIGURES[key];
  if (!figure) return String(value);

  const numeric = Number(value);
  return Number.isFinite(numeric) ? figure(numeric) : String(value);
};

/**
 * Fields that may appear as a row but never as the card's title.
 *
 * The title is the first present field, which works while that field is
 * a name. Buildings carry no name at all, so a roof height of 31.3 was
 * being set as the heading — a measurement pretending to be an identity.
 */
const NEVER_TITLE = new Set([
  "ROOF_H",
  "MAX_FLOOR",
  "NO_APPART",
  "POP_2021",
  "AREA_KM2",
  "POP_DENS",
  "line_count",
  "beds",
]);

/** Values set in mono: figures, codes, route lists. */
const MONO = new Set([
  "line_count",
  "lines_ejyp",
  "code",
  "tree_class",
  "beds",
  "POP_2021",
  "AREA_KM2",
  "POP_DENS",
  "PT_ACCESS_SCORE",
  "ROOF_H",
  "MAX_FLOOR",
  "NO_APPART",
]);

const escape = (value: unknown) =>
  String(value).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!,
  );

const label = (key: string) =>
  LABELS[key] ?? key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");

const present = (properties: Record<string, unknown>, key: string) => {
  const value = properties[key];
  return value !== undefined && value !== null && String(value).trim() !== "";
};

/**
 * Source layers carry wildly different attributes — OSM tags on some,
 * Greek national schema fields on others — so show the fields known to
 * be meaningful and skip the rest.
 *
 * Returns null when the feature carries nothing worth showing, so the
 * caller can skip the popup instead of opening an empty card.
 *
 * @param kind Human label for the layer clicked, shown as the eyebrow.
 */
export function featurePopupHtml(
  properties: Record<string, unknown>,
  kind?: string,
): string | null {
  const rows = PREFERRED.filter((key) => present(properties, key));

  if (rows.length === 0) return null;

  const eyebrow = kind ? `<p class="tm-kind">${escape(kind)}</p>` : "";

  // A measurement is never the heading. When nothing else identifies the
  // feature, the layer name becomes the title and the eyebrow is dropped
  // rather than repeating it twice.
  const titleKey = rows.find((key) => !NEVER_TITLE.has(key));
  const rest = rows.filter((key) => key !== titleKey);

  const title = titleKey ? format(titleKey, properties[titleKey]) : kind;

  if (!title) return null;

  const head =
    `<header class="tm-head">${titleKey ? eyebrow : ""}` +
    `<h2 class="tm-title">${escape(title)}</h2></header>`;

  const body = rest.length
    ? `<dl class="tm-body">${rest
        .map((key) => {
          const unit = UNITS[key]
            ? `<span class="tm-unit">${UNITS[key]}</span>`
            : "";
          const mono = MONO.has(key) ? " tm-value--mono" : "";
          return (
            `<div class="tm-row">` +
            `<dt class="tm-label">${label(key)}</dt>` +
            `<dd class="tm-value${mono}">` +
            `${escape(format(key, properties[key]))}${unit}</dd>` +
            `</div>`
          );
        })
        .join("")}</dl>`
    : "";

  return `<article class="tm-card">${head}${body}</article>`;
}
