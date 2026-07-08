# BigQuery Loading, Partitioning, and Clustering

## Learning Objectives
- Load data into BigQuery from **GCS**, a **pandas DataFrame**, and via **streaming**; know batch vs streaming trade-offs.
- Create **partitioned** tables and explain **partition pruning**.
- Create **clustered** tables and explain how clustering complements partitioning.
- Estimate the cost benefit of pruning and know where the **DuckDB** analogues sit.

## Why This Matters
Two skills separate someone who *can* run a BigQuery query from someone who runs it *cheaply and fast*: getting data in correctly, and structuring tables so queries scan less. BigQuery bills primarily on **bytes scanned** (note 406), so partitioning and clustering are not academic — they are the difference between a query that scans 50 GB and one that scans 500 MB for the same answer. This note is where cost control begins.

## Concept Explanation

### Loading Data: the Three Paths
```
   BATCH LOAD (files)            DATAFRAME LOAD            STREAMING
+---------------------+     +--------------------+     +------------------+
| GCS: CSV/JSON/      |     | pandas df in your  |     | row-by-row via   |
| Parquet/Avro/ORC    |     | Python process     |     | Storage Write /  |
| load_table_from_uri |     | load_table_from_   |     | insert_rows_json |
|                     |     | dataframe          |     |                  |
+----------+----------+     +---------+----------+     +--------+---------+
           |                          |                         |
           v                          v                         v
      free, high-throughput      convenient for ETL       near-real-time,
      preferred for bulk         from Python              small per-row cost
```

| Path | Latency | Cost | Use when |
|------|---------|------|----------|
| **Batch from GCS** | Minutes | **Free** load | Bulk / scheduled ingest; the default |
| **From DataFrame** | Seconds–minutes | Free load (goes via batch) | ETL in Python, moderate volumes |
| **Streaming** | Sub-second | Per-row charge | Live dashboards, event streams |

**Rule of thumb:** batch-load whenever you can (it is free and high-throughput). Stream only when you genuinely need sub-second freshness.

**Write dispositions** control what happens to existing data on load: `WRITE_TRUNCATE` (replace), `WRITE_APPEND` (add), `WRITE_EMPTY` (fail if not empty).

```python
from google.cloud import bigquery
client = bigquery.Client()

# Batch load Parquet from GCS
job = client.load_table_from_uri(
    "gs://my-bucket/orders/*.parquet",
    "my-project.sales.orders",
    job_config=bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition="WRITE_TRUNCATE",
    ),
)
job.result()
print(f"Loaded {job.output_rows} rows")
```

```python
# Load from a pandas DataFrame (needs pyarrow)
import pandas as pd
df = pd.DataFrame({"id": [1, 2, 3], "amount": [9.99, 5.00, 12.50]})
job = client.load_table_from_dataframe(df, "my-project.sales.tmp")
job.result()
```

> DuckDB equivalents (all free, local): batch -> `CREATE TABLE t AS SELECT * FROM 'data/*.parquet'` or `COPY t FROM 'data.csv'`; DataFrame -> `con.execute("CREATE TABLE t AS SELECT * FROM df")` (DuckDB reads a pandas `df` variable directly!); streaming -> plain `INSERT`.

### External Tables (load-free querying)
Instead of loading, you can point BigQuery at files in GCS and query them in place (note 403). No BigQuery storage cost, but every query re-reads the files and you lose partitioning/clustering benefits. Good for occasional access to lake data; load natively for anything queried often.

### Partitioning
A **partition** splits one logical table into physical segments by a column's value — almost always a **date/time** column. When your `WHERE` clause filters on that column, BigQuery reads **only the matching partitions** and skips the rest. This is **partition pruning**.

```
Unpartitioned orders                 Partitioned by DATE(created_at)
+----------------------+            +---------+ +---------+ +---------+
| all rows, all dates  |            | 2023-06 | | 2023-07 | | 2023-08 |
| a WHERE date=... still|           +---------+ +---------+ +---------+
| scans EVERYTHING     |            WHERE date='2023-07-15' reads only
+----------------------+            the 2023-07 partition -> pruning
```

Three partition kinds:
| Kind | Partition by | Example |
|------|--------------|---------|
| **Time-unit column** | a DATE/TIMESTAMP column | `PARTITION BY DATE(created_at)` |
| **Ingestion time** | when the row loaded | `PARTITION BY _PARTITIONDATE` (pseudo-column `_PARTITIONTIME`) |
| **Integer range** | bucketed integer | `PARTITION BY RANGE_BUCKET(user_id, GENERATE_ARRAY(0,1000,100))` |

