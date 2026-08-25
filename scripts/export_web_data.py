#!/usr/bin/env python
"""Generate the web app's data and layer definitions.

    python scripts/export_web_data.py

Writes GeoJSON into web/public/data/ and TypeScript into
web/src/generated/layers.ts. Both come from registry.py and palette.py,
so a layer is never declared twice.
"""

import argparse
import sys
from pathlib import Path

from thessmap import config, rasterexport, webexport
from thessmap.data import MapData

WEB = config.PROJECT_ROOT / "web"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--web", type=Path, default=WEB,
                        help="frontend directory (default: web/)")
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"),
                        help="cut to a window, for a lighter dev dataset")
    parser.add_argument("--types-only", action="store_true",
                        help="regenerate layers.ts without re-exporting GeoJSON")
    args = parser.parse_args(argv)

    types_path = args.web / "src" / "generated" / "layers.ts"

    print("Layer definitions")
    webexport.write_layers_ts(types_path)

    if args.types_only:
        return 0

    bbox = tuple(args.bbox) if args.bbox else None
    data = MapData(bbox=bbox)

    destination = args.web / "public" / "data"

    print("\nGeoJSON")
    written = webexport.export_geojson(data, destination)

    print("\nRasters")
    for name, (stem, png) in webexport.RASTER_SOURCES.items():
        rasterexport.export_population_raster(
            config.RASTERS / f"{stem}.tif",
            destination / png,
            # The same classes as the municipal choropleth, so a cell can
            # be compared against its municipality's average
            breaks=webexport.density_breaks(),
        )

    total = sum(written.values()) / 1e6
    print(f"\n{len(written)} files, {total:.1f} MB total")
    if total > 25:
        print("  Large for plain GeoJSON — vector tiles will fix this.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
