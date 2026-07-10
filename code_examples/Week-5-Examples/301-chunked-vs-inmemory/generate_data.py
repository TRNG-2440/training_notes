"""Generate a largish CSV of fake sales so we can demonstrate the
'too big for a naive approach' problem without downloading anything.

Default is 5 million rows (~150-200 MB). That is large enough to make the
in-memory approach visibly heavier than the chunked one, but small enough
to finish in a few seconds on a laptop. Bump --rows if you have RAM to spare.

Usage:
    python generate_data.py                 # 5,000,000 rows -> sales.csv
    python generate_data.py --rows 2000000  # smaller/faster
    python generate_data.py --out big.csv --rows 10000000
"""
from __future__ import annotations

import argparse
import csv
import os
import random

CATEGORIES = [
    "electronics", "grocery", "clothing", "toys", "books",
    "home", "sports", "beauty", "automotive", "garden",
]


def generate(path: str, rows: int, seed: int = 42) -> None:
    random.seed(seed)
    # Write with the stdlib csv module and a plain loop so that *generation*
    # itself never holds all rows in memory. The whole point of the demo is
    # streaming, so we practice what we preach even while making the file.
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "category", "value"])
        for order_id in range(1, rows + 1):
            category = random.choice(CATEGORIES)
            value = round(random.uniform(1.0, 500.0), 2)
            writer.writerow([order_id, category, value])

    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"Wrote {rows:,} rows to {path}  ({size_mb:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a fake sales CSV.")
    parser.add_argument("--rows", type=int, default=5_000_000,
                        help="number of data rows (default: 5,000,000)")
    parser.add_argument("--out", default="sales.csv",
                        help="output CSV path (default: sales.csv)")
    args = parser.parse_args()
    generate(args.out, args.rows)


if __name__ == "__main__":
    main()
