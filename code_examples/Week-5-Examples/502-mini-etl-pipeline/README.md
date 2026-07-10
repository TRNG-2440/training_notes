# Demo 502 — Mini ETL pipeline (Week 5 capstone demo)

> Day 5 · pairs with `notes/505` and `notes/506`; sets up `exercises/502-capstone-etl-pipeline.md`

This is the demo that ties the **whole week** together. It is a small, self-contained **E → T → L** pipeline that walks through each stage and shows how the week's skills compose.

## What it shows, stage by stage

| Stage | What happens | Week skill |
|-------|--------------|------------|
| **E — Extract** | Pull JSON from a public API with `httpx`; fall back to `sample_data.json` if offline | **Day 1** (HTTP client) |
| **T — Transform** | Clean & reshape with pandas — drop duplicates/nulls, trim/standardize text, derive `title_length` and an `activity_date`, then run data-quality checks | **Day 2** (pandas) + Note 506 |
| **L — Load** | Land into a **DuckDB** warehouse modeled as a simple **star schema** (`fact_task` + `dim_user` + `dim_date`) | **Day 4** (warehouse) + **Day 5** (dimensional model) |
| **Report** | Run analytical SQL over the star (completion rate by user; weekday vs. weekend) | **Day 4/5** (analytics) |

The source data (`sample_data.json`) deliberately contains a **duplicate row** and a **null title** so you can see the cleaning and quality gate actually do something.

## The star it builds

```
        +-----------+                +-----------+
        | dim_user  |                | dim_date  |
        +-----+-----+                +-----+-----+
              |  user_key      date_key  |
              +----------> fact_task <---+
                          (grain: one row per task)
                          measures: is_completed, title_length
```

## Run it

```bash
cd 2440-W5/demos/502-mini-etl-pipeline

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python etl_pipeline.py            # tries the live API, auto-falls back if offline
python etl_pipeline.py --offline  # force the shipped sample (no network)
```

It writes `warehouse.duckdb` next to the script (recreated each run — the load is idempotent). Inspect it directly:

```bash
duckdb warehouse.duckdb "SELECT * FROM fact_task LIMIT 5;"
```

## Expected output (offline, abridged)

```
--- E: EXTRACT ---
[extract] loaded 23 records from sample_data.json
--- T: TRANSFORM ---
[transform] cleaned 23 -> 21 rows (2 dropped as dup/null/blank)
[quality] passed: 21 rows, 6 users, 21 distinct dates
--- L: LOAD (star schema in DuckDB) ---
[load] star built: fact_task=21 rows, dim_user=6, dim_date=21

=== Analytical report: task completion by user ===
 user_label  total_tasks  completed_tasks  pct_complete  avg_title_len
     User 1            6              2.0          33.3           19.7
     ...
```

(With a live connection, the public API returns 200 clean records instead of 23.)

## How this maps to the BigQuery world (Day 4)

| Demo (DuckDB) | BigQuery equivalent |
|---------------|---------------------|
| `duckdb.connect("warehouse.duckdb")` | a BigQuery dataset |
| `CREATE OR REPLACE TABLE ... AS SELECT` | same DDL, `mydataset.` prefix |
| `con.register("staged", df)` | `client.load_table_from_dataframe(df, "mydataset.staged")` |
| `strftime(..., '%Y%m%d')` | `FORMAT_DATE('%Y%m%d', ...)` |

## Where to go from here

This demo is the **skeleton of the capstone exercise** (`exercises/502-capstone-etl-pipeline.md`), which extends it with an **SCD Type 2 dimension** (see Demo 501) and a **FastAPI endpoint** (Day 1) serving the analytical result.

## Files

| File | Purpose |
|------|---------|
| `etl_pipeline.py` | The full E→T→L pipeline + report |
| `sample_data.json` | Offline fallback source (with intentional dirty rows) |
| `requirements.txt` | `duckdb`, `pandas`, `httpx`, `pyarrow` |

## Follow-Along Build Walkthrough

### 1. Intro — what we're building and why

This is the **week capstone**. Over the week the associates learned four separate tools; today we wire them together into one working data pipeline so they can see *why* each one exists. We are going to build a **mini ETL** — Extract, Transform, Load — in a single file, `etl_pipeline.py`, and then run an analytical query over the result.

The data flow is one straight line:

