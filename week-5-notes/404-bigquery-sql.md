# BigQuery SQL

## Learning Objectives
- Write BigQuery **standard SQL** (GoogleSQL): `SELECT / WHERE / GROUP BY / HAVING / JOIN`, subqueries, and CTEs.
- Apply BigQuery's built-in **functions**: date/time, string, aggregate, and **window** functions.
- Work with nested data using **`ARRAY_AGG`** and **`UNNEST`**.
- Translate each pattern to its **DuckDB** equivalent for offline practice.

## Why This Matters
You already know SQL — JOINs, GROUP BY, subqueries. BigQuery does not ask you to relearn it; GoogleSQL is standard SQL. What *is* new is a handful of powerful functions (especially windows and array handling) and BigQuery's dialect details. This note is the working reference you will keep open during today's lab. Because it is 90% standard SQL, almost everything here also runs in **DuckDB** unchanged — the differences are small and flagged inline.

## Concept Explanation

### The Standard Clauses (recap, BigQuery flavor)
The clause order and logical evaluation order are the same you know:

```sql
SELECT   c.region, SUM(f.revenue) AS total_revenue   -- 5. project
FROM     `proj.sales.fact_sales` f                    -- 1. from
JOIN     `proj.sales.dim_customer` c                  -- 1. join
  ON     f.customer_id = c.customer_id
WHERE    f.created_at >= '2024-01-01'                 -- 2. filter rows
GROUP BY c.region                                     -- 3. group
HAVING   SUM(f.revenue) > 10000                       -- 4. filter groups
ORDER BY total_revenue DESC                           -- 6. sort
LIMIT    10;                                           -- 7. limit
```

The only BigQuery-specific syntax above is the backtick-quoted `` `proj.sales.fact_sales` ``. In DuckDB, drop the backticks and use plain names.

BigQuery convenience: you can `GROUP BY` and `ORDER BY` a **SELECT alias** or **position** (`GROUP BY region` or `GROUP BY 1`). DuckDB supports this too.

### JOINs
All standard join types work: `INNER`, `LEFT`, `RIGHT`, `FULL`, `CROSS`. One BigQuery idiom to know: **`CROSS JOIN UNNEST(...)`** (or the comma form) to flatten arrays — see the nested section.

```sql
SELECT o.order_id, u.email
FROM `bigquery-public-data.thelook_ecommerce.orders` o
LEFT JOIN `bigquery-public-data.thelook_ecommerce.users` u
  ON o.user_id = u.id;
```

### Subqueries and CTEs
CTEs (`WITH`) keep multi-step analytics readable — prefer them over deeply nested subqueries.

```sql
WITH monthly AS (
  SELECT
    FORMAT_DATE('%Y-%m', DATE(created_at)) AS month,
    SUM(sale_price) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  WHERE created_at >= '2023-01-01'
  GROUP BY month
)
SELECT month, revenue,
       revenue - LAG(revenue) OVER (ORDER BY month) AS mom_change
FROM monthly
ORDER BY month;
```
> DuckDB: identical. `WITH`, `LAG`, `FORMAT_DATE`... wait — `FORMAT_DATE` differs (see below).

### Function Reference

#### Date / Time
| Task | BigQuery | DuckDB equivalent |
|------|----------|-------------------|
| Current date | `CURRENT_DATE()` | `current_date` |
| Extract part | `EXTRACT(YEAR FROM ts)` | same |
| Format to string | `FORMAT_DATE('%Y-%m', d)` | `strftime(d, '%Y-%m')` |
| Truncate | `DATE_TRUNC(d, MONTH)` | `date_trunc('month', d)` |
| Add interval | `DATE_ADD(d, INTERVAL 7 DAY)` | `d + INTERVAL 7 DAY` |
| Diff | `DATE_DIFF(d1, d2, DAY)` | `date_diff('day', d2, d1)` |
| Timestamp math | `TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)` | `now() - INTERVAL 30 DAY` |

The **date functions are the most common dialect gap** between BigQuery and DuckDB. When a query fails to port, look here first.

#### String
| Task | BigQuery | DuckDB |
|------|----------|--------|
| Concatenate | `CONCAT(a, b)` or `a \|\| b` | same |
| Upper/lower | `UPPER(s)`, `LOWER(s)` | same |
| Substring | `SUBSTR(s, 1, 3)` | same |
| Length | `LENGTH(s)` | same |
| Contains | `s LIKE '%x%'`, `REGEXP_CONTAINS(s, r'x')` | `LIKE`, `regexp_matches(s,'x')` |
| Split | `SPLIT(s, ',')` -> ARRAY | `string_split(s, ',')` |

#### Aggregate
`COUNT`, `SUM`, `AVG`, `MIN`, `MAX` as expected, plus BigQuery favorites:
```sql
SELECT
  COUNT(DISTINCT user_id)                    AS uniques,
  APPROX_COUNT_DISTINCT(user_id)             AS approx_uniques, -- fast, cheap
  COUNTIF(sale_price > 100)                  AS pricey_items,   -- conditional count
  ARRAY_AGG(product_id LIMIT 5)              AS sample_products,
  STRING_AGG(DISTINCT category, ', ')        AS categories
FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
JOIN `bigquery-public-data.thelook_ecommerce.products` p
  ON oi.product_id = p.id;
```
> DuckDB: `count_if` -> use `count(*) FILTER (WHERE ...)`; `ARRAY_AGG` -> `list()`; `STRING_AGG` -> `string_agg()`. No `APPROX_COUNT_DISTINCT` needed offline (data is small) — use `COUNT(DISTINCT ...)`.

