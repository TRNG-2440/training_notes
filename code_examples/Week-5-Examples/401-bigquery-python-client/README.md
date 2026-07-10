# Demo 401 - BigQuery Python Client (with DuckDB offline fallback)

A single script, `analytics.py`, that runs one analytical query
(**top product categories by revenue in 2023**) and returns a **pandas
DataFrame** - against **either** real BigQuery **or** a local **DuckDB**
table. Pick the engine with `--engine`.

This demonstrates the core Day-4 workflow from note
`407-bigquery-python-integration.md`:

- authenticate a client,
- run a **parameterized** query,
- pull results into a DataFrame with `to_dataframe()` / `.df()`,
- report what the query cost (bytes scanned on BigQuery; rows + time on DuckDB).

The **same SQL logic** runs on both engines. The only meaningful differences:

| | BigQuery | DuckDB |
|---|----------|--------|
| Table name | `` `bigquery-public-data.thelook_ecommerce.order_items` `` | plain `order_items` |
| Query parameter | `@start_date` + `ScalarQueryParameter` | `$start_date` dict |
| Data source | public dataset (real, huge) | small sample built on the fly |
| Cost report | bytes scanned + $ estimate | row count + wall-clock time |

## Setup

```bash
cd 2440-W5/demos/401-bigquery-python-client
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

(For the DuckDB path you only need `duckdb` and `pandas`; the BigQuery
libraries are optional until you use `--engine bigquery`.)

## Option A - Offline with DuckDB (zero cloud setup)

Nothing to configure. This is the path if you don't have GCP access.

```bash
python analytics.py --engine duckdb
```

Expected output (numbers are deterministic from the built-in sample):

```
Engine: duckdb

[duckdb] 5 rows in 0.004s (local, no billing)

Top categories by revenue:
   category  line_items  revenue
  Outerwear        2320 259077.0
      Shoes        2280 256800.0
       ...
```

`--engine duckdb` is the default, so `python analytics.py` also works.

## Option B - Real BigQuery (free sandbox, no billing card)

1. **Create a sandbox** (no credit card): sign in at
   <https://cloud.google.com/bigquery/docs/sandbox>. You get 10 GB storage
   and **1 TB of free query processing per month** - this demo scans well
   under that.

2. **Install the gcloud CLI** and authenticate with Application Default
   Credentials:

   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

   (Alternatively use a **service account** key and set
   `GOOGLE_APPLICATION_CREDENTIALS=/path/key.json`.)

3. **Run it:**

   ```bash
   python analytics.py --engine bigquery
   ```

   The query reads the public `bigquery-public-data.thelook_ecommerce`
   dataset. Billing is charged to *your* project but stays inside the free
   tier. The script prints the GB scanned and an estimated cost.

## What to look at in the code

- `run_bigquery()` - `bigquery.Client()`, `QueryJobConfig` with a
  `ScalarQueryParameter`, `.to_dataframe()`, and reading
  `job.total_bytes_processed` for cost.
- `run_duckdb()` - `duckdb.connect()`, an on-the-fly sample table, the same
  query with a `$start_date` parameter, and `.df()`.
- Notice how little differs between the two: the transferable skill is the
  **shape** of the workflow, not the vendor.

## Troubleshooting

- `DefaultCredentialsError` -> you haven't run
  `gcloud auth application-default login` (BigQuery path only).
- `to_dataframe()` warning/error about types -> `pip install pyarrow db-dtypes`.
- No internet / no GCP account -> just use `--engine duckdb`; it needs neither.

## Related material

- Note `407-bigquery-python-integration.md` (the client API in depth)
- Note `406-bigquery-optimization-and-cost.md` (bytes-scanned cost model)
- Exercise `402-bigquery-python-lab.md` (build your own version of this)

## Follow-Along Build Walkthrough

### 1. Intro - what we are building

We are going to write **one script** that answers a single analytical
question - *"what are the top product categories by revenue and order count
in 2023?"* - and hands the answer back as a **pandas DataFrame**.

The twist: the same script runs against **two engines**, chosen at the
command line with an `--engine` flag:

- `--engine bigquery` runs the query against Google's public
  `bigquery-public-data.thelook_ecommerce` dataset in the cloud.
- `--engine duckdb` runs the *same query logic* against a small sample table
  we build locally, in memory, with zero cloud setup.

The goal is to internalize the **shape** of the warehouse-to-DataFrame
workflow (authenticate -> parameterized query -> pull into pandas -> report
cost) rather than memorizing one vendor's SDK. The dual-engine design also
means nobody is blocked: if your GCP sandbox or auth isn't ready, you run the
DuckDB path and follow along identically. Same SQL, same DataFrame, same
printed table.

We'll build `analytics.py` from the outside in, in the order a learner would
naturally reach for each piece.

### 2. Step-by-step assembly

#### Step 0 - imports and constants

Start with the module docstring and the imports. We only need the standard
library plus pandas at the top level; the engine-specific libraries
(`google.cloud.bigquery`, `duckdb`) are imported *inside* their functions so
that a learner without the BigQuery SDK installed can still run the DuckDB
path.

```python
from __future__ import annotations

