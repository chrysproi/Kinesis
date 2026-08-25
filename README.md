# Kinesis City Hub

An interactive map of Thessaloniki's urban infrastructure — transport
networks, mobility hubs, amenities, population density and environment —
across three nested administrative zones: Urban, Metropolitan and
Regional.

The zones dissolve into a single **study boundary** that every other
dataset is clipped to before it reaches the frontend. That is what keeps
2.0 million building footprints down to the 193,000 inside the region.

## How it works

```
source GeoPackages
      │
      │  scripts/prepare_layers.py
      ▼
data/processed/
      │
      │  scripts/export_web_data.py
      ▼
web/public/data/
web/src/generated/layerRegistry.ts
      │
      ▼
React + MapLibre map
```

The Python package owns data preparation and the layer registry. The
frontend consumes the generated layer definitions and GeoJSON, and never
declares a layer of its own.

`src/thessmap/registry.py` is the source of truth for what layers exist,
how they are grouped, and when their detail appears with zoom.
`web/src/config/layerConfig.ts` is the other half: presentation
overrides the frontend owns, and nothing else.

## Repository

```
├── src/thessmap/      Python package
├── scripts/           command-line entry points
├── web/               React + MapLibre frontend
├── tests/             contract tests over both halves of the repo
├── notebooks/         Folium preview notebook
├── data/              source and processed spatial data, not in git
└── outputs/           generated Folium output, not in git
```

For the implementation detail:

| Area | Read this | Covers |
|---|---|---|
| Python | [`src/thessmap/README.md`](src/thessmap/README.md) | registry, palette, preparation pipeline, exports |
| Web | [`web/README.md`](web/README.md) | running the map, configuration, zoom and visibility behaviour |
| Scripts | [`scripts/README.md`](scripts/README.md) | commands, arguments, regeneration and checks |

## Run the map

The committed files in `web/public/data/` are enough to run the
frontend:

```bash
cd web
npm install
npm run dev
```

Python and the source GeoPackages are only required when regenerating
the processed layers.

## Data

Source GeoPackages live under `data/` in EPSG:2100 (Greek Grid);
prepared web layers under `data/processed/` in EPSG:4326.

Neither directory is committed — together they are about 1.5 GB. The
exported GeoJSON under `web/public/data/` **is** committed, so a fresh
clone runs without the source data and nothing in CI has to regenerate
it.

## Licence and attribution

Basemap © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, © [CARTO](https://carto.com/attributions). Population
figures from ELSTAT (2021) and the JRC Global Human Settlement Layer
(2020).
