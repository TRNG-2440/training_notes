# ETL vs. ELT & Pipeline Stages

> Day 5 · Note 505 · refreshes W4 `c202` (ETL concepts) + `c203` (ELT vs ETL) + `c204` (extraction) + `c205` (transformation) + `c206` (loading)

## Learning Objectives

- Distinguish ETL from ELT and explain the modern cloud-warehouse case for ELT
- Describe extraction techniques: full, incremental, CDC
- Recognize the common transformation pattern categories
- Choose a loading strategy: full refresh, append, upsert, merge

## Why This Matters

A dimensional model (Notes 501–504) is a *destination*. A pipeline is how data gets there and stays fresh. This note is the map of the three stages — Extract, Transform, Load — and the strategic choices inside each. The Day 5 capstone (`exercises/502`) is a hand-built E→T→L pipeline, so this is the conceptual spine for it.

## Concept Explanation

### ETL vs. ELT

```
ETL (traditional):  Source -> Extract -> Transform -> Load -> Warehouse
                                            ^ processing happens OUTSIDE the warehouse

ELT (modern):       Source -> Extract -> Load -> Transform -> Warehouse
                                                    ^ processing happens INSIDE the warehouse (SQL)
```

| Aspect | ETL | ELT |
|--------|-----|-----|
| Transform location | External engine (Spark, Python) | In the warehouse (SQL) |
| Order | Transform before load | Load raw, then transform |
| Raw data | Only what you designed for | Preserved — re-transform anytime |
| Flexibility | Fixed transforms | Iterative, re-runnable |
| Best fit | Legacy / on-prem / heavy pre-load masking | Cloud warehouses |

### Why ELT won for cloud warehouses

1. **Cheap storage** — keep the raw layer affordably.
2. **Powerful in-warehouse compute** — BigQuery/DuckDB/Snowflake do the transform work.
3. **Flexibility** — requirements change; re-transform from preserved raw data, no re-extract.
4. **Speed** — load first, transform in parallel with SQL.
5. **Simplicity** — transformations are just SQL (dbt-style), reviewable and testable.

```sql
-- ELT: land raw as-is, then shape with SQL in the warehouse
CREATE OR REPLACE TABLE clean_orders AS
SELECT order_id,
       customer_id,
       CAST(order_date AS DATE)  AS order_date,
       ROUND(amount, 2)          AS amount
FROM raw_orders
WHERE order_id IS NOT NULL;
```

**Still choose ETL when:** transforms need non-SQL logic (ML inference, API enrichment), you must reduce/mask sensitive data *before* it lands, or you are stuck on legacy on-prem infrastructure.

> Note: the Day 5 **capstone is ETL-shaped** (transform in pandas before load) *because* one stage pulls from an HTTP API and reshapes with Python — a good example of "reach for ETL when the transform isn't pure SQL." Once landed in DuckDB, further shaping is ELT-style SQL. Real pipelines mix both.

### Stage 1 — Extraction

| Method | What it does | Use case |
|--------|--------------|----------|
| **Full** | Re-pull the entire source each run | Small / dimension tables |
| **Incremental** | Pull only new/changed rows since a watermark | Large, frequently-updated tables |
| **CDC** | Capture row changes at the source as they happen | Real-time, minimal source load |

```python
# Full extract — simple, complete, heavy
def full_extract(table):
    return db.query(f"SELECT * FROM {table}")

# Incremental extract — track a high-water mark (timestamp or id)
def incremental_extract(table, watermark_col, last_value):
    return db.query(
        f"SELECT * FROM {table} WHERE {watermark_col} > ?", [last_value]
    )
```

Source types you will meet: databases (Postgres/MySQL), **REST/GraphQL APIs** (Day 1 `httpx`), files (CSV/JSON/Parquet on object storage), message queues.

### Stage 2 — Transformation

| Category | Purpose | Examples |
|----------|---------|----------|
| Cleaning | Fix quality issues | drop duplicates/nulls, coerce types |
| Standardization | Enforce consistency | canonical date format, lowercase emails |
| Enrichment | Add context | join reference/lookup data |
| Aggregation | Summarize | sum / count / average to a coarser grain |
| Derivation | Compute new fields | `age` from `birth_date`, `revenue` from `qty*price` |

```python
import pandas as pd  # Day 2 skills

def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["id"])                       # cleaning
    df["email"] = df["email"].str.strip().str.lower()           # standardization
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce") # type coercion
    df = df.dropna(subset=["id", "amount"])                     # completeness
    df["revenue"] = df["quantity"] * df["unit_price"]          # derivation
    return df
```

### Stage 3 — Loading

| Strategy | Behavior | Use case |
|----------|----------|----------|
| **Full refresh** | Replace whole table | small tables, non-historical dims |
| **Append** | Insert new rows | transaction fact tables, logs |
| **Upsert** | Insert or update by key | SCD Type 1 |
| **Merge** | Insert + update (+ delete) | SCD Type 2 (Note 504) |

```sql
-- Full refresh
CREATE OR REPLACE TABLE dim_product AS SELECT * FROM staging.product;

-- Append (facts are insert-only)
INSERT INTO fact_sales SELECT * FROM staging.new_sales;

-- Upsert / SCD Type 1 (DuckDB)
INSERT INTO dim_product BY NAME
SELECT * FROM staging.product
ON CONFLICT (product_key) DO UPDATE SET category = excluded.category;

-- Merge / SCD Type 2 -> see Note 504
```

**Idempotency rule:** design loads so re-running produces the same result (e.g. delete-then-insert a partition, or merge on a key). Pipelines *will* be re-run after failures — Note 506.

## Code Example

A minimal E→T→L in one place (the capstone expands this):

```python
import httpx, pandas as pd, duckdb

# EXTRACT — pull JSON from an API (Day 1 httpx)
resp = httpx.get("https://api.example.com/sales", timeout=30)
rows = resp.json()

# TRANSFORM — clean & derive with pandas (Day 2)
df = pd.DataFrame(rows)
df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
df["revenue"] = df["quantity"] * df["unit_price"]
df = df.dropna(subset=["order_id"]).drop_duplicates("order_id")

# LOAD — land into a DuckDB warehouse (Day 4) as a fact table
con = duckdb.connect("warehouse.duckdb")
con.register("staging", df)
con.execute("INSERT INTO fact_sales SELECT * FROM staging")  # append
```

## Key Takeaways

- **ETL** transforms before load; **ELT** loads raw then transforms in-warehouse with SQL — the cloud default.
- Extraction: **full** (small), **incremental** (watermark), **CDC** (real-time).
- Transformation categories: clean, standardize, enrich, aggregate, derive.
- Loading: **full refresh / append / upsert / merge** — pick by table role; keep loads **idempotent**.
- Real pipelines mix ETL and ELT; the capstone does exactly that.

## Resources

- ELT vs ETL / migration: <https://cloud.google.com/bigquery/docs/migration/pipelines>
- dbt (SQL transforms): <https://www.getdbt.com/>
- Next: `506-data-quality-orchestration-monitoring.md` — making the pipeline trustworthy and operable.
