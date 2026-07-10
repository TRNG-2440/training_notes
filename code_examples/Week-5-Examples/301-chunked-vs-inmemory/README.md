# Demo 301 — Chunked vs In-Memory Aggregation

**What it shows:** the "too big for memory" problem and its first real fix, on a single machine. We generate a largish CSV, then compute the same aggregation two ways and compare **peak memory** and **timing**:

- **In-memory** — `pd.read_csv()` loads the *entire* file, then `groupby`. Peak memory ≈ whole-file size.
- **Chunked** — `pd.read_csv(chunksize=...)` streams the file in pieces, aggregates each piece, and combines the tiny partial results. Peak memory ≈ *one chunk*.

This makes the **Volume** (and, by extension, **Velocity**) concepts from
[`notes/301-big-data-fundamentals.md`](../../notes/301-big-data-fundamentals.md)
concrete. Chunking is the stepping stone from "pandas on one box" to distributed
engines (Spark) and serverless warehouses (BigQuery, Day 4): the moment data no
longer fits in RAM, you stop loading it all at once.

## The lesson in one sentence
Both approaches return the **identical answer** — the difference is that in-memory
peaks at the size of the whole dataset while chunked stays flat at one chunk, so
as the file grows the chunked approach keeps working long after in-memory would
run out of RAM.

## Setup

```bash
cd 2440-W5/demos/301-chunked-vs-inmemory
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
# 1) Create the data (~5M rows, ~150-200 MB, a few seconds).
python generate_data.py

# 2) Aggregate both ways and compare.
python aggregate.py
```

Example output (numbers vary by machine):

```
Aggregating 'sales.csv' (sum of value per category)

  in-memory   time:   1.85s   peak memory:    612.4 MB
  chunked     time:   1.79s   peak memory:     70.2 MB

Result (totals by category):
  automotive    125,314,880.50
  ...

Both approaches agree: True
```

Note the peak-memory gap: in-memory holds the whole DataFrame; chunked holds
only one chunk plus a handful of small partial sums.

## Try this
- **Shrink the chunk:** `python aggregate.py --chunksize 100000` — peak memory
  drops further (with a slight time cost from more iterations).
- **Grow the file:** `python generate_data.py --rows 20000000` then run again.
  The in-memory peak balloons while chunked stays roughly flat.
- **Make in-memory fail:** on a low-RAM machine, generate a very large file and
  run `python aggregate.py --only chunked` — the chunked path still finishes
  when a full load would not. That is the whole point of big-data tooling.

## Files
- `generate_data.py` — writes a fake sales CSV (stdlib only; streams as it writes).
- `aggregate.py` — runs both approaches, measures peak memory (`tracemalloc`) + time.
- `requirements.txt` — just pandas.

## Follow-Along Build Walkthrough

This section is for instructors who want to build the demo live, from an empty
folder, while associates follow along. It assumes solid Python and SQL but only
minimal pandas, so every pandas call is explained. Type each snippet exactly as
shown — the finished files in this folder match it line for line.

### 1. Intro — what we're building and why

We are going to build two small scripts:

1. `generate_data.py` — creates a "largish" CSV of fake sales, big enough that
   loading the whole thing at once is noticeably heavy.
2. `aggregate.py` — answers one simple question, *"what is the total sales value
   per category?"*, two different ways and compares them:
   - **In-memory:** load the entire file into a pandas DataFrame, then group and
     sum.
   - **Chunked:** read the file in pieces with `pd.read_csv(chunksize=...)`,
     aggregate each piece, and combine the small partial results at the end.

Both approaches return the **identical answer**. The goal of the demo is to show
that they differ dramatically in **peak memory**: the in-memory approach peaks at
roughly the size of the whole file, while the chunked approach peaks at roughly
the size of a single chunk. That is the concrete, on-a-laptop version of the
big-data **Volume** problem ("the data is too big for RAM") and its first real
fix. We measure peak memory with `tracemalloc` and wall-clock time with
`time.perf_counter()` so associates can see the trade-off with their own eyes.