import argparse
import time

import pandas as pd

ON_DEMAND_USD_PER_TB = 6.25  # BigQuery on-demand price (approx)
```

- `argparse` gives us the `--engine` flag.
- `time` is used only on the DuckDB side to report wall-clock query time.
- `pd` is the common return type - both engines produce a `pandas.DataFrame`.
- `ON_DEMAND_USD_PER_TB` is the BigQuery on-demand price we use to turn
  "bytes scanned" into a dollar estimate.

#### Step 1 - the engine selection (argparse)

Before writing either query path, decide *how* the user picks one. This is
the entry point of the whole program, so it's a good anchor.

```python
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=["bigquery", "duckdb"],
        default="duckdb",
        help="Which backend to run against (default: duckdb, zero setup).",
    )
    args = parser.parse_args()

    print(f"Engine: {args.engine}\n")
    df = run_bigquery() if args.engine == "bigquery" else run_duckdb()

    print("\nTop categories by revenue:")
    print(df.to_string(index=False))
```

- `argparse.ArgumentParser(description=__doc__)` reuses the module docstring
  as the `--help` text, so the usage examples at the top of the file show up
  in `python analytics.py --help`.
- `choices=["bigquery", "duckdb"]` makes argparse reject any other value with
  a friendly error - the user can only pick a valid engine.
- `default="duckdb"` is the design decision that keeps everyone unblocked:
  bare `python analytics.py` runs the offline path with no configuration.
- The one-line ternary dispatches to `run_bigquery()` or `run_duckdb()`. Both
  return a DataFrame, so everything downstream (the `print`) is
  engine-agnostic.

We haven't written `run_bigquery` / `run_duckdb` yet - that's fine. We now
know the contract: each returns a `pd.DataFrame`.

#### Step 2 - the shared query (two dialects)

The analytical question is identical for both engines, so we define the SQL
as module-level constants. There are two versions because of small dialect
differences - flag these clearly for learners.

```python
BIGQUERY_SQL = """
SELECT
    p.category,
    COUNT(*)                AS line_items,
    ROUND(SUM(oi.sale_price), 2) AS revenue
FROM `bigquery-public-data.thelook_ecommerce.order_items` AS oi
JOIN `bigquery-public-data.thelook_ecommerce.products`   AS p
    ON oi.product_id = p.id
WHERE oi.created_at >= @start_date
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 10
"""

DUCKDB_SQL = """
SELECT
    p.category,
    COUNT(*)                AS line_items,
    ROUND(SUM(oi.sale_price), 2) AS revenue
FROM order_items AS oi
JOIN products   AS p
    ON oi.product_id = p.id
WHERE oi.created_at >= $start_date
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 10
"""

START_DATE = "2023-01-01"
```

The `SELECT ... JOIN ... GROUP BY ... ORDER BY ... LIMIT` body is byte-for-byte
the same. Only two things differ, and both are **BigQuery-specific syntax vs
DuckDB equivalents**:

- **Table naming.** BigQuery uses a fully-qualified,
  backtick-quoted `` `project.dataset.table` `` name
  (`` `bigquery-public-data.thelook_ecommerce.order_items` ``). DuckDB uses a
  plain local table name (`order_items`).
- **Query parameter placeholder.** BigQuery uses named parameters written
  `@start_date`. DuckDB uses `$start_date`. (We'll bind the value differently
  in each function - see below.)

`START_DATE = "2023-01-01"` is the single value we pass in as a parameter to
both, so "2023" is defined in exactly one place.

#### Step 3 - the DuckDB path (build a sample, run the query)

This is the path that needs no cloud, so build it first. It has two parts: a
helper that fabricates a small dataset shaped like `thelook_ecommerce`, and
the function that runs the query.

```python
def _build_sample(con) -> None:
    """Create a small local dataset that mimics thelook_ecommerce shape."""
    con.execute("""
        CREATE TABLE products AS
        SELECT * FROM (VALUES
            (1, 'Jeans'), (2, 'Tops'), (3, 'Shoes'),
            (4, 'Accessories'), (5, 'Outerwear')
        ) AS t(id, category)
    """)
    # Deterministic pseudo-random order items across 2022-2023.
    con.execute("""
        CREATE TABLE order_items AS
        SELECT
            i                                         AS order_item_id,
            (i % 5) + 1                               AS product_id,
            ROUND(5 + (i * 7 % 200) + (i % 13), 2)    AS sale_price,
            DATE '2022-06-01' + (i % 500) * INTERVAL 1 DAY AS created_at
        FROM range(20000) AS r(i)
    """)