```sql
-- Create a partitioned + clustered table
CREATE TABLE `my-project.sales.orders_part`
PARTITION BY DATE(created_at)
CLUSTER BY user_id
AS
SELECT * FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE created_at >= '2023-01-01';
```

```sql
-- Pruning in action: only touches one partition's bytes
SELECT COUNT(*) FROM `my-project.sales.orders_part`
WHERE created_at BETWEEN '2023-07-01' AND '2023-07-31';
```

**The `_PARTITIONTIME` pseudo-column** is BigQuery-specific: for ingestion-time partitioned tables you filter with `WHERE _PARTITIONTIME >= '2023-07-01'`. DuckDB has no such pseudo-column — you filter the real timestamp column instead.

Watch out: wrapping the partition column in a non-trivial function can **defeat pruning** (`WHERE CAST(created_at AS STRING) LIKE '2023-07%'` will scan everything). Filter the column directly.

### Clustering
**Clustering** sorts the data *within* each partition by up to four columns. It does not create separate segments; it co-locates similar values so BigQuery can skip blocks that cannot match. Great for high-cardinality columns you filter or group by (like `user_id`, `product_id`).

```
Partition = coarse buckets (usually date)
Cluster   = sorted order inside each bucket (e.g. by user_id)

  Partition 2023-07  ->  [user 1..50][user 51..99]...  (sorted)
  WHERE user_id = 73  ->  reads only the block holding 73
```

| | Partitioning | Clustering |
|---|--------------|-----------|
| Granularity | Coarse (segments) | Fine (sorted blocks) |
| Best column type | Date/time (or integer range) | High-cardinality (IDs) |
| Max columns | 1 | 4 |
| Guaranteed pruning | Yes (bytes known before run) | Best-effort |
| Combine? | **Yes — partition by date, cluster by ID** | |

Best practice: **partition by a date, cluster by the ID(s) you filter/group on.** They stack.

> DuckDB: no true partitioning/clustering, but it prunes automatically via row-group statistics on **Parquet** files, and you can write **Hive-partitioned Parquet** (`COPY t TO 'out' (FORMAT PARQUET, PARTITION_BY (dt))`) to get directory-level pruning. For the lab, the *concept* is what transfers; the offline demonstration is "filter on the partition column and observe fewer bytes/less time."

## Code Example
Create a partitioned + clustered table in Python and confirm pruning with a dry run (dry runs covered in note 406).

```python
from google.cloud import bigquery
client = bigquery.Client()

# 1. Create partitioned + clustered table via a CTAS query
ctas = """
CREATE OR REPLACE TABLE `my-project.sales.orders_part`
PARTITION BY DATE(created_at)
CLUSTER BY product_id AS
SELECT * FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE created_at >= '2023-01-01'
"""
client.query(ctas).result()

# 2. Dry-run two queries to compare bytes scanned
def bytes_for(sql):
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    return client.query(sql, job_config=cfg).total_bytes_processed

full = bytes_for("SELECT COUNT(*) FROM `my-project.sales.orders_part`")
pruned = bytes_for(
    "SELECT COUNT(*) FROM `my-project.sales.orders_part` "
    "WHERE created_at BETWEEN '2023-07-01' AND '2023-07-31'"
)
print(f"Full scan:   {full/1e6:8.1f} MB")
print(f"With filter: {pruned/1e6:8.1f} MB   ({100*(1-pruned/full):.0f}% saved)")
```

## Key Takeaways
- **Batch-load from GCS** (free, high-throughput) is the default; use **DataFrame** loads for Python ETL and **streaming** only for sub-second freshness.
- Write dispositions: `WRITE_TRUNCATE` / `WRITE_APPEND` / `WRITE_EMPTY`.
- **External tables** avoid loading but re-read files every query and can't be partitioned/clustered — load natively for hot data.
- **Partition by a date column** so `WHERE` on it triggers **pruning** — the main lever on bytes scanned. Don't wrap the partition column in functions or you lose pruning.
- **Cluster by high-cardinality IDs** to prune *within* partitions; partitioning + clustering **stack**.
- `_PARTITIONTIME` is BigQuery-only; DuckDB approximates partition pruning through Parquet row-group stats / Hive-partitioned files.

## Resources
- Loading data intro: <https://cloud.google.com/bigquery/docs/loading-data>
- Partitioned tables: <https://cloud.google.com/bigquery/docs/partitioned-tables>
- Clustered tables: <https://cloud.google.com/bigquery/docs/clustered-tables>
- Streaming (Storage Write API): <https://cloud.google.com/bigquery/docs/write-api>
- DuckDB Parquet & partitioned writes: <https://duckdb.org/docs/data/partitioning/partitioned_writes>
- Prev: `404-bigquery-sql.md` · Next: `406-bigquery-optimization-and-cost.md`
