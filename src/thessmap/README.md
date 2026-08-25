# thessmap

The Python package. It prepares the source GeoPackages into web-ready
layers and generates the frontend's layer definitions from a single
registry.

Run it through [`scripts/`](../../scripts/).

## Install

Conda is the route to prefer: GDAL, GEOS and PROJ arrive as prebuilt
binaries from conda-forge rather than being compiled.

```bash
conda env create -f environment.yml
conda activate interactive-map
```

That installs the package editable and in place, which is what lets
`import thessmap` work from any directory — notebooks, scripts and tests
alike.

With pip alone, in an activated environment:

```bash
python -m pip install -e ".[dev]"
```

Dependencies are declared once, in `pyproject.toml`. `environment.yml`
names the same packages without versions, so the two cannot disagree
about a bound.

## `registry.py` is the contract

Every layer is declared once — 78 of them behind 28 switches — with its
theme, menu label and zoom range:

```python
LayerSpec("bus_stops", "Bus Stops", "transport", group="bus")
LayerSpec("bus_stops_simple",  "…", parent="bus_stops", min_zoom=12, max_zoom=15)
LayerSpec("bus_stops_outer",   "…", parent="bus_stops", min_zoom=14)
LayerSpec("bus_stops_symbols", "…", parent="bus_stops", min_zoom=15)
```

A **parent** is what the user toggles. A **detail** names a parent and a
zoom range, stays out of the menu, and switches itself on while its
parent is enabled and the zoom sits inside its range. That is the whole
mechanism behind "detail arrives with zoom".

Three other flags carry behaviour: `pinned` (always on, no switch),
`auto_hide_above` (closes itself past a zoom, reopens below it), and
`EXCLUSIVE` groups (only one layer per group may be on, for layers that
fill the same polygons).

Zoom thresholds are owned here rather than duplicated across the two
renderers, and `generated/layerRegistry.ts` is generated from this file
— so adding a layer means a registry entry and a prepare rule, not a
change in two languages.

`tests/test_registry.py` checks the invariants this section claims:
every detail names a real parent, ids are unique, ranges are ordered,
pinned layers stay out of the menu.

## Modules

| Module | What it does |
|---|---|
| `registry.py` | ★ every layer, its theme and its zoom thresholds |
| `palette.py` | every colour, width and size decision |
| `config.py` | paths and CRS constants, resolved from `__file__` |
| `data.py` | `MapData` — lazy, cached reads of raw and processed layers |
| `webexport.py` | GeoJSON + `layerRegistry.ts`: paint, menu, legend, sprites |
| `rasterexport.py` | GeoTIFF → pre-coloured PNG, since MapLibre reads no TIFF |
| `classify.py` | Jenks breaks, matching what QGIS produces |
| `indicators.py` | the mapped socio-demographic indicators |
| `walknet.py` | the pedestrian network as a routable graph |
| `build.py` | `build_map()`, the Folium renderer's entry point |

### `prepare/`

Clip · reproject · simplify · classify. `pipeline.py` is the common path
and `sources.py` lists the layers that need nothing more than it; each
source needing real work gets a module of its own beside them.

Preparation overwrites `data/processed/`, and **does not reproduce
byte-identical files across library versions**: GEOS changes ring
rotation and coordinate precision between releases, so `clip` and
`simplify` output drifts. Feature counts and shapes are unaffected. Back
up `data/processed/` before regenerating, and pin the geometry stack if
you need reproducibility.

`data/` is intentionally read-only; `data/processed/` is writable so the
preparation step can run.

### `render/`

The Folium renderer, kept for the notebook, with one module per theme
under `layers/`. The MapLibre frontend does not use any of it.

## Coordinate systems

Source data is EPSG:2100 (Greek Grid), so distances and simplification
tolerances are in metres. Everything is reprojected to EPSG:4326 on the
way out. The GHSL population raster arrives in ESRI:54009 (Mollweide) and
is warped to EPSG:3857 for the browser.
