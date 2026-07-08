# BigQuery Python Integration

## Learning Objectives
- Install and authenticate the **`google-cloud-bigquery`** client (ADC and service accounts).
- Run queries and pull results into a **pandas DataFrame** with `to_dataframe()`.
- Use **parameterized queries** to pass values safely.
- **Load a DataFrame** into a table and read back **job stats** (bytes scanned, cost).
- Handle errors, and use a **DuckDB fallback** that mirrors the same workflow offline.

## Why This Matters
SQL in the console is fine for exploration, but real data engineering is *automated*: pipelines that run queries on a schedule, land results in tables, and hand DataFrames to downstream pandas/ML code (which you reinforced on Day 2). The BigQuery Python client is the seam between SQL and Python. This note is the toolkit for exercise 402 and for the Day 5 ETL work. And because not everyone has cloud access, every pattern here has a **DuckDB twin** — the same shape of code (`connect -> query -> to DataFrame -> load`), so the skill transfers even offline.

## Concept Explanation

### Install
```bash
pip install google-cloud-bigquery pandas pyarrow db-dtypes
# offline fallback:
pip install duckdb pandas
```
`pyarrow` and `db-dtypes` are what make `to_dataframe()` fast and type-correct — install them or you'll hit warnings/errors on certain types.

### Authentication
BigQuery needs to know *who you are* and *which project to bill*. Three common ways:

| Method | How | Use when |
|--------|-----|----------|
| **ADC (recommended)** | `gcloud auth application-default login` once, then `bigquery.Client()` | Local dev, sandbox |
| **Service account** | `Client.from_service_account_json("key.json")` | Automation, CI, servers |
| **Environment var** | `export GOOGLE_APPLICATION_CREDENTIALS=key.json` then `Client()` | Containers |

```python
from google.cloud import bigquery

client = bigquery.Client()                                   # ADC
client = bigquery.Client(project="my-project")               # explicit billing project
client = bigquery.Client.from_service_account_json("key.json")  # service account
```

For the **sandbox**: sign in, run `gcloud auth application-default login`, set your project, and `bigquery.Client()` just works. Queries against `bigquery-public-data` are billed to *your* project (free within 1 TB/month).

### Running a Query -> DataFrame
The one-liner you'll use most:
```python
df = client.query(sql).to_dataframe()
```
`client.query()` returns a **job** immediately (async). Calling `.result()` (or `.to_dataframe()`, which waits) blocks until it finishes.

```python
sql = """
SELECT category, COUNT(*) AS n, AVG(retail_price) AS avg_price
FROM `bigquery-public-data.thelook_ecommerce.products`
GROUP BY category
ORDER BY n DESC
LIMIT 10
"""
df = client.query(sql).to_dataframe()
print(df.head())
```

### Parameterized Queries (do this, not f-strings)
Never build SQL by string-formatting user input — it's an injection risk and mishandles types. Use **query parameters** (`@name`):

```python
sql = """
SELECT order_id, sale_price, created_at
FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE created_at >= @start_date
  AND sale_price > @min_price
"""
cfg = bigquery.QueryJobConfig(query_parameters=[
    bigquery.ScalarQueryParameter("start_date", "DATE", "2023-01-01"),
    bigquery.ScalarQueryParameter("min_price", "FLOAT64", 50.0),
])
df = client.query(sql, job_config=cfg).to_dataframe()
```
Array parameters use `ArrayQueryParameter("ids", "INT64", [1, 2, 3])` with `WHERE id IN UNNEST(@ids)`.

> DuckDB fallback: DuckDB parameters use `?` (positional) or `$name`:
> ```python
> con.execute("SELECT * FROM order_items WHERE created_at >= ? AND sale_price > ?",
>             ["2023-01-01", 50.0]).df()
> ```

### Loading a DataFrame into a Table
```python
import pandas as pd
df = pd.DataFrame({"id": [1, 2, 3], "label": ["a", "b", "c"]})

job = client.load_table_from_dataframe(
    df, "my-project.sales.demo",
    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
)
job.result()
print(f"Loaded {job.output_rows} rows")
```

> DuckDB fallback: DuckDB reads a local `df` variable by name — no client upload needed:
> ```python
> con.execute("CREATE OR REPLACE TABLE demo AS SELECT * FROM df")
> ```

