<style>
:root {
  --bg: #ffffff;
  --panel: #f7f9fc;
  --border: #dfe5ec;
  --text: #1f2937;
  --muted: #5b6472;
  --accent: #2563eb;
}
body {
  color: var(--text);
  background: var(--bg);
  line-height: 1.6;
}
.layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.sidebar {
  width: 250px;
  min-width: 250px;
  position: sticky;
  top: 16px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.content {
  flex: 1;
  min-width: 0;
}
.sidebar a {
  text-decoration: none;
}
details {
  margin: 10px 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
}
summary {
  cursor: pointer;
  font-weight: 600;
}
h1, h2, h3 {
  color: var(--accent);
}
blockquote {
  border-left: 4px solid var(--accent);
  padding-left: 12px;
  color: var(--muted);
}
@media (max-width: 800px) {
  .layout { display: block; }
  .sidebar {
    width: auto;
    min-width: 0;
    position: static;
    margin-bottom: 16px;
  }
}
</style>

# Federated Queries over GCS with BigQuery

> Query files stored in Google Cloud Storage directly from BigQuery without first loading them into a normal BigQuery table.

<div class="layout">

<div class="sidebar">

<details open>
<summary>Navigation</summary>

- [Concept](#concept)
- [Setup Required](#setup-required)
- [Demo Architecture](#demo-architecture)
- [Sample Dataset](#sample-dataset)
- [Implementation Steps](#implementation-steps)
- [Business Queries](#business-queries)
- [Multiple Files](#multiple-files)
- [External vs Native](#external-vs-native)
- [Real-World Use](#real-world-use)
- [Teaching Flow](#teaching-flow)
- [Terminology Note](#terminology-note)

</details>

</div>

<div class="content">

<a id="concept"></a>
<details open>
<summary>1. What is a federated query over GCS?</summary>

For a fresher-friendly explanation:

**The data stays in Google Cloud Storage, while BigQuery queries it through an external table.**

Normal approach:

```text
GCS
 ↓
Load Data
 ↓
BigQuery Native Table
 ↓
SQL Query
```

External-table approach:

```text
GCS
 ↓
BigQuery External Table
 ↓
SQL Query
```

The CSV, JSON, Parquet, Avro, or ORC file physically remains in GCS.

</details>

<a id="setup-required"></a>
<details>
<summary>2. Setup Required</summary>

For a simple classroom demo, you need:

| Component | Purpose |
|---|---|
| Google Cloud Project | Contains the resources |
| GCS Bucket | Stores the source file |
| BigQuery Dataset | Holds the external-table definition |
| External Table | Points to the GCS file |
| BigQuery SQL Editor | Runs queries |

Keep the GCS bucket and BigQuery dataset in a compatible location.

For a beginner demo, using the same project and the same location keeps the setup simple.

</details>

<a id="demo-architecture"></a>
<details>
<summary>3. Recommended Demo Architecture</summary>

```text
Google Cloud Project
│
├── Cloud Storage
│   └── federated-demo-bucket
│       └── sales
│           └── sales.csv
│
└── BigQuery
    └── federated_demo
        └── ext_sales
```

`ext_sales` does not contain a copied version of the CSV.

It points to the file stored in GCS.

</details>

<a id="sample-dataset"></a>
<details>
<summary>4. Sample Dataset</summary>

Create a file named:

```text
sales.csv
```

Use:

```csv
order_id,customer_name,product,category,quantity,price,region
1001,Asha,Laptop,Electronics,1,65000,South
1002,Ravi,Phone,Electronics,2,30000,North
1003,Meena,Chair,Furniture,4,5000,South
1004,John,Monitor,Electronics,2,18000,West
1005,Priya,Table,Furniture,1,12000,South
1006,Arun,Keyboard,Electronics,3,2500,East
1007,Sneha,Phone,Electronics,1,32000,West
1008,David,Chair,Furniture,2,5500,North
```

</details>

<a id="implementation-steps"></a>
<details open>
<summary>5. Implementation Steps</summary>

### Step 1 — Create a GCS bucket

Navigate to:

```text
Google Cloud Console
→ Cloud Storage
→ Buckets
→ Create
```

Example:

```text
Bucket name:
ragav-federated-demo-unique

Storage class:
Standard
```

Choose an appropriate location and create the bucket.

### Step 2 — Upload the CSV

Create a folder:

```text
sales
```

Upload:

```text
sales.csv
```

The file path will look like:

```text
gs://YOUR_BUCKET_NAME/sales/sales.csv
```

### Step 3 — Create a BigQuery dataset

Navigate to:

```text
BigQuery
→ Explorer
→ Your Project
→ Create Dataset
```

Example:

```text
Dataset ID:
federated_demo
```

Use a compatible location with the GCS bucket.

### Step 4 — Create the external table

Inside BigQuery:

```text
federated_demo
→ Create Table
```

Configure:

```text
Create table from:
Google Cloud Storage

File:
gs://YOUR_BUCKET_NAME/sales/sales.csv

File format:
CSV
```

Destination:

```text
Dataset:
federated_demo

Table:
ext_sales

Table type:
External table
```

For the beginner demo, enable schema auto-detection.

Create the table.

### Step 5 — Query it

```sql
SELECT *
FROM `YOUR_PROJECT.federated_demo.ext_sales`;
```

The records are returned even though the source data remains in GCS.

</details>

<a id="business-queries"></a>
<details>
<summary>6. Simple Business Queries</summary>

### Total sales by region

```sql
SELECT
    region,
    SUM(quantity * price) AS total_sales
FROM `YOUR_PROJECT.federated_demo.ext_sales`
GROUP BY region
ORDER BY total_sales DESC;
```

### Electronics orders

```sql
SELECT
    order_id,
    customer_name,
    product,
    quantity,
    price
FROM `YOUR_PROJECT.federated_demo.ext_sales`
WHERE category = 'Electronics';
```

### Revenue by category

```sql
SELECT
    category,
    COUNT(*) AS number_of_orders,
    SUM(quantity) AS total_quantity,
    SUM(quantity * price) AS revenue
FROM `YOUR_PROJECT.federated_demo.ext_sales`
GROUP BY category;
```

</details>

<details>
<summary>7. Best Classroom Demonstration — Change the GCS File</summary>

Add another row to the CSV:

```csv
1009,Rahul,Tablet,Electronics,2,25000,East
```

Upload the updated file back to the same GCS path.

Run:

```sql
SELECT *
FROM `YOUR_PROJECT.federated_demo.ext_sales`;
```

Now explain:

```text
GCS file changed
      ↓
External table still points to the file
      ↓
BigQuery queries the latest underlying data
```

You did not manually load the new row into a native BigQuery table.

</details>

<details>
<summary>8. Create the External Table Using SQL</summary>

```sql
CREATE OR REPLACE EXTERNAL TABLE
`YOUR_PROJECT.federated_demo.ext_sales`
(
    order_id INT64,
    customer_name STRING,
    product STRING,
    category STRING,
    quantity INT64,
    price NUMERIC,
    region STRING
)
OPTIONS
(
    format = 'CSV',
    uris = ['gs://YOUR_BUCKET_NAME/sales/sales.csv'],
    skip_leading_rows = 1
);
```

Then:

```sql
SELECT *
FROM `YOUR_PROJECT.federated_demo.ext_sales`;
```

</details>

<a id="multiple-files"></a>
<details>
<summary>9. Query Multiple Files</summary>

A real data lake may contain:

```text
sales/
├── sales_20260810.csv
├── sales_20260811.csv
└── sales_20260812.csv
```

Create an external table using a wildcard:

```sql
CREATE OR REPLACE EXTERNAL TABLE
`YOUR_PROJECT.federated_demo.ext_sales_all`
(
    order_id INT64,
    customer_name STRING,
    product STRING,
    category STRING,
    quantity INT64,
    price NUMERIC,
    region STRING
)
OPTIONS
(
    format = 'CSV',
    uris = ['gs://YOUR_BUCKET_NAME/sales/*.csv'],
    skip_leading_rows = 1
);
```

Query:

```sql
SELECT *
FROM `YOUR_PROJECT.federated_demo.ext_sales_all`;
```

This is useful when new files arrive regularly in the same folder.

</details>

<a id="external-vs-native"></a>
<details>
<summary>10. External Table vs Native BigQuery Table</summary>

| Native BigQuery Table | GCS External Table |
|---|---|
| Data stored in BigQuery | Data remains in GCS |
| Data must be loaded | No initial data load |
| Better for repeated analytics | Useful for direct data-lake access |
| Usually faster | Can be slower |
| Supports normal table operations | Primarily used for querying external data |
| BigQuery manages storage | GCS manages source storage |

Easy rule:

```text
Exploration / Raw Data
        ↓
External Table

Repeated Production Analytics
        ↓
Native BigQuery Table
```

</details>

<a id="real-world-use"></a>
<details>
<summary>11. Real-World Use Case</summary>

Imagine applications generate daily files:

```text
Applications
     ↓
CSV / JSON / Parquet
     ↓
GCS Data Lake
     ↓
BigQuery External Tables
     ↓
Exploration / Validation
     ↓
Important Data
     ↓
Native BigQuery Tables
     ↓
Dashboards / Reporting
```

A company can keep large amounts of raw data in GCS and query only what is required.

</details>

<details>
<summary>12. CSV vs Parquet</summary>

For a first demo:

```text
CSV
↓
Easy for students to open and understand
```

For production analytical workloads:

```text
Parquet
↓
Column-oriented format
↓
Often better suited to analytics
```

Start with CSV and introduce Parquet afterward.

</details>

<a id="terminology-note"></a>
<details>
<summary>13. Important Terminology Note</summary>

In casual training discussions, people may say:

```text
Federated query over GCS
```

The more precise BigQuery implementation is:

```text
GCS
 ↓
BigQuery External Table
```

BigQuery also uses the term **federated query** for querying supported external databases through connections and functions such as:

```text
EXTERNAL_QUERY()
```

So for interviews, remember:

```text
GCS → External Table

Cloud SQL / Spanner / supported databases
→ Federated Query / EXTERNAL_QUERY()
```

</details>

<a id="teaching-flow"></a>
<details open>
<summary>14. Recommended Teaching Flow</summary>

1. Show `sales.csv`.
2. Upload it into GCS.
3. Show that no native sales table exists in BigQuery.
4. Create `federated_demo`.
5. Create `ext_sales`.
6. Run `SELECT *`.
7. Run a revenue query.
8. Modify the CSV in GCS.
9. Query again.
10. Demonstrate `sales/*.csv`.
11. Compare external and native tables.

Final message for students:

> **The file stays in GCS. BigQuery can query it through an external table without first loading it into native BigQuery storage.**

</details>

## Final Flow

```text
WITHOUT EXTERNAL TABLE

GCS
 ↓
Load
 ↓
BigQuery Native Table
 ↓
SQL


WITH EXTERNAL TABLE

GCS
 ↓
BigQuery External Table
 ↓
SQL
```

For this basic demonstration, you do not need Dataflow, Dataproc, a VM, Cloud SQL, or the `gcloud` CLI.

</div>
</div>
