# thessmap

The Python package. It prepares the source GeoPackages into web-ready
layers and generates the frontend's layer definitions from a single
registry.

Installed editable (`pip install -e .`) so `import thessmap` works from a
notebook, a script or a test alike. Run it through
[`scripts/`](../../scripts/).

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

Nothing else hard-codes a zoom level, and `web/src/generated/layers.ts`
is generated from this file — so adding a layer means a registry entry
and a prepare rule, not a change in two languages.

## Modules

| Module | What it does |
|---|---|
| `registry.py` | ★ every layer, its theme and its zoom thresholds |
| `palette.py` | every colour, width and size decision |
| `config.py` | paths and CRS constants, resolved from `__file__` |
| `data.py` | `MapData` — lazy, cached reads of raw and processed layers |
| `webexport.py` | GeoJSON + `layers.ts`: MapLibre paint, menu, legend, sprites |
| `rasterexport.py` | GeoTIFF → pre-coloured PNG, since MapLibre reads no TIFF |
| `classify.py` | Jenks breaks, matching what QGIS produces |
| `indicators.py` | the mapped socio-demographic indicators |
| `walknet.py` | the pedestrian network as a routable graph |
| `build.py` | `build_map()`, the Folium renderer's entry point |

### `prepare/`

Clip · reproject · simplify · classify. `pipeline.py` is the common path;
`sources.py` lists the simple layers that need nothing but it. Anything
needing real work gets a module: `buildings.py`, `water.py`,
`walkways.py`, `amenities.py`, `destinations.py`, `openspaces.py`,
`hubs.py`, `special.py`.

### `render/`

The Folium renderer, kept for the notebook. `builder.py` assembles,
`layers/` holds one module per theme, `zoom.py` turns registry thresholds
into Leaflet zoom rules. The MapLibre frontend does not use any of it.

## Coordinate systems

Source data is EPSG:2100 (Greek Grid), so distances and simplification
tolerances are in metres. Everything is reprojected to EPSG:4326 on the
way out. The GHSL population raster arrives in ESRI:54009 (Mollweide) and
is warped to EPSG:3857 for the browser.