```
public API (or sample_data.json)  ->  extract()  ->  raw list[dict]
raw list[dict]                     ->  transform() ->  clean pandas DataFrame
clean DataFrame                    ->  load()      ->  DuckDB star schema
DuckDB star schema                 ->  report()    ->  analytical answers
```

Each stage is one function, and each function hands its output to the next. As we build, notice where each day's skill shows up:

- **Day 1 (httpx / HTTP clients)** — the Extract stage pulls JSON over HTTP.
- **Day 2 (pandas)** — the Transform stage cleans and reshapes.
- **Day 4 (DuckDB warehouse)** — the Load stage creates and populates tables.
- **Day 5 (dimensional modeling)** — the tables aren't flat; they're a **star schema** (`fact_task` + `dim_user` + `dim_date`), and we query it like a warehouse analyst would.

The goal by the end: run one command and watch data travel from a live API all the way to a completion-rate report, with a data-quality gate that refuses to publish bad data.

### 2. Step-by-step assembly

We build the file top-down: imports and config first, then E, then T, then L, then the query, then a `main()` that runs them in order.

#### Step 0 — Imports and configuration constants

Start with the module docstring and the constants that everything else references. Do this first so the stage functions have names to point at.

```python
from __future__ import annotations
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).parent
API_URL = "https://jsonplaceholder.typicode.com/todos"   # public, no auth
SAMPLE = HERE / "sample_data.json"
WAREHOUSE = HERE / "warehouse.duckdb"
```

`API_URL` is a free public endpoint (no key needed). `SAMPLE` is our offline fallback, and `WAREHOUSE` is the DuckDB file we'll write next to the script. Everything is anchored to `HERE` so the demo runs from any directory.

#### Step 1 — EXTRACT (Day 1: httpx) → raw `list[dict]`

The Extract stage's only job is to *get the raw records*. It doesn't clean anything. Type them: they come out as a `list[dict]`.

```python
def extract(offline: bool = False) -> list[dict]:
    """Pull JSON from the API with httpx; fall back to the shipped sample."""
    if not offline:
        try:
            import httpx
            print(f"[extract] GET {API_URL}")
            resp = httpx.get(API_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            print(f"[extract] pulled {len(data)} records from API")
            return data
        except Exception as e:  # network down, timeout, DNS, etc.
            print(f"[extract] API unavailable ({type(e).__name__}: {e}); "
                  f"falling back to sample file")

    data = json.loads(SAMPLE.read_text())
    print(f"[extract] loaded {len(data)} records from {SAMPLE.name}")
    return data
```

What it does and why:

- **The httpx call** (`httpx.get(...).raise_for_status().json()`) is the Day 1 skill. `raise_for_status()` turns a 4xx/5xx into an exception so we don't silently process an error page.
- **The offline fallback** is the teaching point. Real pipelines run against flaky networks. If `--offline` is passed *or* the API throws *any* exception (DNS, timeout, 500), we fall through to reading `sample_data.json` from disk. Same shape either way, so the rest of the pipeline can't tell the difference.

**Handoff:** `extract()` returns raw, uncleaned records. It knows nothing about pandas or DuckDB. That output becomes the input to `transform()`.

#### Step 2 — TRANSFORM (Day 2: pandas) → clean DataFrame

Now we clean and reshape. This is where the dirty data in `sample_data.json` matters: it intentionally contains a **duplicate row** (`id: 63` appears twice) and a **null title** (`id: 101`), plus a title padded with whitespace (`id: 44`, `"  cupiditate quo est   "`). Transform must handle all three.

```python
def transform(records: list[dict]) -> pd.DataFrame:
    """Clean & reshape with pandas, then derive dimensional attributes."""
    df = pd.DataFrame(records)

    # Cleaning ---------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["id"])                 # remove dup task ids
    df["title"] = df["title"].astype("string").str.strip() # trim whitespace
    df = df.dropna(subset=["title"])                       # drop rows w/o a title
    df = df[df["title"] != ""]
    print(f"[transform] cleaned {before} -> {len(df)} rows "
          f"({before - len(df)} dropped as dup/null/blank)")

    # Standardization + derivation ------------------------------------------
    df = df.rename(columns={"id": "task_id", "userId": "user_id"})
    df["completed"] = df["completed"].astype(bool)
    # Derive a synthetic load/activity date so we can join a real date dimension.
    # (The demo API has no timestamps; assign deterministic recent dates.)
    base = date.today() - timedelta(days=30)
    df = df.reset_index(drop=True)
    df["activity_date"] = [base + timedelta(days=int(i) % 30) for i in df.index]
    df["title_length"] = df["title"].str.len().astype(int)   # derived measure

    return df[["task_id", "user_id", "activity_date",
               "completed", "title", "title_length"]]
```

