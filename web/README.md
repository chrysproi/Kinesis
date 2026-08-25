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

## How the map behaves

**Detail arrives with zoom.** Nothing is simply on or off. A bus stop is
nothing below zoom 12, a plain dot to 14, gains a circle sized by the
lines it serves at 14, and only shows its station-type symbol at 15.
Trees run the same way: a density wash at 13, a stipple at 16,
individual crowns at 18. The zone frame runs the other way — on at the
opening view, closing itself on the first zoom in, and reopening if you
zoom back out.

Those tiers are declared in the Python registry as parent and detail
layers; the frontend reads the thresholds and switches between them. See
[the registry](../src/thessmap/README.md#registrypy-is-the-contract) for
how they are written, and `zoom` in the config below for shifting them
without touching Python.

**Symbol size carries meaning.** A bus stop's outer circle is sized by
how many lines serve it, so network hierarchy reads at a glance rather
than as a uniform scatter of dots. Metro stations take the maximum band.

## Configuring it

[`src/config/layerConfig.ts`](src/config/layerConfig.ts) holds the
frontend's knobs. Edit it,
save, and Vite reloads — no Python, no regeneration.

Every entry is optional and everything starts empty. Leave a layer out
and it keeps the value it was generated with; name it and yours wins.

**Keys are layer ids, the ones in the sidebar and the URL** — `trees`,
`bus_stops`, `parking`, `bike_lanes`. Not the internal per-zoom ids, so
one line covers every tier a layer draws. Read them off a shared link:
`#14.6/40.64/22.93/+trees` names `trees`.

### opacity

A multiplier on every opacity the layer paints — fill, line, circle,
halo, heatmap alike. `1` is unchanged, `0` hides it.

```ts
opacity: {
  trees: 0.5,        // canopy at half strength
  bus_stops: 0.8,    // quieten the service halos
},
```

### zoom

`shift` moves every tier by the same amount and keeps the staircase
intact — a bus stop still goes dot → sized circle → symbol, just
earlier or later. `min` and `max` clamp afterwards, as hard bounds.

```ts
zoom: {
  trees: { shift: -3 },            // all three tiers, three zooms earlier
  bus_stops: { min: 11 },          // never before 11, whatever the tier
  buildings: { min: 13, max: 18 },
},
```

### theme and themeOrder

`theme` moves a layer into a different group, in the sidebar and the
legend together. `themeOrder` puts groups you name first; anything
unlisted keeps its position after them.

```ts
theme: { parking: "transport", taxi: "transport" },
themeOrder: ["transport", "services"],
```

The group keys are `zones`, `environment`, `fabric`, `transport`,
`services`, `amenities`, `population`.

### startsOn

What is on when the map opens. A URL carrying a layer segment still
wins over this — it is the default, not a lock.

```ts
startsOn: { trees: true, ferry_routes: false },
```

## Two halves of the layer model

```
Python  →  src/generated/layerRegistry.ts    canonical generated defaults
human   →  src/config/layerConfig.ts         optional presentation overrides
```

`layerConfig.ts` is not a second registry. It names no layers of its own
and holds no defaults: every entry is an override of a value that
already exists, and an empty config leaves the map exactly as generated.

`layerRegistry.ts` is written by `scripts/export_web_data.py` from
`registry.py` and `palette.py`. **Do not edit it** — change the Python
and regenerate:

```bash
python scripts/export_web_data.py --types-only
```

That flag is the frontend inner loop: it rewrites the module in about a
second and Vite hot-reloads. Every other flag is documented in the
[Scripts README](../scripts/README.md), which owns them.

It exports the layer list and MapLibre paint, the sidebar menu tree, the
legend blocks, icon sprites, zoom thresholds and the viewport limits.

Most new layers therefore need no handwritten frontend definition at all
— add them to the Python registry and regenerate. A layer that draws an
icon additionally needs its glyph registered in `src/ui/lucide.tsx` and
`src/map/icons/sprites.ts`, which is the one place the two sides are
edited together.

## Layout

Folders are named after the domain — map, layers, sidebar, url — rather
than after the kind of file they hold.

```
src/
├── config/        human presentation decisions
├── generated/     the generated contract, never hand-edited
├── layers/        the layer model: state, visibility, zoom, grouping
├── map/           the MapLibre implementation
│   ├── layers/        adding sources and layers, and their paint
│   ├── interactions/  clicks and the feature card
│   └── icons/         sprite artwork, and registering it with the map
├── sidebar/       the layer-selection UI and the legend
├── ui/            genuinely reusable primitives
└── url/           the hash as application state, not a generic hook
```

The rule that matters: **dependencies run one way** — `generated` and
`config` are read by `layers`, `layers` by `map` and `sidebar`, and
nothing reads back upward. That one is enforced, not merely intended:
`tests/test_frontend.py` walks every relative import and fails on a
violation.

## Deploying

Pushing to `main` builds and publishes to GitHub Pages via
[.github/workflows/deploy.yml](../.github/workflows/deploy.yml) —
https://chrysproi.github.io/Kinesis/

`base` in [vite.config.ts](vite.config.ts) is `"/Kinesis/"` to match the
project-site path. Serving from anywhere else means changing it, or every
asset 404s.

`public/data/` is 86 MB of GeoJSON, written with a `.json` extension so
it is served as `application/json` — a content type GitHub Pages and the
common CDNs compress. Some hosts do gzip `application/geo+json` too, but
not all, and the difference is 64 MB raw against 6.5 MB gzipped on the
largest file.

A first visit fetches about 4 MB of that. `buildings_height.json` (61 MB)
and `trees.json` are fetched lazily, only if switched on.

### Where this stops scaling

GeoJSON is a deliberate choice for a static deployment of this size, and
the map already does most of what MapLibre recommends for large
datasets: URL-backed sources rather than inline data, reduced coordinate
precision, simplification, zoom gating and lazy loading of the two heavy
layers.

If the data grows materially, the next step is **vector tiles** (PMTiles
served statically), not a larger committed GeoJSON bundle. That would
also bring every file under the 25 MiB per-asset limit that currently
rules out Cloudflare Pages as a host.
