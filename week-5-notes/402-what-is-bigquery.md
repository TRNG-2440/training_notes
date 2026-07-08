# What Is BigQuery

## Learning Objectives
- Define BigQuery and its place in the analytics landscape.
- Explain what **serverless** means and why it changes the operating model.
- Name the four architectural pillars — **Dremel, Colossus, Capacitor, Jupiter** — and what each does.
- Explain the **separation of storage and compute** and why it matters for cost and scale.
- Decide **when to use** BigQuery and **when not to**.

## Why This Matters
Yesterday (Day 3) you learned cloud and big-data fundamentals in the abstract. BigQuery is where those abstractions become a tool you actually type SQL into. It is Google Cloud's flagship analytics engine and one of the most widely used cloud warehouses in the industry — so it appears constantly on data-engineering job descriptions.

The reason BigQuery feels different from a database is architectural: it is **serverless** and it **separates storage from compute**. Understand those two ideas and everything else — the pricing, the speed on petabytes, the "no cluster to size" experience — follows. Get them wrong and you will either overspend or reach for BigQuery when a plain database was the right call.

## Concept Explanation

### What Is BigQuery?
> BigQuery is a fully managed, **serverless**, highly scalable cloud data warehouse that runs standard SQL over datasets from gigabytes to petabytes — with no infrastructure to manage.

You do not provision servers, size a cluster, install patches, or tune disks. You create datasets and tables, then run SQL. Google runs the machines.

```
Data Sources                BigQuery                 Consumption
+-------------+           +-----------+              +--------------+
| Apps / DBs  |  ETL/ELT  |           |   SQL query  | BI (Looker)  |
| Files (GCS) | --------> | BigQuery  | <----------  | Dashboards   |
| Streaming   |           |           |              | pandas / ML  |
+-------------+           +-----------+              +--------------+
```

### What "Serverless" Really Means
"Serverless" does not mean there are no servers — it means *you never see them*. Compare with a traditional warehouse (or a self-managed database):

| Aspect | Traditional DWH / DB | BigQuery |
|--------|----------------------|----------|
| Provisioning | You size and buy clusters | None — just run SQL |
| Scaling | Manual or scheduled | Automatic per query |
| Patching / upgrades | Your team | Google |
| Idle cost | Pay for the running cluster | Pay for **storage only** |
| Capacity planning | Constant chore | Not your problem |

Practical upshot: a query that needs 2,000 CPUs gets them for the seconds it runs, then they go back to the pool. You pay for the bytes that query scanned, not for a machine sitting idle overnight.

### The Four Architectural Pillars
BigQuery is built on four Google technologies. You will not interact with them directly, but naming them explains *why* it is fast and cheap.

```
+-----------------------------------------------------------+
|                     BigQuery                               |
|                                                           |
|   COMPUTE                          STORAGE                 |
|   +---------------------+          +--------------------+  |
|   | Dremel query engine |  <-----> | Capacitor format   |  |
|   | (slots do the work) |          | (columnar files)   |  |
|   +----------+----------+          +---------+----------+  |
|              |                               |             |
|              |        Jupiter network        |             |
|              +-------- (petabit fabric)-------+             |
|                              |                             |
|                     +--------v---------+                   |
|                     |    Colossus      |                   |
|                     | (distributed FS) |                   |
|                     +------------------+                   |
+-----------------------------------------------------------+
```

| Pillar | Role | Why it matters |
|--------|------|----------------|
| **Dremel** | Distributed query engine; breaks a query into a tree of thousands of workers ("slots") | Massive parallelism -> petabyte scans in seconds |
| **Colossus** | Google's distributed file system; durable, replicated storage | Your data is safe and separate from compute |
| **Capacitor** | Columnar, compressed on-disk format | Reads only the columns a query needs -> less bytes scanned -> cheaper |
| **Jupiter** | Google's ultra-fast datacenter network | Lets separated storage & compute talk at petabit speed |

The key insight: because **Jupiter** is so fast, storage (Colossus) and compute (Dremel slots) do **not** need to live on the same machine. That is what makes the separation below possible.

### Separation of Storage and Compute
In a classic database, storage and CPU are welded together in one server — scale one and you pay for both. BigQuery splits them.

```
   STORAGE (Colossus)              COMPUTE (Dremel slots)
+----------------------+        +------------------------+
| Your tables, always  |        | Query workers, on      |
| resident, columnar   | <----> | demand, ephemeral      |
| Pay per GB / month   |        | Pay per query (bytes   |
|                      |        | scanned) or per slot   |
+----------------------+        +------------------------+
      grows slowly                spikes per workload
```

