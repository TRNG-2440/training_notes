# BigQuery Datasets, Tables, and Types

## Learning Objectives
- Navigate the BigQuery hierarchy: **project -> dataset -> table** and the fully qualified name.
- Distinguish the table types: **native, external, views, materialized views**.
- Use BigQuery's core **data types**, including the nested types **STRUCT**, **ARRAY**, and **JSON**.
- Read and write a **table schema** in SQL DDL and in Python.
- Map each concept to its **DuckDB** equivalent for offline practice.

## Why This Matters
Before you can query anything you have to know how BigQuery *addresses* data and how it *shapes* it. Two things trip up newcomers: (1) the three-level name with backticks, which is different from every plain database you have used, and (2) **nested data** — BigQuery lets a single row contain arrays of structs, which is unusual coming from normalized SQL. Nested types are not a curiosity; the public `thelook_ecommerce` dataset and countless real event tables use them, and they are the key to avoiding expensive JOINs. Get comfortable here and the SQL note (404) will feel natural.

## Concept Explanation

### The Hierarchy: Project -> Dataset -> Table
```
Organization
   └── Project              billing + IAM boundary   e.g. my-analytics-proj
        └── Dataset         a named group of tables  e.g. sales
             └── Table      the actual data          e.g. orders
                  └── Column / Field
```

You reference a table by its **fully qualified name**, backtick-quoted:

```sql
`project.dataset.table`
-- e.g.
`bigquery-public-data.thelook_ecommerce.orders`
```

| Level | What it is | Notes |
|-------|-----------|-------|
| **Project** | Billing + access boundary | Queries are billed to *your* project even when reading public data |
| **Dataset** | Container of tables/views; has a **location** (US, EU, ...) | Location is fixed at creation; you cannot JOIN across regions |
| **Table** | The data, with a schema | Can be native, external, a view, or materialized |

> DuckDB equivalent: there is no project/dataset layer. You just use `schema.table` or a bare `table` in the current database. A DuckDB file *is* roughly the "dataset."

Create a dataset:
```sql
-- BigQuery
CREATE SCHEMA IF NOT EXISTS `my-project.sales`
OPTIONS (location = 'US', default_table_expiration_days = 7);
```

### Table Types
BigQuery offers four kinds of "tables." Choosing the right one affects cost and freshness.

| Type | Data lives... | Cost model | Use when |
|------|---------------|-----------|----------|
| **Native (managed)** | Inside BigQuery (Capacitor/Colossus) | Storage + query | Default; best performance |
| **External** | In GCS / Sheets / Cloud SQL, read in place | Query only (no BQ storage) | Query lake files without loading |
| **View** | Nothing stored — a saved SQL query | Query re-runs each time | Reusable logic, no extra storage |
| **Materialized view** | Precomputed results, auto-refreshed | Storage + cheaper reads | Repeated expensive aggregations |

```
NATIVE            EXTERNAL           VIEW              MATERIALIZED VIEW
+---------+       +---------+        +-----------+     +------------------+
| data in |       | pointer |        | saved SQL |     | precomputed rows |
| BigQuery|       | to GCS  |        | (no data) |     | + auto-refresh   |
+---------+       +---------+        +-----------+     +------------------+
```

```sql
-- View: logic reused, storage-free, always fresh
CREATE VIEW `my-project.sales.recent_orders` AS
SELECT order_id, user_id, created_at
FROM `my-project.sales.orders`
WHERE created_at >= '2024-01-01';

-- External table: query a CSV in GCS without loading it
CREATE EXTERNAL TABLE `my-project.sales.us_states`
OPTIONS (
  format = 'CSV',
  uris = ['gs://cloud-samples-data/bigquery/us-states/us-states.csv'],
  skip_leading_rows = 1
);
```

> DuckDB equivalent: `CREATE VIEW` is identical. For "external" data, DuckDB reads files directly in a query: `SELECT * FROM 'data/*.parquet'` or `read_csv_auto('states.csv')` — no external-table DDL needed.

### Core Data Types
| BigQuery type | Meaning | Example literal | DuckDB equivalent |
|---------------|---------|-----------------|-------------------|
| `INT64` | 64-bit integer | `42` | `BIGINT` / `INTEGER` |
| `FLOAT64` | double | `3.14` | `DOUBLE` |
| `NUMERIC` / `BIGNUMERIC` | exact decimal (money) | `9.99` | `DECIMAL` |
| `STRING` | UTF-8 text | `'hello'` | `VARCHAR` |
| `BOOL` | true/false | `TRUE` | `BOOLEAN` |
| `BYTES` | binary | `b'\x00'` | `BLOB` |
| `DATE` | calendar date | `DATE '2024-01-01'` | `DATE` |
| `DATETIME` | date+time, no zone | `DATETIME '2024-01-01 12:00'` | `TIMESTAMP` |
| `TIMESTAMP` | absolute instant (UTC) | `TIMESTAMP '2024-01-01 12:00 UTC'` | `TIMESTAMPTZ` |
| `TIME` | time of day | `TIME '12:30:00'` | `TIME` |
| `GEOGRAPHY` | spatial (GIS) | `ST_GEOGPOINT(lng, lat)` | via `spatial` ext |
| **`STRUCT`** | ordered named fields (a record) | `STRUCT(1 AS id, 'a' AS name)` | `STRUCT`/`ROW` |
| **`ARRAY`** | repeated values of one type | `[1, 2, 3]` | `LIST` |
| **`JSON`** | native semi-structured JSON | `JSON '{"k":1}'` | `JSON` |

