# Kinesis City Hub

An interactive map of Thessaloniki's urban infrastructure — transport
networks, mobility hubs, amenities, population density and environment —
across three nested administrative zones: Urban, Metropolitan and
Regional.

The zones dissolve into a single **study boundary** that every other
layer is clipped to. That is what keeps 1.4 million building footprints
down to the 220,000 inside the region.

## How it fits together

A Python package prepares the data and **generates the frontend's layer
definitions**; a React app draws them.

```
data/*.gpkg                 source GeoPackages, EPSG:2100, not in git
    │
    │  scripts/prepare_layers.py
    ▼
data/processed/*.gpkg       clipped to the study area, EPSG:4326, not in git
    │
    │  scripts/export_web_data.py
    ▼
web/public/data/*.json      GeoJSON, in git
web/src/generated/layers.ts in git — layer ids, zooms, paint, legend
    │
    │  npm run dev
    ▼
the map
```

`src/thessmap/registry.py` is the single source of truth: 78 layers
behind 28 switches, each declared once with its theme, zoom thresholds
and menu grouping. Nothing hard-codes a zoom level, and no layer is
declared twice — `layers.ts` is generated from it, never hand-edited.

## Run it

The committed GeoJSON is enough to run the map. You need the source data
only to regenerate layers.

```bash
cd web
npm install
npm run dev            # http://localhost:5173
```

To work on the Python side as well:

```bash
conda create -n interactive-map -c conda-forge python=3.12 --file requirements.txt
conda activate interactive-map
pip install -e .       # editable, so `import thessmap` works from anywhere
```

Then, with the source GeoPackages in `data/`:

```bash
python scripts/prepare_layers.py       # source  → data/processed/
python scripts/export_web_data.py      # processed → web/
```

Changing only a colour or a zoom threshold needs neither — regenerate the
type definitions alone and Vite hot-reloads:

```bash
python scripts/export_web_data.py --types-only
```

## Two ideas worth knowing

**Detail arrives with zoom.** Nothing is simply on or off. A bus stop is
nothing below zoom 12, a plain dot to 14, gains a circle sized by the
lines it serves at 14, and only shows its station-type symbol at 15.
Trees run the same way: a density wash at 13, a stipple at 16,
individual crowns at 18. The zone frame runs the other way — on at the
opening view, and closing itself on the first zoom in.

**Symbol size carries meaning.** A bus stop's outer circle is sized by
how many lines serve it, so network hierarchy reads at a glance rather
than as a uniform scatter of dots. Metro stations take the maximum band.

## Layout

| Path | What it is |
|---|---|
| [`src/thessmap/`](src/thessmap/) | the Python package — registry, palette, data prep, export |
| [`scripts/`](scripts/) | the command-line entry points |
| [`web/`](web/) | the React + MapLibre frontend |
| [`notebooks/`](notebooks/) | a preview notebook driving the Folium renderer |
| `data/` | source and processed GeoPackages, not in version control |

Each of the first three has its own README.

## Data

`data/` holds source GeoPackages in EPSG:2100 (Greek Grid);
`data/processed/` holds the web-ready layers in EPSG:4326. Neither is in
version control — together they are about 1.5 GB — which is why
`web/public/data/` **is** committed: without it a clone has no map, and
nothing in CI could regenerate it.

Two things worth knowing:

- `data/` is intentionally read-only; `data/processed/` is writable so
  the preparation step can run.
- Re-running preparation does **not** reproduce byte-identical files
  across library versions. GEOS changes ring rotation and coordinate
  precision between releases, so `clip` and `simplify` output drifts.
  Feature counts and shapes are unaffected. Back up `data/processed/`
  before regenerating, and pin the geometry stack if you need
  reproducibility.

## Licence and attribution

Basemap © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, © [CARTO](https://carto.com/attributions). Population
figures from ELSTAT (2021) and the JRC Global Human Settlement Layer
(2020).
