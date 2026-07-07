# File Formats: CSV, JSON/JSONL & Parquet

## Learning Objectives

- Describe CSV, JSON, JSON Lines (JSONL), and Parquet and what each stores well
- Explain row-based vs. columnar storage and why columnar wins for analytics
- Understand compression, embedded schema, and type preservation across formats
- Read and write all four from pandas (`to_csv/to_json/to_parquet`) and reason about size/speed trade-offs

## Why This Matters

The file format you pick silently controls **storage cost, query speed, and whether types survive a round-trip**. On a small CSV nobody cares — but at data-lake scale, choosing Parquet over CSV can cut storage by ~10x and speed up analytical reads by more. This week:

- **Today's demo `202-format-size-comparison/`** makes you *see* the size/speed gap.
- **Day 4 BigQuery** loves Parquet loads and stores columnar internally.
- **Day 5 ETL** writes Parquet as the intermediate/curated format.

You already met these formats as data *types* in note 202. This note is about how they land **on disk**.

## Concept Explanation

### Row-based vs. columnar — the core idea

This one picture explains most of the trade-offs.

```
Logical table:
  id | name  | salary
  ---+-------+-------
  1  | Ada   | 120000
  2  | Linus | 150000
  3  | Grace | 110000

ROW-BASED (CSV, JSON) stored on disk:
  1,Ada,120000 | 2,Linus,150000 | 3,Grace,110000
  ^-- values from the same ROW sit together

COLUMNAR (Parquet) stored on disk:
  [1,2,3] | [Ada,Linus,Grace] | [120000,150000,110000]
  ^-- values from the same COLUMN sit together
```

- **Row-based** is great when you read/write **whole records** (append a log line, stream a row). To compute `AVG(salary)` you must still read every other column too.
- **Columnar** is great for **analytics**: `AVG(salary)` reads *only* the salary column off disk (**column pruning**), and because a column holds one type of similar values, it **compresses dramatically** (run-length, dictionary encoding).

### CSV — Comma-Separated Values

Plain text, one row per line, row-based, universal.

```csv
id,name,salary,active
1,Ada,120000,true
2,Linus,150000,false
```

| Aspect | Value |
|--------|-------|
| Storage | text, row-based |
| Schema | header row only (names, no types) |
| Types | **everything is a string** — no type info |
| Compression | none built in |
| Human-readable | yes |

**Pros:** works everywhere, editable in any tool, dead simple.
**Cons:** no types (that `true` and `120000` are just text — pandas has to *guess* on read), no nesting, no built-in compression, biggest on disk.

> **Type loss is the real CSV trap.** Save a datetime or a boolean to CSV and read it back — you get a string, unless you tell `read_csv` how to parse it (`parse_dates=`, `dtype=`).

### JSON — JavaScript Object Notation

Self-describing, supports nesting, row-based, web-native.

```json
[
  {"id": 1, "name": "Ada",   "active": true},
  {"id": 2, "name": "Linus", "active": false}
]
```

**Pros:** carries basic types (number/bool/null), represents nested/hierarchical data, native to APIs.
**Cons:** **verbose** — every key is repeated on every record, so it's usually *bigger* than CSV; the whole array must be parsed at once; slow for analytics.

### JSON Lines (JSONL / NDJSON)

One JSON object **per line** — no enclosing array, no commas between records.

```
{"id": 1, "name": "Ada",   "active": true}
{"id": 2, "name": "Linus", "active": false}
```

**Why it exists:** you can read/append/stream **one record at a time** without loading the whole file, and split it across workers by line. It's the standard for logs, streaming ingestion, and big data exports (BigQuery exports JSONL, not JSON arrays).

```python
df.to_json("data.jsonl", orient="records", lines=True)
pd.read_json("data.jsonl", lines=True)
```

### Parquet — columnar, binary, analytics-first

The default format for data lakes and analytics engines. Binary, columnar, with **schema and types embedded** and **compression built in**.

```
Parquet file layout:
+-------------------------------+
| Row Group 1                   |
|  ┌───────────┐                |
|  | Column id | (compressed)   |  <- each column stored & compressed separately
|  | Column nm | (compressed)   |
|  | Column sal| (compressed)   |
|  └───────────┘                |
+-------------------------------+
| Row Group 2 ...               |
+-------------------------------+
| Footer: schema + statistics   |  <- min/max per column enable predicate pushdown
+-------------------------------+
```

| Aspect | Value |
|--------|-------|
| Storage | binary, columnar |
| Schema | **embedded**, with real types |
| Types | rich (int, float, bool, timestamp, nested) — **preserved on round-trip** |
| Compression | built in (Snappy default; also gzip, zstd) |
| Human-readable | no (needs a library/tool) |

