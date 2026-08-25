# Scripts

Command-line entry points, thin by design: they parse flags and call
into [`thessmap`](../src/thessmap/README.md). Every one takes `--help`.

Run them from the repository root, with the
[package environment](../src/thessmap/README.md#install) active and the
source GeoPackages in `data/`. Once launched, their input and output
paths are resolved by the package rather than from the working
directory.

## The pipeline

### `prepare_layers.py` — source → `data/processed/`

Clips to the study boundary, reprojects to EPSG:4326, simplifies and
classifies. Overwrites what the map reads, so back it up first if you
need the current files.

```bash
python scripts/prepare_layers.py --dry-run          # list what would run
python scripts/prepare_layers.py --only bus_stops trees
python scripts/prepare_layers.py --out build/processed
```

### `export_web_data.py` — `data/processed/` → `web/`

Writes GeoJSON into `web/public/data/` and TypeScript into
`web/src/generated/layerRegistry.ts`.

```bash
python scripts/export_web_data.py
python scripts/export_web_data.py --types-only      # style or zoom change only
python scripts/export_web_data.py --bbox 22.9 40.6 23.0 40.7
```

`--types-only` is the one to reach for while tuning a colour or a zoom
threshold: it takes a second, and Vite hot-reloads the result.

## Analysis

### `hub_catchment.py` — residents within walking distance

Sums the GHSL 100 m population grid over the cells inside each radius.
800 m is the usual ten-minute walk. Straight-line, so treat the figures
as upper bounds.

```bash
python scripts/hub_catchment.py 22.9486 40.6262
python scripts/hub_catchment.py 22.9486 40.6262 --radius 400 800 1500
```

### `analyse_accessibility.py` — bus–metro integration and walk catchments

Both computed along the pedestrian network rather than as circles, and
written to `data/processed/` as GeoPackages. Neither is a map layer:
they are inputs to the hub siting work.

```bash
python scripts/analyse_accessibility.py
python scripts/analyse_accessibility.py --threshold 400 --minutes 5 10 15
```

## The Folium renderer

### `build_map.py` — a standalone HTML map

The original renderer, kept because the [notebook](../notebooks/) drives
it. Folium inlines every geometry, so the page is large; `--only` is the
fast way to look at one theme.

```bash
python scripts/build_map.py
python scripts/build_map.py --only zones metro_line metro_stations
python scripts/build_map.py --output outputs/preview.html
```

Writes to `outputs/`.

## Checks

```bash
pytest                      # registry, export and frontend contracts
```

Contract tests rather than unit tests: every detail names a real parent,
the committed `layerRegistry.ts` matches what the registry would emit
now, every source has a file behind it, every icon reference resolves to
a sprite, and the frontend's dependencies never run upward. They fail
when Python and the frontend drift apart, which is the failure this
architecture is exposed to.

On the frontend:

```bash
cd web
npm run lint
npm run build               # tsc -b && vite build
```