Walk it in two passes:

- **Cleaning.** Load the list into a DataFrame, then: `drop_duplicates(subset=["id"])` removes the duplicate `id: 63`; `str.strip()` trims the padded title; `dropna(subset=["title"])` removes the `null` title (`id: 101`); the last filter drops any title that became empty after trimming. The print line reports `before -> after` so associates *see* rows disappear.
- **Standardization + derivation.** Rename `id`/`userId` to warehouse-friendly `task_id`/`user_id`, coerce `completed` to a real bool, and derive two new columns. `activity_date` is synthetic (this API has no timestamps) but deterministic, so we have something to join a **date dimension** to. `title_length` is a **derived measure** we'll aggregate later. We return only the columns we need, in a fixed order.

**Handoff:** `transform()` returns a tidy DataFrame with exactly the columns the star schema expects. It's still just in-memory pandas — nothing is persisted yet.

#### Step 2b — The quality gate (Note 506)

Before we let anything reach the warehouse, we assert the data is fit to publish. This is a separate function on purpose: cleaning and *verifying the clean worked* are different jobs.

```python
def quality_gate(df: pd.DataFrame) -> None:
    """Minimal data-quality checks (Note 506). Raise to stop before publish."""
    problems = []
    if df["task_id"].duplicated().any():
        problems.append("duplicate task_id")
    if df["task_id"].isnull().any():
        problems.append("null task_id")
    if df["title"].isnull().any() or (df["title"] == "").any():
        problems.append("empty title")
    if problems:
        raise ValueError(f"[quality] FAILED: {problems}")
    print(f"[quality] passed: {len(df)} rows, "
          f"{df['user_id'].nunique()} users, "
          f"{df['activity_date'].nunique()} distinct dates")
```

If any check fails it **raises**, stopping the run *before* the load — better to fail loudly than to publish bad numbers. On success it prints a one-line summary (row count, distinct users, distinct dates). This is the Day/Note-506 data-quality skill in miniature.

#### Step 3 — LOAD (Day 4 warehouse + Day 5 star schema) → DuckDB

Now persist the clean frame into DuckDB, shaped as a **star**: two dimension tables plus one fact table.

```python
def load(df: pd.DataFrame, con: duckdb.DuckDBPyConnection) -> None:
    """Build a simple star: dim_user + dim_date + fact_task."""
    con.register("staged", df)

    # dim_date — the conformed date dimension (Note 503)
    con.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        SELECT DISTINCT
            CAST(strftime(activity_date, '%Y%m%d') AS INTEGER) AS date_key,
            activity_date                                       AS full_date,
            EXTRACT(year  FROM activity_date)                   AS year,
            EXTRACT(month FROM activity_date)                   AS month,
            strftime(activity_date, '%A')                       AS day_name,
            (EXTRACT(dow FROM activity_date) IN (0, 6))         AS is_weekend
        FROM staged;
    """)

    # dim_user — one row per user (surrogate = user_id here for simplicity)
    con.execute("""
        CREATE OR REPLACE TABLE dim_user AS
        SELECT DISTINCT
            user_id                       AS user_key,
            'U' || CAST(user_id AS VARCHAR) AS user_natural_id,
            'User ' || CAST(user_id AS VARCHAR) AS user_label
        FROM staged;
    """)

    # fact_task — grain: one row per task; FKs to dims + measures
    con.execute("""
        CREATE OR REPLACE TABLE fact_task AS
        SELECT
            s.task_id,                                                    -- degenerate dim
            CAST(strftime(s.activity_date, '%Y%m%d') AS INTEGER) AS date_key,
            s.user_id                                            AS user_key,
            CAST(s.completed AS INTEGER)                         AS is_completed, -- additive
            s.title_length                                       AS title_length  -- additive
        FROM staged s;
    """)

    n = con.execute("SELECT COUNT(*) FROM fact_task").fetchone()[0]
    print(f"[load] star built: fact_task={n} rows, "
          f"dim_user={con.execute('SELECT COUNT(*) FROM dim_user').fetchone()[0]}, "
          f"dim_date={con.execute('SELECT COUNT(*) FROM dim_date').fetchone()[0]}")
```