#### Window Functions
Windows compute across a set of rows *related to the current row* without collapsing them — essential for running totals, ranks, and moving averages. Syntax is standard SQL and identical in DuckDB.

```sql
SELECT
  DATE(created_at) AS day,
  SUM(sale_price)  AS daily_rev,
  -- running total
  SUM(SUM(sale_price)) OVER (ORDER BY DATE(created_at))                          AS running_total,
  -- 7-day moving average
  AVG(SUM(sale_price)) OVER (ORDER BY DATE(created_at)
                             ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)           AS ma7,
  -- rank days by revenue
  RANK() OVER (ORDER BY SUM(sale_price) DESC)                                    AS rev_rank
FROM `bigquery-public-data.thelook_ecommerce.order_items`
WHERE created_at >= '2023-01-01'
GROUP BY day
ORDER BY day;
```

Common window functions: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()/LEAD()`, `FIRST_VALUE()/LAST_VALUE()`, `NTILE(n)`, and any aggregate used with `OVER (...)`. Use `PARTITION BY` to restart the window per group:

```sql
-- rank products within each category
SELECT category, name, total_sales,
       RANK() OVER (PARTITION BY category ORDER BY total_sales DESC) AS rank_in_cat
FROM product_totals;
```

### Nested Data: ARRAY_AGG and UNNEST
This is BigQuery's signature. Two directions:

**Flat -> nested** with `ARRAY_AGG(STRUCT(...))`:
```sql
SELECT order_id,
       ARRAY_AGG(STRUCT(product_id, sale_price)) AS items
FROM `bigquery-public-data.thelook_ecommerce.order_items`
GROUP BY order_id;
```

**Nested -> flat** with `UNNEST` (comma-join the array like a table):
```sql
SELECT o.order_id, item.product_id, item.sale_price
FROM my_nested_orders AS o,
     UNNEST(o.items) AS item;               -- one output row per array element
```

`UNNEST` is also handy for turning a literal array into rows, and for filtering "does this array contain X":
```sql
SELECT * FROM `proj.sales.orders`
WHERE EXISTS (SELECT 1 FROM UNNEST(items) i WHERE i.product_id = 42);
```
> DuckDB: `list(struct_pack(...))` builds nested; `UNNEST(items)` flattens. The comma-`UNNEST` join pattern works the same way.

## Code Example
A complete, realistic analytical query combining CTEs, joins, aggregates, and a window function — the kind you will write in the lab. Runnable against the public dataset (BigQuery) with the noted DuckDB tweaks.

```sql
-- BigQuery: top 3 products by revenue within each category, 2023
WITH product_rev AS (
  SELECT
    p.category,
    p.name,
    SUM(oi.sale_price) AS revenue,
    COUNT(*)           AS units
  FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
  JOIN `bigquery-public-data.thelook_ecommerce.products` p
    ON oi.product_id = p.id
  WHERE oi.created_at BETWEEN '2023-01-01' AND '2023-12-31'
  GROUP BY p.category, p.name
),
ranked AS (
  SELECT *,
         RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rnk
  FROM product_rev
)
SELECT category, name, revenue, units
FROM ranked
WHERE rnk <= 3
ORDER BY category, revenue DESC;
```

To run the same logic in DuckDB against a local `order_items` / `products` table: remove the backticks and fully qualified names, and (if you used any) swap `FORMAT_DATE`/`COUNTIF` for `strftime`/`count(*) FILTER`. The CTEs, JOIN, `SUM`, and `RANK() OVER (PARTITION BY ...)` are identical.

## Key Takeaways
- GoogleSQL **is** standard SQL: your `SELECT/WHERE/GROUP BY/HAVING/JOIN`, subquery, and CTE knowledge transfers directly. The only visible BigQuery addition is backtick `` `project.dataset.table` `` names.
- Prefer **CTEs (`WITH`)** for multi-step analytics readability.
- Learn the BigQuery extras: `COUNTIF`, `APPROX_COUNT_DISTINCT`, `ARRAY_AGG`, `STRING_AGG`, and the **date functions**.
- **Window functions** (`OVER`, `PARTITION BY`, `LAG`, `RANK`, moving averages) are the analytical workhorse — identical syntax in DuckDB.
- **`ARRAY_AGG(STRUCT(...))`** nests; **`UNNEST`** flattens — BigQuery's signature move for one-to-many without JOINs.
- Biggest BigQuery->DuckDB gaps are **date formatting** and a few aggregate names; everything else ports cleanly.

## Resources
- GoogleSQL query syntax: <https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax>
- Function reference: <https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-and-operators>
- Window (analytic) functions: <https://cloud.google.com/bigquery/docs/reference/standard-sql/analytic-function-concepts>
- Arrays & UNNEST: <https://cloud.google.com/bigquery/docs/arrays>
- DuckDB SQL: <https://duckdb.org/docs/sql/introduction>
- Prev: `403-bigquery-datasets-tables-and-types.md` · Next: `405-bigquery-loading-partitioning-clustering.md`