### 2. Step-by-step assembly

#### Step 2.1 — `generate_data.py`: make a file too big to ignore

We can't demonstrate a Volume problem without volume. Rather than download a
dataset, we synthesize one. Start with the module docstring and imports:

```python
"""Generate a largish CSV of fake sales so we can demonstrate the
'too big for a naive approach' problem without downloading anything.
...
"""
from __future__ import annotations

import argparse
import csv
import os
import random
```

We deliberately use only the standard library here — `csv` for writing rows,
`random` for the fake data, `os` to check the file size, `argparse` for
command-line flags. No pandas yet; generation should not need it.

Next, define the set of categories we'll bucket sales into. Ten categories keeps
the final aggregated result small and readable:

```python
CATEGORIES = [
    "electronics", "grocery", "clothing", "toys", "books",
    "home", "sports", "beauty", "automotive", "garden",
]
```

Now the core function. This is the important part — notice it **streams** rows to
disk instead of building a giant list first:

```python
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
```

What each piece does and why:

- `random.seed(seed)` makes the data **reproducible** — every run produces the
  same file, so the aggregated totals are stable across the class.
- `csv.writer(f)` plus `writer.writerow(...)` writes one line at a time. We write
  the header first, then loop. Because we write inside the loop and never keep a
  list of all rows, memory used by generation stays tiny no matter how many rows
  we ask for. This is the same discipline the chunked reader will use — we
  practice what we preach.
- `random.choice(CATEGORIES)` and `random.uniform(1.0, 500.0)` invent a category
  and a dollar value per order; `round(..., 2)` gives cents.
- `os.path.getsize(path)` reports how big the file actually got, converted to MB,
  so associates can *see* the Volume they just created.

How this shows Volume/Velocity: the `--rows` knob (added next) lets us dial the
file size up until the naive approach struggles. Generating 5 million rows in a
steady stream, one row at a time, is itself a small taste of **Velocity** — a
continuous flow of records rather than one big blob.

Finally the CLI wrapper so the row count and output path are adjustable:

```python
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
```

The default of 5,000,000 rows (~150-200 MB) is chosen to finish in a few seconds
yet be clearly heavier in-memory than chunked. `if __name__ == "__main__"` means
the file can be imported without running, but runs `main()` when executed
directly.

#### Step 2.2 — `aggregate.py`: the same answer, two ways

Now the payoff script. Start with the docstring (which doubles as a teaching aid)
and imports:

```python
"""Aggregate a big CSV two ways and compare peak memory + timing.
...
"""
from __future__ import annotations

import argparse
import time
import tracemalloc

import pandas as pd
```

The two new imports to call out: `tracemalloc` is Python's built-in memory
profiler — it tracks how much memory your Python allocations use and, crucially,
the **peak** during a window. `time` gives us wall-clock timing. `pandas as pd`
is our data tool.

**The in-memory approach.** This is what most people write first, and it is
perfectly correct:

```python
def in_memory(path: str) -> pd.Series:
    """Load the whole file, then aggregate. Simple, but memory = file size."""
    df = pd.read_csv(path)
    return df.groupby("category")["value"].sum().sort_index()
```

Line by line for the pandas-light audience:

- `pd.read_csv(path)` reads the **entire** CSV into a DataFrame `df` (an in-memory
  table). This is the expensive line — every row now lives in RAM at once.
- `df.groupby("category")` buckets rows by their `category` value (like SQL
  `GROUP BY category`).
- `["value"].sum()` selects the `value` column within each bucket and sums
  it — the SQL equivalent of `SELECT category, SUM(value) ... GROUP BY category`.
- `.sort_index()` orders the result alphabetically by category so it's easy to
  compare against the other approach.

