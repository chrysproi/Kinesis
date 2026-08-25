"""Build web-ready layers from the source GeoPackages.

    python scripts/prepare_layers.py --dry-run
    python scripts/prepare_layers.py --only bus_stops trees
    python scripts/prepare_layers.py --out /tmp/processed

This overwrites data/processed/, which is what the map reads. Because
GEOS output varies between library versions, re-running will not always
reproduce byte-identical files — back up data/processed/ first if you
need the current ones.
"""

import argparse
import sys
from pathlib import Path

from thessmap import config
from thessmap.prepare import ALL_NAMES, prepare_all


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--only", nargs="+", metavar="LAYER", choices=ALL_NAMES,
        help=f"build a subset. Choices: {', '.join(ALL_NAMES)}",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="destination directory (default: data/processed)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="list what would be built, write nothing",
    )
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args(argv)

    targets = args.only or ALL_NAMES

    if args.dry_run:
        print(f"Would build {len(targets)} layers into "
              f"{args.out or config.PROCESSED}:")
        for name in targets:
            print(f"  {name}")
        return 0

    destination = args.out or config.PROCESSED

    if destination == config.PROCESSED:
        print("Overwriting data/processed/ — the layers the map reads.\n")

    timings = prepare_all(
        only=args.only, processed=destination, verbose=not args.quiet
    )

    total = sum(timings.values())
    print(f"Built {len(timings)} layers in {total:.1f}s")

    slowest = sorted(timings.items(), key=lambda kv: -kv[1])[:3]
    for name, seconds in slowest:
        print(f"  {name}: {seconds:.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