What it does and why:

- **`con.register("staged", df)`** hands the pandas DataFrame straight to DuckDB as a queryable view named `staged`. No CSV round-trip — DuckDB reads the DataFrame in place. (In BigQuery this is `load_table_from_dataframe`; see the mapping table above.)
- **`dim_date`** is the conformed date dimension (Note 503): one row per distinct date, with an integer `date_key`, plus derived `year`/`month`/`day_name`/`is_weekend` attributes so analysts can slice by calendar without date math.
- **`dim_user`** is one row per user, with a surrogate `user_key` and human-readable `user_label`.
- **`fact_task`** is the center of the star. Its **grain is one row per task**. It holds foreign keys (`date_key`, `user_key`), a **degenerate dimension** (`task_id` lives on the fact), and two **additive measures** (`is_completed`, `title_length`) we can `SUM`/`AVG`.
- `CREATE OR REPLACE` means re-running rebuilds the tables cleanly.

**Handoff:** after `load()`, the warehouse *is* the state. Downstream code queries DuckDB, not pandas.

#### Step 4 — The analytical query over the star

The payoff: SQL that joins the fact to the dimensions — exactly what the star was built for.

```python
def report(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Analytical report: task completion by user ===")
    df = con.execute("""
        SELECT
            u.user_label,
            COUNT(*)                        AS total_tasks,
            SUM(f.is_completed)             AS completed_tasks,
            ROUND(100.0 * SUM(f.is_completed) / COUNT(*), 1) AS pct_complete,
            ROUND(AVG(f.title_length), 1)   AS avg_title_len
        FROM fact_task f
        JOIN dim_user u ON f.user_key = u.user_key
        GROUP BY u.user_label
        ORDER BY completed_tasks DESC, u.user_label
    """).fetchdf()
    print(df.to_string(index=False))

    print("\n=== Completion by weekend vs. weekday (uses dim_date) ===")
    df2 = con.execute("""
        SELECT
            CASE WHEN d.is_weekend THEN 'weekend' ELSE 'weekday' END AS day_type,
            COUNT(*)            AS tasks,
            SUM(f.is_completed) AS completed
        FROM fact_task f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY day_type
        ORDER BY day_type
    """).fetchdf()
    print(df2.to_string(index=False))
```

The first query joins `fact_task` to `dim_user` to get completion rate and average title length **per user**. The second joins to `dim_date` to compare **weekday vs. weekend** completion. Both follow the same fact→dimension join pattern — this is what dimensional modeling buys you: simple, fast, obvious aggregations.

#### Step 5 — `main()` wires the stages in order

Finally, an orchestrator that runs E → T → gate → L → report, in sequence.

```python
def main() -> None:
    ap = argparse.ArgumentParser(description="Mini E->T->L pipeline (Day 5 capstone demo)")
    ap.add_argument("--offline", action="store_true",
                    help="skip the API and use the shipped sample file")
    args = ap.parse_args()

    print("--- E: EXTRACT ---")
    records = extract(offline=args.offline)

    print("\n--- T: TRANSFORM ---")
    df = transform(records)
    quality_gate(df)

    print("\n--- L: LOAD (star schema in DuckDB) ---")
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()                 # idempotent: fresh warehouse each run
    con = duckdb.connect(str(WAREHOUSE))
    load(df, con)

    report(con)
    con.close()
    print(f"\nDone. Warehouse written to {WAREHOUSE.name}. "
          f"Open it: duckdb {WAREHOUSE.name}")
```

Note the `WAREHOUSE.unlink()` before connecting: we delete and rebuild the warehouse every run, which makes the pipeline **idempotent** — run it ten times, get the same result. That's a full-load pattern (more on that in Discussion).

### 3. How it fits together — the E→T→L data flow

Trace one record end to end:

