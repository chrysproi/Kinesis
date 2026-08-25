# Frontend

React 19 + TypeScript + Vite, drawing with [MapLibre GL JS](https://maplibre.org/)
on a CARTO Positron raster basemap. State is [Zustand](https://zustand.docs.pmnd.rs/);
styling is Tailwind v4 through `@theme` tokens in `src/index.css`.

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # tsc -b && vite build  →  dist/
npm run lint       # oxlint
```

## The generated layer module

`src/generated/layers.ts` is written by `scripts/export_web_data.py` from
`registry.py` and `palette.py`. **Do not edit it** — change the Python and
regenerate:

```bash
python scripts/export_web_data.py --types-only
```

It exports the layer list and MapLibre paint, the sidebar menu tree, the
legend blocks, icon sprites, zoom thresholds and the viewport limits. A
new layer therefore needs no TypeScript at all — only a registry entry
and, if it draws an icon, one line in `src/components/lucide.tsx` and one
in `src/map/icons.ts`.

## Layout

| Path | What it is |
|---|---|
| `src/map/MapView.tsx` | creates the map, adds sources and layers, wires clicks |
| `src/map/icons.ts` | lucide SVGs rasterised for `addImage`, plus the hand-drawn sprites |
| `src/map/popup.ts` | the feature card |
| `src/map/clusters.ts` | cluster badges as DOM markers |
| `src/store.ts` | which layers are on, and the zoom rules that change that |
| `src/hooks/useHashState.ts` | `#zoom/lat/lon/-off,+on` in the address bar |
| `src/components/` | sidebar, legend, active-layer chips, switch, zoom badge |

## Two things that are easy to trip over

**Icons are rasters, not DOM nodes.** MapLibre draws symbols from images
registered with `addImage`, which is why this uses `lucide-static` rather
than `lucide-react` for the map, and `lucide-react` for the sidebar and
legend. Both come from the same icon set so the key matches the map.

**The URL carries a difference, not a state.** `#9.66/40.64/22.90/-zones,+trees`
means "the defaults, minus zones, plus trees" — so a shared link stays
short and keeps working when a default changes. An older absolute list is
still read.

## Deploying

The build is static. For a GitHub Pages project site set `base` in
[vite.config.ts](vite.config.ts) to `"/<repo-name>/"` first, or every
asset 404s.

`public/data/` is 86 MB of GeoJSON, written with a `.json` extension so
static hosts gzip it — `application/geo+json` is not on their compressible
lists, and the largest file is 64 MB raw against 6.5 MB gzipped.

A first visit fetches about 4 MB of that. `buildings_height.json` (61 MB)
and `trees.json` are fetched lazily, only if switched on.
