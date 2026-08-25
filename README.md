# Thessaloniki interactive map

An atlas of Thessaloniki's urban infrastructure, organised around three
nested administrative zones — Urban, Metropolitan and Regional.

Those zones dissolve into a single **study boundary**, which every other
layer is clipped to. That is what keeps 1.4 million building footprints
down to the 187,000 that fall inside the region.

## What it shows

| Theme | Layers |
|---|---|
| Zones | Urban / Metropolitan / Regional frame |
| Transport | metro line and stations, bus stops, bus lanes, bike lanes, ferry, taxi, parking |
| Environment | buildings, water network, lakes, street trees |
| Amenities | education, culture |

Two ideas make it more than a stack of layers.

**Detail arrives with zoom.** Nothing is simply on or off. Bus stops are
hidden below zoom 13, plain dots to 15, gain a service-intensity circle
at 15, and only reveal their station-type symbol at 16. Trees, the
densest layer, appear at 18 alone.

**Symbol size carries meaning.** A bus stop's outer circle is sized by
how many lines serve it, so network hierarchy reads at a glance rather
than as a uniform scatter of dots. Metro stations take the maximum band.

## Setup

```bash
conda create -n interactive-map -c conda-forge python=3.12 --file requirements.txt
conda activate interactive-map
pip install -e .
```

The editable install is what lets `import thessmap` work from any
directory — notebooks, scripts and tests alike.

## Use

```bash
# Build the map into outputs/
python scripts/build_map.py

# One theme at a time, for fast iteration
python scripts/build_map.py --only zones metro_line metro_stations

# Rebuild the web-ready layers from source
python scripts/prepare_layers.py --dry-run
python scripts/prepare_layers.py --only bus_stops trees
```

Then open `outputs/urban_metropolitan_regional_interactive.html`. It is
around 112 MB, so give the browser a moment: Folium inlines every
geometry into the page.

## Layout

```
src/thessmap/
├── config.py       paths and CRS constants, resolved from __file__
├── palette.py      every colour and size decision
├── registry.py     ★ all 35 layers and their zoom thresholds
├── data.py         MapData — lazy, cached layer loading
├── build.py        build_map()
├── prepare/        clip · simplify · reproject · classify
└── render/         basemap · builder · svg · markers · zoom
    └── layers/     one module per theme
```

**`registry.py` is the contract.** Every layer is declared once, with its
menu label, theme and zoom range. Rendering code asks for a group by id
and the thresholds come from the registry — no module hard-codes a zoom
level. Adding a theme means writing one layer module and one registry
entry.

## Data

`data/` holds source GeoPackages in EPSG:2100 (Greek Grid) and
`data/processed/` the web-ready layers in EPSG:4326. Neither is in
version control.

Two things worth knowing:

- `data/` is intentionally read-only; `data/processed/` is writable so
  the preparation step can run.
- Re-running preparation does **not** reproduce byte-identical files
  across library versions. GEOS changes ring rotation and coordinate
  precision between releases, so `clip` and `simplify` output drifts.
  Feature counts and shapes are unaffected. Back up `data/processed/`
  before regenerating, and pin the geometry stack if you need
  reproducibility.

## Where this is heading

Folium inlines all geometry, which is why the page is 112 MB regardless
of which layers are switched on. The fix is vector tiles: bake the
processed layers into PMTiles and render with MapLibre, so the browser
fetches only what is in view.

The structure anticipates that. `prepare/`, `palette.py` and
`classify.py` carry over untouched; `registry.py` generates the MapLibre
style's `minzoom`/`maxzoom` directly, so thresholds never get duplicated
between Python and the frontend. Only `render/` gets replaced.