1. **Extract** hits `API_URL` with httpx (or reads `sample_data.json` offline) and returns a raw `list[dict]` — no cleaning, just "get the bytes."
2. That list flows into **Transform**, which builds a DataFrame, drops the duplicate/null/blank rows, standardizes column names and types, and derives `activity_date` + `title_length`. Output: a clean, warehouse-shaped DataFrame.
3. The DataFrame passes through the **quality gate**. If it's dirty, we raise and stop *before* touching the warehouse.
4. **Load** registers that frame as `staged` and builds the DuckDB star: `dim_date`, `dim_user`, and `fact_task`. Now the warehouse holds the state.
5. **Report** runs analytical SQL over the star and prints the answers.

Each arrow is a clean handoff: extract→raw list, transform→clean frame, load→warehouse tables, report→results. Nothing skips a stage; each stage only knows about the one before it.

### 4. Demo Notes (instructor)

**What to run:**

```bash
python etl_pipeline.py            # online: tries the live API, auto-falls back
python etl_pipeline.py --offline  # offline: forces sample_data.json
```

Demo the **offline** run first — it's deterministic and shows the cleaning clearly. Then run **online** to show the same code pulling ~200 live records.

**Expected output at each stage (offline):**

- Extract: `[extract] loaded 23 records from sample_data.json` — 23 raw rows.
- Transform: `[transform] cleaned 23 -> 21 rows (2 dropped as dup/null/blank)` — the **2 dropped rows are the duplicate `id: 63` and the null-title `id: 101`**. Pause here; this is the moment associates *see* cleaning happen.
- Quality: `[quality] passed: 21 rows, 6 users, 21 distinct dates`.
- Load: `[load] star built: fact_task=21 rows, dim_user=6, dim_date=21`.
- Report: a per-user completion table (User 1: 6 tasks, 2 completed, 33.3%, avg title len ~19.7) followed by a weekday/weekend breakdown.

**Online difference:** the live API returns ~200 clean rows, so nothing gets dropped and the counts are larger. Same code path — that's the point.

**Gotchas to call out:**

- **API flakiness → fallback.** Kill your wifi and re-run without `--offline`; the `except` branch fires and it uses the sample. Great live demonstration of defensive extraction. Point out `raise_for_status()` — a 500 is a failure, not data.
- **Dedup/null handling.** Open `sample_data.json` and show the duplicate `id: 63` and the `null` title on `id: 101` before running, so the "2 dropped" number isn't magic.
- **Synthetic dates.** `activity_date` is derived, not from the API. Be upfront: it exists only so we have a real `dim_date` to join. In production this would be a genuine event timestamp.
- **Idempotency.** The warehouse is deleted and rebuilt each run (`WAREHOUSE.unlink()` + `CREATE OR REPLACE`). Re-running never double-loads.
- **First online run needs `httpx` installed** (`pip install -r requirements.txt`); if it's missing, the `import httpx` inside the try raises and you fall back to the sample.

### 5. Discussion Topics

1. **ETL vs. ELT — which is this, and when would you flip it?** We *transform in pandas before loading* (classic ETL). When would you instead load raw into DuckDB/BigQuery and transform with SQL (ELT)? What changes about scale, cost, and who owns the transforms?
2. **Idempotency and re-runs.** We drop and rebuild the warehouse every run. What are the trade-offs of that vs. `INSERT`-only? What breaks if two runs overlap? How would you make loads safe to retry (upserts, `MERGE`, run keys)?
3. **Incremental vs. full load.** This is a full reload of ~20-200 rows. At a million rows a day, full reload is wasteful. How would you switch to incremental — a watermark/high-water-mark column, only pulling records newer than the last run? What state would you have to persist between runs?
4. **Where SCD Type 2 would slot in.** `dim_user` is currently overwritten each run (SCD Type 1 — history is lost). If a user's label or attributes changed over time and you needed to preserve history, where in `load()` would Type 2 logic go (effective/expiry dates, `is_current` flag, surrogate keys)? See Demo 501.
5. **Orchestration and scheduling in production.** `main()` runs the stages by hand. In production what runs this on a schedule and handles retries, alerting, and dependencies between stages (Airflow, Dagster, Prefect, cron)? What does each stage becoming a separate task buy you?
6. **Data-quality gates.** Our `quality_gate` raises and halts the run. Is halting always right, or should some checks warn-and-continue, quarantine bad rows, or route to a dead-letter table? Where should the gate live — before load (as here), or as post-load assertions in the warehouse?