The return type is a pandas `Series`: an indexed one-column result, here indexed
by category with the summed value as data.

How this shows Volume: peak memory for this function is roughly the size of the
whole DataFrame. Double the file, double the peak. Eventually it won't fit — that
is the wall.

**The chunked approach.** Same answer, but it never holds the whole file:

```python
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
```

The key difference is the `chunksize` argument:

- `pd.read_csv(path, chunksize=chunksize)` does **not** return a DataFrame. It
  returns an **iterator**. Each time the `for` loop turns, pandas reads just the
  next `chunksize` rows (default 500,000) into a small DataFrame called `chunk`,
  and only that one chunk is in memory at a time.
- For each chunk we run the *same* `groupby("category")["value"].sum()` as before,
  producing a tiny partial Series (at most ten rows — one per category). We append
  it to `partials`. The list of partials is small even for a huge file.
- After the loop, `pd.concat(partials)` stacks all the partial Series into one
  long Series. Because each chunk contributed its own "electronics" total,
  "grocery" total, etc., the same category appears many times. So we run
  `.groupby(level=0).sum()` — group by the **index** (`level=0` is the category
  index) and sum, collapsing the repeats into one final total per category.
  `.sort_index()` again for a comparable order.

The critical teaching point is that **summing is associative**: the sum of the
whole equals the sum of the partial sums. That is exactly why aggregation is
"chunkable" — we can compute pieces independently and combine them cheaply.

How this shows Volume/Velocity: only one chunk is resident at any moment, so peak
memory is ~chunk-sized regardless of file size. This is streaming — process a
window of data as it flows past, discard it, move on — the mental model behind
real streaming and distributed systems.

**Measuring memory and time.** We wrap either function in a small harness so both
are measured identically:

```python
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
```

- `tracemalloc.start()` begins tracking allocations; `tracemalloc.get_traced_memory()`
  returns `(current, peak)` — we care about **peak**, the high-water mark reached
  while `fn` ran. `tracemalloc.stop()` turns tracking off.
- `time.perf_counter()` before and after gives elapsed wall-clock seconds.
- `fn` and `*args` make this generic: we pass in either `in_memory` or `chunked`
  plus their arguments, and get back the result Series while the timing/memory
  line is printed. This guarantees a fair, apples-to-apples comparison.

**Wiring it together in `main()`:**

```python
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
```

Points to highlight:

- `--only` lets you skip the in-memory run on files so large it would run out of
  memory — proving the chunked path finishes when the naive one cannot.
- We store results in a dict so we can print the answer once and, when both ran,
  verify agreement with `results["in-memory"].round(2).equals(results["chunked"].round(2))`.
  We round to 2 decimals first because floating-point sums added in a different
  order can differ in the last bit; rounding to cents makes the comparison honest.
- The final `print` restates the lesson so it's on screen after the numbers.

### 3. How it fits together

There are two aggregation paths that produce the same `pd.Series`:

```
                        generate_data.py  -->  sales.csv (big)
                                                   |
                        +--------------------------+--------------------------+
                        |                                                     |
                  in_memory(path)                                    chunked(path, chunksize)
              read_csv() whole file                         read_csv(chunksize=) one piece at a time
              one big groupby().sum()                       groupby().sum() per chunk -> partials
                        |                                   concat(partials).groupby(level=0).sum()
                        |                                                     |
                        +----------------- both wrapped by measure() ---------+
                              tracemalloc peak + perf_counter time
                                          |
                            print totals; verify both agree
```

`measure()` is the neutral judge: it calls each function inside its own
`tracemalloc` window and reports the **peak** allocation. Because both functions
are measured the exact same way, the printed peak-memory numbers are directly
comparable — the whole demo hinges on that side-by-side pair of numbers.

### 4. Demo Notes (instructor)

**What to run**, in order:

```bash
python generate_data.py          # once, creates sales.csv (~5M rows)
python aggregate.py              # runs both approaches and compares
```

