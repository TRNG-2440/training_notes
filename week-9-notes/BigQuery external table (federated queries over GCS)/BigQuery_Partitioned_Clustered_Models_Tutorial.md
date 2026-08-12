# 🚀 Partitioned and Clustered Models in BigQuery

> **Fresher-friendly guide with a simple real-world use case, BigQuery implementation, and dbt configuration**

---

## 📌 Quick Idea

In BigQuery, **partitioning** and **clustering** are techniques used to improve query performance and reduce the amount of data scanned.

```text
Without optimization

BIG SALES TABLE
-----------------------------------------
2026-01-01 | India | Electronics | 5000
2026-01-01 | USA   | Fashion     | 3000
2026-02-01 | India | Home        | 2500
2026-03-01 | UK    | Electronics | 7000
...millions of rows...
-----------------------------------------

Query:
"Give me India sales for March"

BigQuery may need to examine a large amount of data.
```

With partitioning and clustering:

```text
SALES TABLE

Partition: January
   India
   USA
   UK

Partition: February
   India
   USA
   UK

Partition: March
   India
   USA
   UK
```

If we query:

```text
March
+
India
```

BigQuery can first eliminate irrelevant date partitions and then skip many irrelevant storage blocks inside the selected partition.

> **Easy memory trick**
>
> - **Partitioning** → choose the large section of data
> - **Clustering** → narrow down further inside that section

---

<details open>
<summary><strong>1️⃣ What is Partitioning?</strong></summary>

A **partitioned table** divides one large table into smaller logical segments based on **one partitioning column**.

Most commonly, this is a:

```text
DATE
TIMESTAMP
DATETIME
```

For example:

```text
sales_date
```

Imagine your company stores five years of order data:

```text
500 million rows
```

Management asks:

> **"Show sales for August 2026."**

If `sales_date` is the partitioning column, BigQuery can read only the relevant August partition instead of scanning unrelated dates.

This is called **partition pruning**.

</details>

---

<details open>
<summary><strong>2️⃣ Simple Partition Example</strong></summary>

Suppose your table contains:

```text
order_id
order_date
customer_id
region
product_category
amount
```

Partition it using:

```text
order_date
```

Conceptually:

```text
SALES
 │
 ├── 2026-08-01
 │
 ├── 2026-08-02
 │
 ├── 2026-08-03
 │
 ├── 2026-08-04
 │
 └── ...
```

Then this query:

```sql
SELECT *
FROM `project.analytics.sales`
WHERE order_date = '2026-08-12';
```

can focus on that matching partition instead of scanning all dates.

</details>

---

<details open>
<summary><strong>3️⃣ What is Clustering?</strong></summary>

Clustering is different.

Instead of dividing the table into date partitions, **BigQuery organizes rows with similar values together in storage blocks based on selected columns**.

Example:

```text
cluster by region
```

Conceptually:

```text
INDIA rows
INDIA rows
INDIA rows

USA rows
USA rows

UK rows
UK rows
```

So when you query:

```sql
WHERE region = 'INDIA'
```

BigQuery can use clustering metadata to skip blocks that are unlikely to contain `INDIA`.

</details>

---

## 🆚 Partitioning vs Clustering

For freshers, remember:

```text
PARTITIONING
"What large section should I eliminate?"

Usually:
DATE / TIME


CLUSTERING
"Within that selected data,
how can I organize similar records?"

Usually:
customer_id
region
category
status
product_id
```

---

## 🛒 Best Real-World Example — E-Commerce Sales

Suppose raw orders contain:

```text
order_id
order_date
customer_id
customer_state
category
amount
status
```

Business users frequently ask:

```text
Sales this month

Sales for Karnataka

Electronics sales this month

Completed orders this month

Sales for a particular customer
```

A strong design could be:

```text
PARTITION BY
order_date

CLUSTER BY
customer_state,
category
```

Conceptually:

