#!/usr/bin/env python
"""How many residents live within walking distance of a location.

    python scripts/hub_catchment.py 22.9486 40.6262
    python scripts/hub_catchment.py 22.9486 40.6262 --radius 400 800 1500

Sums the GHSL 100 m population grid over the cells whose centres fall
inside each radius. 800 m is the usual ten-minute walk.

Straight-line distance, not street network: a real walkshed is shorter
than a circle wherever the street grid is interrupted, so treat these as
upper bounds until isochrones are wired in.
"""

import argparse
import sys

from thessmap import rasterexport

# The ten-minute walk, and a shorter and longer bracket around it
DEFAULT_RADII = (400, 800, 1500)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("lon", type=float, help="longitude, EPSG:4326")
    parser.add_argument("lat", type=float, help="latitude, EPSG:4326")
    parser.add_argument("--radius", type=float, nargs="+", default=DEFAULT_RADII,
                        metavar="M", help="one or more radii in metres")
    args = parser.parse_args(argv)

    print(f"Hub at {args.lat:.5f}, {args.lon:.5f}\n")
    print(f"{'radius':>8}  {'residents':>10}  {'cells':>6}  {'per km2':>8}")

    for radius in args.radius:
        result = rasterexport.hub_catchment((args.lon, args.lat), radius)

        # Density over the populated cells rather than over the circle:
        # a waterfront hub has half its circle in the sea, and dividing
        # by the full disc would understate how dense its catchment is.
        land = result["cells"] * 0.01
        density = result["population"] / land if land else 0

        print(f"{radius:>7.0f}m  {result['population']:>10,}  "
              f"{result['cells']:>6}  {density:>8,.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