Optional variations to run live:

```bash
python aggregate.py --chunksize 100000     # smaller chunks -> lower peak, a bit slower
python generate_data.py --rows 20000000    # bigger file -> watch in-memory peak balloon
python aggregate.py --only chunked         # the path that survives when in-memory can't
```

**Expected output** (numbers vary by machine, but the *shape* is the point):

```
Aggregating 'sales.csv' (sum of value per category)

  in-memory   time:   1.85s   peak memory:    612.4 MB
  chunked     time:   1.79s   peak memory:     70.2 MB

Result (totals by category):
  automotive    125,314,880.50
  ...

Both approaches agree: True
```

The two takeaways to point at on screen: (1) the chunked **peak memory** is a
fraction of in-memory, and (2) `Both approaches agree: True` — same answer,
smaller footprint.

**Gotchas to preempt:**

- *Combining partial aggregates correctly.* The most common mistake associates
  make is aggregating each chunk but then just concatenating the partials and
  calling it done — that leaves duplicate rows (one "grocery" total per chunk).
  You must re-aggregate: `pd.concat(partials).groupby(level=0).sum()`. Stress that
  this only works because sum is associative. If someone tries to compute an
  *average* this way, a naive mean-of-means is wrong — you'd need to carry sum and
  count per chunk and divide at the end. Good discussion hook.
- *Row count vs runtime.* Time scales with total rows regardless of approach — you
  still have to read every byte. Chunking saves **memory, not time** (it can even
  be slightly slower due to more iterations and repeated `concat`/`groupby`
  overhead). Set expectations: the two time numbers will be close; it's the memory
  numbers that diverge.
- *Peak memory is Python-allocation memory.* `tracemalloc` tracks Python-side
  allocations; the absolute MB may not match your OS task manager exactly. The
  *ratio* between the two runs is the honest, comparable signal.
- *Floating-point comparison.* We `.round(2)` before `.equals()` because summing
  in a different order can differ in the last bit. Without rounding,
  `Both approaches agree` could occasionally print `False` for a correct program.

### 5. Discussion Topics

Prompts to run with the class after the demo:

1. **When chunking isn't enough.** Chunking keeps one machine alive longer, but a
   single laptop still reads the whole file serially. At what data size do you
   reach for a **distributed** engine (Spark) or a **serverless warehouse**
   (BigQuery) instead? What do those give you that a `for` loop over chunks
   cannot? (Hint: many machines reading many chunks in parallel.)
2. **Streaming vs batch.** Our chunked loop is really *batch* processing of a
   file that already exists. How would this change if rows were arriving
   continuously (Velocity) — a live event stream? What breaks, and what stays the
   same about the "aggregate a window, combine, discard" pattern?
3. **Memory vs speed trade-off.** Shrinking `--chunksize` lowers peak memory but
   adds iterations. Where's the sweet spot? Is there ever a reason to make chunks
   *bigger*? How would you pick a chunk size for a machine you don't control?
4. **Why is aggregation chunkable but sorting and joins are harder?** Sum, count,
   min, and max combine trivially across chunks because they're associative. What
   goes wrong if you try to fully **sort** a file one chunk at a time, or **join**
   two big files chunk by chunk? (You'd need to see data from other chunks — this
   is exactly why distributed engines do expensive "shuffles.")
5. **Correctness of combined aggregates.** Sum and count are safe to combine as
   sum-of-partials. Which common aggregates are *not* safe done naively (average,
   median, distinct count)? For each, what would you have to carry per chunk to get
   the right final answer?
6. **From this demo to the real tools.** Map each piece of our script onto its
   big-data equivalent: our chunk ↔ a Spark partition, our per-chunk `groupby` ↔ a
   map/partial-aggregate stage, our final `concat().groupby().sum()` ↔ the reduce
   stage. What is the engine doing for you that you hand-wrote here?