```text
                           SALES TABLE
                               │
                 Partition by order_date
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
       Aug 10               Aug 11               Aug 12
          │                    │                    │
          ▼                    ▼                    ▼
      clustered            clustered             clustered
       by state             by state              by state
          │                    │                    │
      KA/TN/MH/...         KA/TN/MH/...         KA/TN/MH/...
```

---

## 🧭 When Should I Use Partitioning?

Use partitioning when queries commonly filter by:

```text
Order date
Transaction date
Event date
Created date
Timestamp
```

Example:

```sql
WHERE order_date BETWEEN '2026-08-01'
                     AND '2026-08-12'
```

### Simple rule

> If most queries ask **"today"**, **"this month"**, **"last 7 days"**, or a particular date range, consider partitioning by date.

---

## 🧩 When Should I Use Clustering?

Use clustering when queries frequently filter or group by columns such as:

```text
customer_id
region
country
category
status
product_id
```

Example:

```sql
WHERE customer_state = 'KA'
```

or:

```sql
WHERE customer_state = 'KA'
AND category = 'ELECTRONICS'
```

The order of clustering columns matters.

For:

```text
CLUSTER BY customer_state, category
```

these are especially useful query patterns:

```sql
WHERE customer_state = 'KA'
```

and:

```sql
WHERE customer_state = 'KA'
AND category = 'ELECTRONICS'
```

---

## 🔗 Can We Use Both?

**Yes.**

This is often the most useful pattern.

```text
PARTITION BY order_date

CLUSTER BY
customer_state,
category
```

Suppose you ask:

> **"Give Electronics sales from Karnataka for August 12."**

BigQuery can conceptually do:

```text
Step 1

Skip all dates except Aug 12
        ↓
Partition pruning


Step 2

Inside Aug 12
skip unrelated state/category blocks
        ↓
Cluster block pruning
```

---

# 🧪 Hands-On Demo in GCP BigQuery

## Scenario

We will build:

```text
RAW ORDERS
    │
    ▼
SALES_ANALYTICS
```

Columns:

```text
order_id
order_date
customer_id
customer_state
category
amount
status
```

---

## Step 1 — Open BigQuery

Go to:

```text
Google Cloud Console
    ↓
BigQuery
    ↓
SQL Workspace
```

Use your training project.

Example:

```text
bigquery-optimization-lab
```

---

## Step 2 — Create Dataset

Create:

```text
partition_cluster_demo
```

Use the same BigQuery region you normally use.

---

## Step 3 — Create Raw Table

```sql
CREATE OR REPLACE TABLE
`YOUR_PROJECT.partition_cluster_demo.raw_orders`
(
    order_id INT64,
    order_date DATE,
    customer_id STRING,
    customer_state STRING,
    category STRING,
    amount NUMERIC,
    status STRING
);
```

---

## Step 4 — Insert Sample Data

```sql
INSERT INTO
`YOUR_PROJECT.partition_cluster_demo.raw_orders`
VALUES

(1001,'2026-08-10','C001','KA','ELECTRONICS',45000,'COMPLETED'),

(1002,'2026-08-10','C002','TN','FASHION',12000,'COMPLETED'),

(1003,'2026-08-10','C003','KA','HOME',8500,'COMPLETED'),

(1004,'2026-08-11','C004','MH','ELECTRONICS',35000,'COMPLETED'),

(1005,'2026-08-11','C005','KA','ELECTRONICS',22000,'CANCELLED'),

(1006,'2026-08-11','C006','TN','HOME',7000,'COMPLETED'),

(1007,'2026-08-12','C007','KA','ELECTRONICS',60000,'COMPLETED'),

(1008,'2026-08-12','C008','MH','FASHION',16000,'COMPLETED'),

(1009,'2026-08-12','C009','KA','FASHION',11000,'COMPLETED'),

(1010,'2026-08-12','C010','TN','ELECTRONICS',28000,'COMPLETED');
```

Check:

```sql
SELECT *
FROM `YOUR_PROJECT.partition_cluster_demo.raw_orders`;
```

---

## Step 5 — First Create a Normal Table