```

- `_build_sample(con)` creates two tables that match the columns our query
  needs: `products(id, category)` and
  `order_items(order_item_id, product_id, sale_price, created_at)`.
- The `products` table is a literal `VALUES` list of five categories.
- The `order_items` table is generated from `range(20000)` - DuckDB's
  table-producing function - so we get 20,000 rows *deterministically*. The
  arithmetic (`i % 5`, `i * 7 % 200`, dates spread across 500 days from
  2022-06-01) means the output numbers are always the same, which is why the
  README's expected output is stable.

```python
def run_duckdb() -> pd.DataFrame:
    import duckdb

    con = duckdb.connect()  # in-memory
    _build_sample(con)

    t0 = time.perf_counter()
    df = con.execute(DUCKDB_SQL, {"start_date": START_DATE}).df()
    elapsed = time.perf_counter() - t0
    print(f"[duckdb] {len(df)} rows in {elapsed:.3f}s "
          f"(local, no billing)")
    return df
```

- `import duckdb` is *inside* the function so it's only required when this
  path runs.
- `duckdb.connect()` with no argument opens an **in-memory** database - it
  vanishes when the process exits, perfect for a demo.
- `_build_sample(con)` populates it.
- `con.execute(DUCKDB_SQL, {"start_date": START_DATE})` runs the query and
  **binds the parameter** as a dict - the key `start_date` matches the
  `$start_date` placeholder. This is the parameterized-query equivalent of
  BigQuery's `ScalarQueryParameter`.
- `.df()` is DuckDB's method to materialize the result set as a pandas
  DataFrame - the DuckDB counterpart of BigQuery's `.to_dataframe()`.
- We wrap it in `time.perf_counter()` to report rows + wall-clock time, since
  there are no "bytes scanned" or billing to report locally.

#### Step 4 - the BigQuery path (client, query, to_dataframe)

Now the cloud path. Structurally it mirrors `run_duckdb()`: connect, run a
parameterized query, get a DataFrame, report cost.

```python
def run_bigquery() -> pd.DataFrame:
    from google.cloud import bigquery

    client = bigquery.Client()  # uses Application Default Credentials

    cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", START_DATE)
        ]
    )
    job = client.query(BIGQUERY_SQL, job_config=cfg)
    df = job.to_dataframe()  # blocks until the job finishes

    scanned_gb = (job.total_bytes_processed or 0) / 1e9
    est_usd = scanned_gb / 1000 * ON_DEMAND_USD_PER_TB
    print(f"[bigquery] scanned {scanned_gb:.3f} GB  "
          f"~ ${est_usd:.4f} (free within 1 TB/month)")
    return df
```

- `from google.cloud import bigquery` is again a function-local import, so
  learners on the DuckDB path never need this library installed.
- `bigquery.Client()` creates the authenticated client. It reads
  **Application Default Credentials** (ADC) - whatever
  `gcloud auth application-default login` set up, or a service-account key
  pointed at by `GOOGLE_APPLICATION_CREDENTIALS`. No project string is passed;
  ADC supplies it.
- `bigquery.QueryJobConfig(query_parameters=[...])` is how BigQuery binds
  parameters. `ScalarQueryParameter("start_date", "DATE", START_DATE)` names
  the parameter (matching `@start_date`), declares its SQL type (`DATE`), and
  supplies the value. This is **BigQuery-specific**; the DuckDB equivalent was
  just the `{"start_date": ...}` dict.
- `client.query(BIGQUERY_SQL, job_config=cfg)` submits the query and returns a
  **job** object immediately (asynchronous).
- `job.to_dataframe()` blocks until the job finishes and pulls the results
  into a pandas DataFrame - the BigQuery counterpart of DuckDB's `.df()`.
- `job.total_bytes_processed` is the cost signal unique to a serverless
  warehouse: BigQuery bills by **bytes scanned**. We convert to GB and to an
  estimated dollar figure using `ON_DEMAND_USD_PER_TB`. DuckDB has no analog -
  there it reports rows + time instead.

#### Step 5 - printing the results (shared)

Both functions return a DataFrame, so `main()` prints it the same way
regardless of engine:

```python
    print("\nTop categories by revenue:")
    print(df.to_string(index=False))