Benefits:
- **Store cheaply, forever.** Storage is priced like object storage; keeping history is affordable.
- **Scale compute independently.** A heavy report spins up thousands of slots without touching storage.
- **No over-provisioning.** Idle at 3am? You pay only storage, no compute.
- **Many consumers, one copy.** Ten teams can query the same table concurrently, each getting their own slots.

### Key Features (at a glance)
- **Standard SQL** (GoogleSQL, SQL:2011-compliant) — you already know most of it.
- **BigQuery ML** — train models with `CREATE MODEL ... AS SELECT ...` (SQL, no export).
- **Streaming inserts / Storage Write API** — near-real-time ingestion.
- **External / federated tables** — query GCS, Sheets, Cloud SQL in place, no load (note 405).
- **Partitioning & clustering** — prune scanned bytes to cut cost (notes 405, 406).
- **Public datasets** — `bigquery-public-data.*`, e.g. `thelook_ecommerce`, free to query (within the 1 TB/month free tier).

### When to Use BigQuery — and When Not
| Use BigQuery when... | Reach for something else when... |
|----------------------|----------------------------------|
| Large-scale analytics / BI over history | You need sub-second single-row lookups -> **Bigtable / Redis** |
| Ad-hoc exploration across big tables | Heavy transactional writes (OLTP) -> **Cloud SQL / Spanner** |
| ELT: transform inside the warehouse | Tiny datasets where a laptop suffices -> **DuckDB / SQLite** |
| ML on structured data (BQML) | Streaming event *processing* logic -> **Dataflow / Pub-Sub** |
| Many analysts querying one shared copy | You must avoid all cloud/billing setup -> **DuckDB (this week's fallback)** |

A blunt rule: **BigQuery is an OLAP warehouse, not a database.** If you find yourself wanting to `UPDATE` single rows thousands of times per second, you picked the wrong tool.

### The Free Sandbox and the Local Fallback
Two ways to follow along this week, both zero-cost:

1. **BigQuery sandbox** — no credit card. Sign in with a Google account, get 10 GB storage + **1 TB of query processing free per month**. Query `bigquery-public-data` immediately. See <https://cloud.google.com/bigquery/docs/sandbox>.
2. **DuckDB** — `pip install duckdb`, runs entirely on your laptop, speaks nearly identical standard SQL. Use it if you cannot get cloud access. Notes flag where syntax differs (backtick `project.dataset.table`, `_PARTITIONTIME`, dry-run costing).

## Code Example
Your first BigQuery query in Python — and the DuckDB equivalent, so you can run one of them today.

```python
# --- Real BigQuery (needs sandbox + `pip install google-cloud-bigquery db-dtypes`) ---
from google.cloud import bigquery

client = bigquery.Client()  # uses Application Default Credentials
sql = """
    SELECT category, COUNT(*) AS n
    FROM `bigquery-public-data.thelook_ecommerce.products`
    GROUP BY category
    ORDER BY n DESC
    LIMIT 5
"""
df = client.query(sql).to_dataframe()
print(df)
```

```python
# --- DuckDB fallback (needs only `pip install duckdb pandas`) ---
import duckdb

con = duckdb.connect()  # in-memory
con.execute("""
    CREATE TABLE products AS
    SELECT * FROM (VALUES
        ('Jeans'), ('Tops'), ('Jeans'), ('Shoes'), ('Tops'), ('Tops')
    ) AS t(category)
""")
df = con.execute("""
    SELECT category, COUNT(*) AS n
    FROM products
    GROUP BY category
    ORDER BY n DESC
    LIMIT 5
""").df()
print(df)
```

Notice the SQL body is nearly identical. The BigQuery-specific piece is the **backtick-quoted fully qualified name** `` `project.dataset.table` ``; DuckDB just uses a bare table name. That is the pattern for the whole day: same SQL, different table addressing and cost model.

## Key Takeaways
- BigQuery is a **serverless** cloud OLAP warehouse — you run SQL, Google runs the machines.
- Four pillars: **Dremel** (compute/slots), **Colossus** (storage), **Capacitor** (columnar format), **Jupiter** (network).
- **Storage and compute are separated** — store cheaply forever, scale compute per query, pay nothing for idle compute.
- Great for **large-scale analytics, ad-hoc exploration, ELT, BQML**; wrong for **single-row lookups and heavy OLTP writes**.
- Practice free via the **sandbox** (1 TB/month) or entirely offline via **DuckDB**.

## Resources
- BigQuery overview: <https://cloud.google.com/bigquery/docs/introduction>
- Sandbox (no card): <https://cloud.google.com/bigquery/docs/sandbox>
- Dremel paper: <https://research.google/pubs/pub36632/>
- Under the hood (BigQuery architecture): <https://cloud.google.com/blog/products/bigquery/bigquery-under-the-hood>
- Prev: `401-data-warehousing-oltp-vs-olap.md` · Next: `403-bigquery-datasets-tables-and-types.md`