Create an unoptimized table for comparison:

```sql
CREATE OR REPLACE TABLE
`YOUR_PROJECT.partition_cluster_demo.sales_normal`
AS

SELECT *
FROM `YOUR_PROJECT.partition_cluster_demo.raw_orders`;
```

This is a normal table.

```text
No partition

No clustering
```

---

## Step 6 — Create Partitioned Table

```sql
CREATE OR REPLACE TABLE
`YOUR_PROJECT.partition_cluster_demo.sales_partitioned`

PARTITION BY order_date

AS

SELECT *
FROM `YOUR_PROJECT.partition_cluster_demo.raw_orders`;
```

Now:

```text
sales_partitioned
      │
      └── partitioned by
          order_date
```

---

## Step 7 — Query the Partitioned Table

```sql
SELECT
    customer_state,
    SUM(amount) AS total_sales

FROM
`YOUR_PROJECT.partition_cluster_demo.sales_partitioned`

WHERE order_date = '2026-08-12'

GROUP BY customer_state;
```

The important part:

```sql
WHERE order_date = '2026-08-12'
```

because `order_date` is the partitioning column.

BigQuery can prune the other date partitions.

---

## Step 8 — Show Students the Difference

Before clicking **Run**, BigQuery normally displays an estimate such as:

```text
This query will process ...
```

Compare:

### Normal table

```sql
SELECT *
FROM `sales_normal`
WHERE order_date = '2026-08-12';
```

### Partitioned table

```sql
SELECT *
FROM `sales_partitioned`
WHERE order_date = '2026-08-12';
```

> **Teaching note**
>
> With this tiny sample dataset, the difference may be negligible.  
> The optimization becomes important when the table contains millions or billions of records.

---

## Step 9 — Create Only a Clustered Table

```sql
CREATE OR REPLACE TABLE
`YOUR_PROJECT.partition_cluster_demo.sales_clustered`

CLUSTER BY customer_state, category

AS

SELECT *
FROM
`YOUR_PROJECT.partition_cluster_demo.raw_orders`;
```

---

## Step 10 — Query Clustered Table

```sql
SELECT *

FROM
`YOUR_PROJECT.partition_cluster_demo.sales_clustered`

WHERE customer_state = 'KA';
```

Since:

```text
customer_state
```

is the first clustered column, this query matches the clustering design well.

---

## Step 11 — Create Partitioned + Clustered Table

Now create the most useful version:

```sql
CREATE OR REPLACE TABLE
`YOUR_PROJECT.partition_cluster_demo.sales_optimized`

PARTITION BY order_date

CLUSTER BY
    customer_state,
    category

AS

SELECT *
FROM
`YOUR_PROJECT.partition_cluster_demo.raw_orders`;
```

Architecture:

```text
sales_optimized
      │
      ├── PARTITION
      │      order_date
      │
      └── CLUSTER
             customer_state
             category
```

---

## Step 12 — Query the Optimized Table

```sql
SELECT

    customer_state,

    category,

    COUNT(*) AS total_orders,

    SUM(amount) AS total_sales

FROM
`YOUR_PROJECT.partition_cluster_demo.sales_optimized`

WHERE
    order_date = '2026-08-12'

    AND customer_state = 'KA'

    AND category = 'ELECTRONICS'

GROUP BY

    customer_state,

    category;
```

Conceptually BigQuery does:

```text
All data
   │
   ▼
Filter partition
2026-08-12
   │
   ▼
Find blocks for
KA
   │
   ▼
Find relevant
ELECTRONICS records
   │
   ▼
Return result
```

---

## 👀 Where Can I See Partition Details?

In BigQuery:

```text
Explorer
   ↓
Dataset
   ↓
sales_optimized
   ↓
Details
```

Look for:

```text
Partitioned by

Clustered by
```

You should see conceptually:

```text
Partitioned by:
order_date

Clustered by:
customer_state,
category
```

---

# 🛠️ How This Relates to dbt

Suppose you're using:

```text
dbt
+
BigQuery
```