```

`df.to_string(index=False)` renders the whole DataFrame as aligned text
without the pandas row index - clean enough to read in a terminal during a
demo.

Finish the file with the standard entry-point guard:

```python
if __name__ == "__main__":
    main()
```

### 3. How it fits together

The control flow is a straight line from the CLI flag to the printed table:

1. **CLI flag.** `main()` parses `--engine` (defaulting to `duckdb`).
2. **Dispatch.** The ternary picks `run_bigquery()` or `run_duckdb()`. Each is
   self-contained: it imports its own driver, connects, and runs.
3. **Query + parameter.** The chosen function runs its dialect of the shared
   query, binding `START_DATE` as a named parameter (`@start_date` via
   `ScalarQueryParameter`, or `$start_date` via a dict).
4. **DataFrame.** The result is materialized into pandas -
   `job.to_dataframe()` for BigQuery, `.df()` for DuckDB - and returned to
   `main()`.
5. **Cost report.** Each function prints its own engine-appropriate stat line
   (GB scanned + $ estimate, or rows + seconds) before returning.
6. **Print.** Back in `main()`, the DataFrame is printed with
   `to_string(index=False)`.

The key teaching point: steps 3-4 are the *same idea* on both engines. The
only real differences are table addressing, the parameter-binding syntax, and
what "cost" means.

### 4. Demo Notes (instructor)

**What to run.**

- Lead with the offline path - it needs **zero setup** and produces
  deterministic output:

  ```bash
  python analytics.py --engine duckdb
  ```

  (or just `python analytics.py`, since `duckdb` is the default). Everyone in
  the room can run this immediately.

- Then, if you have a sandbox wired up, show the real thing:

  ```bash
  python analytics.py --engine bigquery
  ```

**Expected output (DuckDB).** Deterministic from the built-in 20,000-row
sample:

```
Engine: duckdb

[duckdb] 5 rows in 0.004s (local, no billing)

Top categories by revenue:
   category  line_items  revenue
  Outerwear        2320 259077.0
      Shoes        2280 256800.0
       ...
```

**Expected output (BigQuery).** Real categories from `thelook_ecommerce`,
preceded by a scan line like
`[bigquery] scanned 0.0xx GB  ~ $0.000x (free within 1 TB/month)`. The exact
numbers vary as the public dataset grows.

**Auth gotchas.**

- `--engine bigquery` needs a **BigQuery sandbox** (free, no credit card) plus
  **Application Default Credentials**. Run
  `gcloud auth application-default login` and
  `gcloud config set project YOUR_PROJECT_ID` first.
- A `DefaultCredentialsError` means ADC isn't set up - you skipped the
  `gcloud auth ...` step.
- Type errors from `to_dataframe()` usually mean a missing dependency:
  `pip install pyarrow db-dtypes`.
- No network / no GCP account? That's exactly what `--engine duckdb` is for -
  it needs neither, and the demo is identical.

### 5. Discussion Topics

1. **Serverless cost model.** BigQuery bills by *bytes scanned*, not by rows
   returned or time spent. Why does `SELECT *` on a wide table cost more than
   selecting three columns, even for the same `LIMIT`? How does
   `job.total_bytes_processed` help you predict a bill *before* it's a
   surprise?
2. **Is DuckDB a fair local proxy?** We ran the same SQL shape locally. Where
   does the analogy hold (SQL semantics, DataFrame output, parameterization)
   and where does it break down (data volume, distributed execution, the
   bytes-scanned cost model that only exists in the cloud)?
3. **`to_dataframe()` / `.df()` memory limits.** Both pull the *entire* result
   set into local RAM. What happens if the query returned 50 million rows
   instead of 10? How do `LIMIT`, aggregation, and pushing filters into the
   `WHERE` clause protect your laptop?
4. **Parameterized queries.** We passed `start_date` as a bound parameter
   (`@start_date` / `$start_date`) instead of string-formatting the date into
   the SQL. What does this buy us in terms of SQL injection safety, query
   caching, and reuse?
5. **When to push compute to the warehouse.** Our query does the
   `GROUP BY`/`SUM` in SQL and only ships 10 summarized rows back to pandas.
   When is it right to aggregate in the warehouse vs. pulling raw rows and
   doing the work in pandas? What are the trade-offs in bytes transferred,
   memory, and speed?
6. **Same workflow, different vendor.** How much of `run_bigquery()` would
   change if the warehouse were Snowflake or Redshift instead? What is the
   *transferable* skill here - the shape of the workflow, or any one SDK?
