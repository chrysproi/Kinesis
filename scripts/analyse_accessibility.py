"""Bus-Metro integration and Metro walking catchments.

    python scripts/analyse_accessibility.py

Both are computed along the pedestrian network rather than as straight
lines or circular buffers, and both write a GeoPackage into
data/processed/ for later use. Neither is added to the map: the brief
treats them as inputs to the hub work, not as display layers.

    --threshold  walking distance for the bus-metro pass, metres
    --minutes    catchment thresholds, minutes
"""

import argparse
import sys

import geopandas as gpd

from thessmap import config, walknet

INTEGRATION_LAYER = "metro_bus_integration"
CATCHMENT_LAYER = "metro_walk_catchment"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--threshold", type=float, default=300, metavar="M",
                        help="bus-metro walking threshold in metres (default 300)")
    parser.add_argument("--minutes", type=int, nargs="+",
                        default=list(walknet.CATCHMENT_MINUTES), metavar="N",
                        help="catchment thresholds in minutes (default 5 10)")
    args = parser.parse_args(argv)

    print("Pedestrian network")
    network = walknet.build()

    stations = gpd.read_file(config.raw_path("metro_stations"))
    stops = gpd.read_file(config.processed_path("bus_stops"))

    print(f"\nBus-Metro integration ({args.threshold:.0f} m walk)")
    integration = walknet.bus_metro_integration(
        stations, stops, network, metres=args.threshold
    )
    _save(integration, INTEGRATION_LAYER)

    ranked = integration.sort_values("BUS_LINES_NEAR", ascending=False)
    print(f"\n  {'station':<28} {'stops':>6} {'lines':>6}")
    for row in ranked.itertuples():
        print(f"  {str(row.METRO_NAME):<28} {row.BUS_STOPS_NEAR:>6} "
              f"{row.BUS_LINES_NEAR:>6}")

    isolated = ranked[ranked.BUS_LINES_NEAR == 0]
    if len(isolated):
        print(f"\n  no bus connection within {args.threshold:.0f} m: "
              f"{', '.join(str(n) for n in isolated.METRO_NAME)}")

    print(f"\nWalking catchments ({', '.join(str(m) for m in args.minutes)} min)")
    catchments = walknet.walking_catchment(
        stations, network, minutes=tuple(args.minutes)
    )
    _save(catchments, CATCHMENT_LAYER)

    return 0


def _save(gdf, name):
    """Write to data/processed in the web CRS, like every other layer."""

    path = config.PROCESSED / f"{name}_web_4326.gpkg"
    path.parent.mkdir(parents=True, exist_ok=True)

    web = gdf.to_crs(epsg=config.WEB_CRS)
    web.to_file(path, layer=f"{name}_web_4326", driver="GPKG")

    print(f"  saved {len(web)} features -> {path.name}")


if __name__ == "__main__":
    sys.exit(main())