Naming note: BigQuery uses `INT64`/`FLOAT64` (bit-width names) where standard SQL says `INTEGER`/`DOUBLE`. Both aliases usually work in DDL, but you will see the `64` forms everywhere.

### Nested Types: STRUCT and ARRAY (the big idea)
Coming from normalized SQL, you would model an order and its line items as **two tables** joined by `order_id`. BigQuery lets you keep the line items **inside** the order row as an `ARRAY<STRUCT<...>>`. No JOIN needed, and columnar storage keeps it efficient.

```
Normalized (2 tables)            Nested (1 table, 1 row per order)
orders     order_items          orders
+----+     +----+------+        +----+--------------------------------+
| id | <-- | oid| prod |        | id | items (ARRAY<STRUCT>)          |
+----+     +----+------+        +----+--------------------------------+
| 1  |     | 1  | A    |        | 1  | [{prod:A, qty:2},{prod:B,qty:1}]|
| 2  |     | 1  | B    |        | 2  | [{prod:C, qty:5}]               |
+----+     | 2  | C    |        +----+--------------------------------+
           +----+------+
```

```sql
-- A STRUCT groups fields; an ARRAY repeats them
SELECT
  order_id,
  ARRAY_AGG(STRUCT(product_id, sale_price)) AS items
FROM `bigquery-public-data.thelook_ecommerce.order_items`
GROUP BY order_id
LIMIT 5;
```

To turn the nested rows back into flat rows you **UNNEST** (covered fully in note 404):
```sql
SELECT order_id, item.product_id, item.sale_price
FROM my_orders_nested, UNNEST(items) AS item;
```

> DuckDB equivalent: `LIST` (array), `STRUCT`, `list()` aggregate, and `UNNEST(...)` all exist with almost identical syntax, so nested exercises run offline.

### JSON Type
For truly variable/semi-structured payloads, the native `JSON` type stores and indexes JSON and lets you access fields with dot/bracket paths:
```sql
SELECT
  payload.user.id       AS user_id,     -- dot access
  JSON_VALUE(payload, '$.event.type') AS event_type
FROM `my-project.raw.events`;
```
Use `STRUCT`/`ARRAY` when the shape is known and stable; use `JSON` when it is unpredictable.

## Code Example
Defining a schema with a nested column, in SQL and in the Python client.

```sql
-- DDL: a native table with an ARRAY<STRUCT> column
CREATE TABLE `my-project.sales.orders` (
  order_id   INT64    NOT NULL,
  user_id    INT64,
  created_at TIMESTAMP,
  items ARRAY<STRUCT<product_id INT64, qty INT64, price NUMERIC>>
);
```

```python
from google.cloud import bigquery

client = bigquery.Client()

schema = [
    bigquery.SchemaField("order_id", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("user_id", "INT64"),
    bigquery.SchemaField("created_at", "TIMESTAMP"),
    # A repeated STRUCT = ARRAY<STRUCT<...>>
    bigquery.SchemaField(
        "items", "RECORD", mode="REPEATED",
        fields=[
            bigquery.SchemaField("product_id", "INT64"),
            bigquery.SchemaField("qty", "INT64"),
            bigquery.SchemaField("price", "NUMERIC"),
        ],
    ),
]
table = bigquery.Table("my-project.sales.orders", schema=schema)
table = client.create_table(table, exists_ok=True)
print(f"Created {table.full_table_id} with {len(table.schema)} top-level fields")
```

Note the Python client calls a STRUCT a `RECORD` and an ARRAY `mode="REPEATED"` — the same thing under two names.

## Key Takeaways
- Address data as `` `project.dataset.table` `` — three levels, backtick-quoted. Datasets have a fixed **location**.
- Four table types: **native** (default), **external** (query files in place), **view** (saved SQL), **materialized view** (precomputed, auto-refreshed).
- Types use bit-width names (`INT64`, `FLOAT64`); money -> `NUMERIC`.
- **STRUCT** = a record of named fields; **ARRAY** = repeated values; together `ARRAY<STRUCT>` models one-to-many *without a JOIN*. **UNNEST** flattens it back.
- Use **JSON** for unpredictable shapes; **STRUCT/ARRAY** for known ones.
- DuckDB mirrors all of this (`LIST`, `STRUCT`, `UNNEST`, `CREATE VIEW`, direct file reads) so offline practice is faithful.

## Resources
- Datasets & tables intro: <https://cloud.google.com/bigquery/docs/datasets-intro>
- Data types: <https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types>
- Work with arrays: <https://cloud.google.com/bigquery/docs/arrays>
- Nested & repeated data: <https://cloud.google.com/bigquery/docs/nested-repeated>
- DuckDB data types: <https://duckdb.org/docs/sql/data_types/overview>
- Prev: `402-what-is-bigquery.md` · Next: `404-bigquery-sql.md`
