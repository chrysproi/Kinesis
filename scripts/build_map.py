"""Build the interactive map and write it to outputs/.

    python scripts/build_map.py
    python scripts/build_map.py --only zones metro_line metro_stations
    python scripts/build_map.py --output outputs/preview.html

Buildings and trees dominate the file size, so `--only` is the fast way
to iterate on a single theme.
"""

import argparse
import sys
import time
from pathlib import Path

from thessmap import config
from thessmap.build import STEP_NAMES, build_map


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--only", nargs="+", metavar="LAYER", choices=STEP_NAMES,
        help=f"build a subset. Choices: {', '.join(STEP_NAMES)}",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help=f"destination HTML (default: outputs/{config.MAP_FILENAME})",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress progress")

    args = parser.parse_args(argv)

    started = time.perf_counter()

    builder = build_map(only=args.only, verbose=not args.quiet)
    path = builder.save(args.output)

    elapsed = time.perf_counter() - started
    size_mb = path.stat().st_size / 1e6

    print(f"\nSaved {path}")
    print(f"  {size_mb:.1f} MB in {elapsed:.1f}s")
    print(f"  {len(builder.groups)} feature groups, "
          f"{len(builder.zoom_rules())} zoom rules")

    return 0


if __name__ == "__main__":
    sys.exit(main())