**Pros:** ~5-10x smaller than CSV, fast analytical reads, column pruning, types survive, footer stats let engines skip row groups (**predicate pushdown**).
**Cons:** not human-readable, needs a library (`pyarrow`), overhead makes it a poor fit for tiny files or single-row appends.

> Reading Parquet in pandas requires the **`pyarrow`** engine: `pip install pyarrow`.

### Format comparison

| Feature | CSV | JSON | JSONL | Parquet |
|---------|-----|------|-------|---------|
| Layout | row | row | row | **columnar** |
| Human-readable | yes | yes | yes | no |
| Types preserved | no | partial | partial | **yes** |
| Nested data | no | yes | yes | yes |
| Built-in compression | no | no | no | **yes** |
| Column pruning | no | no | no | **yes** |
| Stream one record | no* | no | **yes** | no |
| Relative size (typical) | 1x | 1.5-2x | ~1.5x | **0.1-0.3x** |
| Best for | interchange, humans | APIs, configs | logs, streaming, exports | analytics, data lakes |

\* CSV can be read in chunks (`chunksize=`), but a single record isn't self-contained the way a JSONL line is.

### Reading & writing from pandas

```python
# --- write ---
df.to_csv("out.csv", index=False)                       # index=False -> don't dump the row numbers
df.to_json("out.json", orient="records", indent=2)      # pretty JSON array
df.to_json("out.jsonl", orient="records", lines=True)   # JSON Lines
df.to_parquet("out.parquet", compression="snappy")      # needs pyarrow

# --- read ---
pd.read_csv("out.csv", parse_dates=["hire_date"])       # help CSV recover types
pd.read_json("out.json")
pd.read_json("out.jsonl", lines=True)
pd.read_parquet("out.parquet")                          # types come back intact
pd.read_parquet("out.parquet", columns=["id", "salary"])# column pruning: reads only these
```

> **`orient="records"`** is the shape you'll use most — a list of `{column: value}` objects, one per row. It's also exactly the shape a JSON API returns (note 204).

## Code Example

Write the same DataFrame four ways and compare size + write time. This is the seed of demo `202-format-size-comparison/`.

```python
import pandas as pd, numpy as np, os, time

# ~100k rows — big enough to see the gap, fast enough to run in seconds
n = 100_000
rng = np.random.default_rng(42)
df = pd.DataFrame({
    "id": np.arange(n),
    "name": [f"user_{i}" for i in range(n)],
    "dept": rng.choice(["Web", "Kernel", "Data", "Ops"], n),
    "salary": rng.uniform(30_000, 150_000, n).round(2),
    "active": rng.choice([True, False], n),
})

os.makedirs("out", exist_ok=True)   # never assume the dir exists

def timed_write(label, path, fn):
    t = time.perf_counter()
    fn(path)
    secs = time.perf_counter() - t
    mb = os.path.getsize(path) / 1024 / 1024
    print(f"{label:<8} {mb:7.2f} MB   {secs:6.3f} s")

print(f"{'format':<8} {'size':>7}      {'write':>6}")
timed_write("CSV",     "out/d.csv",     lambda p: df.to_csv(p, index=False))
timed_write("JSONL",   "out/d.jsonl",   lambda p: df.to_json(p, orient="records", lines=True))
timed_write("Parquet", "out/d.parquet", lambda p: df.to_parquet(p, compression="snappy"))

# Typical result: Parquet is the smallest file AND competitive/fastest to write,
# while CSV/JSONL are several times larger. The gap widens with more rows.
```

## Key Takeaways

- **Row-based (CSV/JSON/JSONL)** suits whole-record reads and streaming; **columnar (Parquet)** suits analytics.
- **CSV**: universal + human-readable, but no types and biggest on disk.
- **JSON**: self-describing and nestable, but verbose; **JSONL** fixes streaming/append by putting one object per line.
- **Parquet**: smallest, fastest for analytics, embeds schema + types, compresses automatically — the go-to for data lakes and BigQuery loads. Needs `pyarrow`.
- From pandas it's one call each: `to_csv` / `to_json` / `to_parquet`, and the matching `read_*`.
- Use **`orient="records"`** for the list-of-objects shape shared by JSONL and JSON APIs.
- **Parquet preserves types on round-trip; CSV loses them** — a constant source of bugs.

## Resources

- Apache Parquet: <https://parquet.apache.org/>
- pandas I/O reference: <https://pandas.pydata.org/docs/reference/io.html>
- JSON Lines spec: <https://jsonlines.org/>
- Understanding columnar storage: <https://parquet.apache.org/docs/file-format/>
- Cross-reference: `demos/202-format-size-comparison/` and `exercises/202-file-format-benchmark.md`