You don't have to manually run `CREATE TABLE ... PARTITION BY ...` for every dbt model.

You can configure the model.

Conceptually:

```text
dbt model
   │
   ├── materialized = table
   ├── partition_by = order_date
   └── cluster_by = customer_state, category
           │
           ▼
      BigQuery table
```

A dbt BigQuery model might be configured like:

```sql
{{
    config(
        materialized='table',

        partition_by={
            "field": "order_date",
            "data_type": "date",
            "granularity": "day"
        },

        cluster_by=[
            "customer_state",
            "category"
        ]
    )
}}
```

Then:

```sql
SELECT

    order_id,
    order_date,
    customer_id,
    customer_state,
    category,
    amount,
    status

FROM {{ ref('stg_orders') }}
```

Now dbt builds the BigQuery table with the optimization configuration.

---

## ✅ Complete dbt Example

Create:

```text
models/marts/sales_analytics.sql
```

```sql
{{
    config(

        materialized='table',

        partition_by={
            "field": "order_date",
            "data_type": "date",
            "granularity": "day"
        },

        cluster_by=[
            "customer_state",
            "category"
        ]

    )
}}


SELECT

    order_id,

    order_date,

    customer_id,

    customer_state,

    category,

    amount,

    status

FROM {{ ref('stg_orders') }}
```

When the dbt model is executed, BigQuery creates the relation using those optimization settings.

---

# ⚠️ Why Not Partition Everything?

Partitioning isn't automatically better for every table.

```text
Small lookup table
100 rows

Don't partition it.


Massive sales table
500 million rows

Partitioning may help.
```

> Partitioning is most useful when the table is large enough and queries consistently filter by the partition column.

---

# ⚠️ Why Not Cluster Every Column?

Clustering columns should match **real query patterns**.

If users frequently query:

```sql
WHERE customer_state = ...
AND category = ...
```

then:

```text
customer_state
category
```

are reasonable clustering choices.

But clustering by:

```text
customer_name
description
email
phone
```

may not be useful unless those fields genuinely appear frequently in selective filters or aggregations.

---

# 🧠 Easy Student Comparison

```text
PARTITION

Think:
Bookshelf

January shelf
February shelf
March shelf

If I need March,
I go directly to March.


CLUSTER

Think:
Inside March shelf

India books together
USA books together
UK books together

If I need March + India,
I narrow down even more.
```

---

# 🌍 Real-World Query

Suppose the company stores:

```text
5 TB sales table
```

Management asks:

> **"Give me Electronics sales from Karnataka for August 2026."**

Without optimization:

```text
Potentially huge scan
```

With:

```text
PARTITION BY order_date
CLUSTER BY customer_state, category
```

BigQuery can first restrict the relevant August data and then prune blocks using the clustered fields.

---

# 📊 Partition vs Cluster vs Both

| Requirement | Best Choice |
|---|---|
| Queries mostly filter by date | Partition |
| Queries mostly filter by customer/category | Cluster |
| Queries filter by date + dimensions | Partition + Cluster |
| Small lookup table | Neither |
| Huge event table | Usually Partition |
| Huge event table queried by date and user | Partition + Cluster |

---

# 🎓 Final Teaching Flow

```text
1. Create normal table
          ↓
2. Run date query
          ↓
3. Create partitioned table
          ↓
4. Run same date query
          ↓
5. Explain partition pruning
          ↓
6. Create clustered table
          ↓
7. Query by state
          ↓
8. Explain block pruning
          ↓
9. Create partition + cluster table
          ↓
10. Query using date + state + category
          ↓
11. Show Details tab
          ↓
12. Finally show same idea in dbt config
```

---

## ⭐ Final Takeaway

> **Partitioning helps BigQuery choose which large section of the table to scan; clustering helps BigQuery narrow the scan further inside the relevant data.**

---

### Suggested Reference

Google Cloud BigQuery documentation:
- Partitioned tables
- Querying partitioned tables
- Clustered tables
- Querying clustered tables
