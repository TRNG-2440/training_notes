# Data Warehousing, OLTP vs OLAP

## Learning Objectives
- Define a **data warehouse** and explain the four Inmon characteristics (subject-oriented, integrated, time-variant, non-volatile).
- Distinguish a **data warehouse** from a **data lake** and a **lakehouse**.
- Compare **OLTP** and **OLAP** systems across purpose, schema, query shape, and optimization.
- Explain how data flows from OLTP systems into an OLAP warehouse via ETL/ELT.
- Survey the major **data-store vendors** and where BigQuery sits among them.

## Why This Matters
Today is the core technical day of the week: **BigQuery**, a cloud OLAP data warehouse. But a tool only makes sense once you know the *problem* it solves. Your transactional apps (the FastAPI services from Day 1, the databases behind them) are tuned to *run the business* one row at a time. The moment someone asks "what were revenue trends by region last quarter?" those systems buckle: the query scans millions of rows, competes with live traffic, and the schema is normalized into a dozen JOINs.

A **data warehouse** is the purpose-built answer. It is where analytics lives, separate from the operational systems, optimized for reading enormous slices of history. Understanding warehouse vs lake, and OLTP vs OLAP, is what lets you explain *why* BigQuery exists and *when* to reach for it versus a regular database.

## Concept Explanation

### What Is a Data Warehouse?
A **data warehouse** is a centralized repository designed for analytical processing and reporting. It consolidates data from many operational systems into one unified, query-optimized view.

Bill Inmon, the "father of data warehousing," defined it with four characteristics:

| Characteristic | Meaning | Contrast with operational DB |
|----------------|---------|------------------------------|
| **Subject-oriented** | Organized around business subjects (sales, customers) not apps | App-oriented (order system, CRM) |
| **Integrated** | Consistent naming, units, and codes across sources | Each source has its own conventions |
| **Time-variant** | Keeps historical snapshots for trend analysis | Current state only |
| **Non-volatile** | Loaded then read; rarely updated/deleted | Constant INSERT/UPDATE/DELETE |

```
Operational Systems              Data Warehouse
+---------------+               +----------------+
| Order System  |               |   "Sales"      |
+---------------+     ETL/ELT    |  (customers,   |
| CRM System    |  ----------->  |   products,    |
+---------------+               |   regions,     |
| Inventory     |               |   time)        |
+---------------+               +----------------+
   app-oriented                    subject-oriented
   current only                    full history
```

### Warehouse vs Lake vs Lakehouse
These three terms get muddled constantly. The clean distinction is **schema-on-write vs schema-on-read** and **who cleans the data**.

| | Data Warehouse | Data Lake | Lakehouse |
|---|----------------|-----------|-----------|
| Stores | Structured, modeled tables | Raw files (any format) | Raw files + table layer |
| Schema | On write (defined up front) | On read (interpret later) | Hybrid |
| Data | Cleaned, conformed | Raw, messy, everything | Raw + curated zones |
| Users | Analysts, BI tools | Data scientists, engineers | Both |
| Cost/GB | Higher | Lower (object storage) | Lower |
| Example | BigQuery, Snowflake, Redshift | S3 / GCS + files | Databricks, BigLake, Iceberg |

```
   DATA LAKE                 DATA WAREHOUSE
+----------------+         +------------------+
| raw CSV/JSON   |  ETL    | modeled tables   |
| Parquet, logs  | ----->  | star schema      |
| images, blobs  | clean   | conformed dims   |
| "dump it all"  | model   | "query-ready"    |
+----------------+         +------------------+
        \                        /
         \      LAKEHOUSE       /
          +-------------------+
          | table format over |
          | cheap object store|
          | (Iceberg/Delta)   |
          +-------------------+
```

Rule of thumb: a **lake** is cheap storage for *everything, later*; a **warehouse** is curated storage for *analytics, now*. BigQuery is a warehouse, but with **BigLake / external tables** it can also query lake files in place (covered in note 405).

### OLTP vs OLAP: The Central Distinction
Two workload types drive two system designs.

- **OLTP — OnLine Transaction Processing.** Runs the business. Many small, fast writes and point lookups. Example: place an order, update inventory.
- **OLAP — OnLine Analytical Processing.** Analyzes the business. Few large, complex reads over history. Example: revenue by region by quarter.

| Aspect | OLTP | OLAP |
|--------|------|------|
| **Purpose** | Run the business | Analyze the business |
| **Users** | Apps, operational staff | Analysts, executives, BI tools |
| **Queries** | Simple, targeted (by PK) | Complex, aggregated, scans |
| **Data scope** | Current state | Historical |
| **Writes** | Frequent, real-time | Batch loads |
| **Response time** | Milliseconds | Seconds to minutes |
| **Concurrency** | Thousands of users | Dozens of users |
| **Schema** | Normalized (3NF) | Denormalized (star/snowflake) |
| **Storage** | Row-oriented | Column-oriented |
| **Optimize for** | Write throughput | Read/scan throughput |
| **Examples** | PostgreSQL, MySQL, Cloud SQL | BigQuery, Snowflake, Redshift |

The **row vs column storage** difference is the deepest one and it explains why BigQuery is fast. An analytical query like `SELECT region, SUM(revenue)` touches 2 columns out of 40. A **columnar** store reads only those 2 columns' data; a **row** store must read every row in full. This is why BigQuery (and its Capacitor format, note 402) is columnar.