### Job Stats and Cost
Every finished job exposes what it scanned — the basis for cost reporting (note 406).
```python
job = client.query(sql)
job.result()  # wait
print("bytes processed:", job.total_bytes_processed)
print("bytes billed:   ", job.total_bytes_billed)
print("cache hit:      ", job.cache_hit)
est_usd = (job.total_bytes_billed or 0) / 1e12 * 6.25
print(f"est cost: ${est_usd:.4f}")
```
For a cost estimate *without* running, dry-run (note 406): `QueryJobConfig(dry_run=True)` and read `total_bytes_processed`.

> DuckDB fallback: no bytes-billed concept. Report **rows** and wall-clock time instead:
> ```python
> import time
> t = time.perf_counter()
> out = con.execute(sql).df()
> print(f"{len(out)} rows in {time.perf_counter()-t:.3f}s")
> ```

### Error Handling
```python
from google.api_core.exceptions import NotFound, BadRequest, Forbidden

try:
    df = client.query(sql).to_dataframe()
except NotFound as e:      # table/dataset missing
    print("Not found:", e)
except BadRequest as e:    # SQL syntax / type error
    print("Bad query:", e)
except Forbidden as e:     # permissions / quota
    print("Forbidden:", e)
```

## Code Example
A tiny **engine-agnostic** helper — the pattern behind demo 401 and exercise 402. It runs the *same SQL* on either backend, so associates without cloud access still complete every task.

```python
"""bq_or_duck.py - run analytics on BigQuery OR DuckDB with one interface."""
from __future__ import annotations
import time
import pandas as pd


class Analytics:
    def __init__(self, engine: str = "duckdb", project: str | None = None):
        self.engine = engine
        if engine == "bigquery":
            from google.cloud import bigquery
            self._bq = bigquery
            self.client = bigquery.Client(project=project)
        elif engine == "duckdb":
            import duckdb
            self.con = duckdb.connect()
        else:
            raise ValueError("engine must be 'bigquery' or 'duckdb'")

    def query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        if self.engine == "bigquery":
            cfg = None
            if params:
                qp = [self._bq.ScalarQueryParameter(k, _bq_type(v), v)
                      for k, v in params.items()]
                cfg = self._bq.QueryJobConfig(query_parameters=qp)
            job = self.client.query(sql, job_config=cfg)
            df = job.to_dataframe()
            print(f"[bq] scanned {job.total_bytes_processed/1e6:.1f} MB")
            return df
        # duckdb: named params via $name
        t = time.perf_counter()
        df = self.con.execute(sql, params or {}).df()
        print(f"[duckdb] {len(df)} rows in {time.perf_counter()-t:.3f}s")
        return df

    def load_df(self, df: pd.DataFrame, table: str) -> int:
        if self.engine == "bigquery":
            job = self.client.load_table_from_dataframe(df, table)
            job.result()
            return job.output_rows
        self.con.register("_incoming", df)
        self.con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _incoming")
        return len(df)


def _bq_type(v):
    return {int: "INT64", float: "FLOAT64", bool: "BOOL"}.get(type(v), "STRING")


if __name__ == "__main__":
    a = Analytics("duckdb")                      # runs offline with zero setup
    a.con.execute("CREATE TABLE t AS SELECT * FROM range(5) AS r(n)")
    print(a.query("SELECT SUM(n) AS total FROM t"))
```

## Key Takeaways
- Install `google-cloud-bigquery pandas pyarrow db-dtypes`; authenticate with **ADC** (`gcloud auth application-default login`) for dev, service accounts for automation.
- `client.query(sql).to_dataframe()` is the workhorse; queries are **async jobs** — `.result()`/`.to_dataframe()` block until done.
- Use **parameterized queries** (`@name` + `ScalarQueryParameter`), never f-string interpolation.
- **Load** with `load_table_from_dataframe`; read `job.total_bytes_processed/billed` for cost reporting; **dry-run** to estimate first.
- Catch `NotFound`, `BadRequest`, `Forbidden` from `google.api_core.exceptions`.
- The **DuckDB fallback** mirrors every step (`connect -> execute -> .df() -> CREATE TABLE AS`) so the workflow is learnable with zero cloud setup.

## Resources
- Python client reference: <https://cloud.google.com/python/docs/reference/bigquery/latest>
- Authentication (ADC): <https://cloud.google.com/docs/authentication/provide-credentials-adc>
- Query parameters: <https://cloud.google.com/bigquery/docs/parameterized-queries>
- DataFrame download (BigQuery Storage API): <https://cloud.google.com/bigquery/docs/bigquery-storage-python-pandas>
- DuckDB Python API: <https://duckdb.org/docs/api/python/overview>
- Prev: `406-bigquery-optimization-and-cost.md` · See demo `demos/401-bigquery-python-client/`
