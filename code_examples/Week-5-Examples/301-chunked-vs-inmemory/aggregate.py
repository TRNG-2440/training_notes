"""Aggregate a big CSV two ways and compare peak memory + timing.

  (a) IN-MEMORY : pd.read_csv() loads the ENTIRE file, then groupby.
  (b) CHUNKED   : pd.read_csv(chunksize=...) streams pieces, aggregates each,
                  and combines the small partial results at the end.

Both produce the identical answer (sum of `value` per `category`). The
difference is *how much memory* they need to get there. In-memory peaks at
~the size of the whole DataFrame; chunked peaks at ~the size of one chunk.

This is the single-machine version of the big-data lesson from
notes/301-big-data-fundamentals: when data is too big for RAM you stop
loading it all at once. Chunking is the stepping stone from pandas-on-one-box
to distributed engines like Spark and serverless warehouses like BigQuery.

Usage:
    python generate_data.py          # once, to create sales.csv
    python aggregate.py              # run both approaches on sales.csv
    python aggregate.py --chunksize 250000
    python aggregate.py --file big.csv --only chunked
"""
from __future__ import annotations

import argparse
import time
import tracemalloc

import pandas as pd


def in_memory(path: str) -> pd.Series:
    """Load the whole file, then aggregate. Simple, but memory = file size."""
    df = pd.read_csv(path)
    return df.groupby("category")["value"].sum().sort_index()


def chunked(path: str, chunksize: int) -> pd.Series:
    """Stream the file in pieces; aggregate each; combine partial sums.

    Only one chunk lives in memory at a time. The list of partial results is
    tiny (one row per category per chunk), so peak memory stays ~chunk-sized
    no matter how large the file grows.
    """
    partials: list[pd.Series] = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        partials.append(chunk.groupby("category")["value"].sum())
    # Combine: concat the small partials, then sum per category.
    return pd.concat(partials).groupby(level=0).sum().sort_index()


def measure(label: str, fn, *args) -> pd.Series:
    """Run fn, reporting wall-clock time and PEAK memory it allocated."""
    tracemalloc.start()
    start = time.perf_counter()
    result = fn(*args)
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"  {label:10}  time: {elapsed:6.2f}s   peak memory: {peak_mb:8.1f} MB")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare in-memory vs chunked aggregation.")
    parser.add_argument("--file", default="sales.csv", help="input CSV (default: sales.csv)")
    parser.add_argument("--chunksize", type=int, default=500_000,
                        help="rows per chunk for the chunked approach (default: 500,000)")
    parser.add_argument("--only", choices=["in-memory", "chunked"],
                        help="run just one approach (e.g. in-memory on a huge file may OOM)")
    args = parser.parse_args()

    print(f"Aggregating '{args.file}' (sum of value per category)\n")

    results: dict[str, pd.Series] = {}
    if args.only in (None, "in-memory"):
        results["in-memory"] = measure("in-memory", in_memory, args.file)
    if args.only in (None, "chunked"):
        results["chunked"] = measure("chunked", chunked, args.file, args.chunksize)

    # Show the (identical) answer, and prove both agree when both ran.
    any_result = next(iter(results.values()))
    print("\nResult (totals by category):")
    for category, total in any_result.items():
        print(f"  {category:12} {total:14,.2f}")

    if len(results) == 2:
        same = results["in-memory"].round(2).equals(results["chunked"].round(2))
        print(f"\nBoth approaches agree: {same}")

    print(
        "\nLesson: chunked peak memory stays ~one-chunk-sized while in-memory "
        "peaks at ~whole-file-sized. Grow the file and the gap grows with it -- "
        "eventually in-memory can't fit at all. That's the wall big-data tools "
        "(Spark, BigQuery) exist to get past. See notes/301."
    )


if __name__ == "__main__":
    main()