```
ROW STORE (OLTP)                 COLUMN STORE (OLAP)
[id|name|region|rev|...]         id:     [1,2,3,4,...]
[id|name|region|rev|...]         name:   [a,b,c,d,...]
[id|name|region|rev|...]         region: [W,E,W,S,...]  <- read just this
[id|name|region|rev|...]         rev:    [10,5,8,3,...] <- and this
read whole rows to sum rev       read 2 columns, skip 38
```

### Example Queries Side by Side
```sql
-- OLTP: point lookup, uses an index, ~5ms
SELECT order_id, status, shipping_address
FROM orders
WHERE customer_id = 12345 AND order_id = 98765;
```

```sql
-- OLAP: wide aggregation over history, ~seconds, columnar scan
SELECT c.region, p.category, d.year,
       SUM(f.revenue) AS total_revenue,
       AVG(f.discount_percent) AS avg_discount
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
JOIN dim_product  p ON f.product_id  = p.product_id
JOIN dim_date     d ON f.date_id     = d.date_id
WHERE d.year IN (2023, 2024)
GROUP BY c.region, p.category, d.year
ORDER BY total_revenue DESC;
```

### How Data Flows: OLTP -> ETL/ELT -> OLAP
Warehouses do not collect data themselves; pipelines feed them. (This is Day 5's whole topic; here is the map.)

```
+-------------+     +-------------+     +--------------+
|  OLTP       |     |  ETL / ELT  |     |   OLAP       |
|  Systems    | --> |  Pipeline   | --> |   Warehouse  |
+-------------+     +-------------+     +--------------+
| Orders      |     | extract     |     | fact_sales   |
| Products    |     | transform   |     | dim_product  |
| Customers   |     | load        |     | dim_customer |
+-------------+     +-------------+     +--------------+
 write-heavy        nightly/hourly      read-heavy
 normalized         (batch/stream)      denormalized
```

- **ETL** = transform *before* load (classic; transform in a staging server).
- **ELT** = load raw *then* transform *inside* the warehouse (modern; BigQuery is powerful enough to do the T). We contrast these on Day 5.

### Data-Store Vendor Landscape
You will meet many of these in the field. The point is not to memorize them but to place BigQuery.

| Category | Vendors / products |
|----------|--------------------|
| **Cloud data warehouses (OLAP)** | **BigQuery** (GCP), Redshift (AWS), Snowflake (multi-cloud), Synapse (Azure) |
| **Relational OLTP (RDBMS)** | PostgreSQL, MySQL, SQL Server, Oracle, Cloud SQL, Aurora |
| **NoSQL — key-value / wide-column** | Bigtable, DynamoDB, Cassandra, Redis |
| **NoSQL — document** | MongoDB, Firestore, Couchbase |
| **Lake / object storage** | GCS, Amazon S3, Azure Blob (often + Parquet/Iceberg) |
| **Lakehouse / query engines** | Databricks, Athena, Presto/Trino, DuckDB (local!) |

Where BigQuery fits: **serverless cloud OLAP warehouse** on GCP. Its closest peers are Snowflake and Redshift. Its opposite is an OLTP RDBMS like Cloud SQL. For *local, offline* practice this week we use **DuckDB** — an in-process columnar OLAP engine that speaks nearly the same standard SQL, so nobody without cloud access is blocked. See note 402 for the BigQuery details and 407 for the DuckDB fallback.

## Code Example
A tiny, dependency-free illustration of the columnar vs row idea and OLTP/OLAP recommendation logic.

```python
from dataclasses import dataclass


@dataclass
class Workload:
    query_shape: str      # "point_lookup" | "aggregation"
    freshness: str        # "realtime" | "batch"
    scope: str            # "current" | "historical"


def recommend_system(w: Workload) -> str:
    """Toy heuristic: OLTP for transactions, OLAP for analytics."""
    olap = 0
    olap += w.query_shape == "aggregation"
    olap += w.freshness == "batch"
    olap += w.scope == "historical"
    return "OLAP (e.g. BigQuery)" if olap >= 2 else "OLTP (e.g. Cloud SQL)"


examples = [
    Workload("point_lookup", "realtime", "current"),    # order status
    Workload("aggregation", "batch", "historical"),     # quarterly revenue
]
for w in examples:
    print(f"{w} -> {recommend_system(w)}")
# Workload(...current) -> OLTP (e.g. Cloud SQL)
# Workload(...historical) -> OLAP (e.g. BigQuery)
```

## Key Takeaways
- A **data warehouse** is subject-oriented, integrated, time-variant, non-volatile — built to *analyze* the business.
- **Lake** = cheap raw storage (schema-on-read); **warehouse** = curated modeled tables (schema-on-write); **lakehouse** blends them.
- **OLTP** = many small fast writes, normalized, row storage; **OLAP** = few large reads, denormalized, **column storage**. Columnar storage is why analytical scans are cheap.
- Data flows OLTP -> **ETL/ELT** -> OLAP; ELT (transform in the warehouse) is the modern default and BigQuery's sweet spot.
- **BigQuery** is a serverless cloud OLAP warehouse; peers are Snowflake/Redshift; the local offline stand-in this week is **DuckDB**.

## Resources
- Inmon — building the data warehouse: <https://www.kimballgroup.com/>
- Data warehouse vs data lake (Google): <https://cloud.google.com/learn/what-is-a-data-warehouse>
- OLTP vs OLAP (Oracle): <https://www.oracle.com/database/what-is-oltp/>
- DuckDB (local OLAP): <https://duckdb.org/>
- Next: `402-what-is-bigquery.md`
