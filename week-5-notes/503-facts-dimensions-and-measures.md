# Facts, Dimensions & Measures

> Day 5 · Note 503 · refreshes W4 `c195` (facts) + `c196` (dimensions) + `c198` (measures) + `c199` (conformed dims)

## Learning Objectives

- Describe the three fact-table types and match a scenario to each
- Classify a measure as additive / semi-additive / non-additive and query it correctly
- Explain surrogate vs. natural keys and why surrogate keys win in a warehouse
- Explain conformed dimensions and build a proper **date dimension**

## Why This Matters

Notes 501–502 gave you the shapes. This note is the anatomy: what actually goes *inside* fact and dimension tables, and the traps (summing a non-additive measure, using a natural key that changes) that quietly corrupt reports. Get these right and your numbers are trustworthy.

## Concept Explanation

### Fact Tables

A fact table stores **quantitative measurements of a business process** at a declared grain. Characteristics: many rows (millions–billions), narrow (few columns), mostly foreign keys + numeric measures, usually partitioned by date.

```sql
CREATE TABLE fact_sales (
    -- Surrogate foreign keys to dimensions
    date_key      BIGINT NOT NULL,
    customer_key  BIGINT NOT NULL,
    product_key   BIGINT NOT NULL,
    store_key     BIGINT NOT NULL,

    -- Degenerate dimension (an ID with no attributes of its own)
    order_number  VARCHAR,

    -- Measures
    quantity        BIGINT,          -- additive
    unit_price      DECIMAL(10,2),   -- non-additive
    discount_amount DECIMAL(10,2),   -- additive
    revenue         DECIMAL(12,2)    -- additive
);
```

#### Three types of fact table

| Type | One row = | Example | Notes |
|------|-----------|---------|-------|
| **Transaction** | One event | One sale line item | Atomic, most common, insert-only |
| **Periodic snapshot** | State at end of a period | Account balance each day | Regular heartbeat; semi-additive measures |
| **Accumulating snapshot** | One process instance, updated as it progresses | An order from placed → shipped → delivered | Rows get **updated** as milestones hit |

```sql
-- Transaction: one row per sale line
CREATE TABLE fact_sales_txn (
    date_key BIGINT, customer_key BIGINT, product_key BIGINT,
    quantity BIGINT, amount DECIMAL(12,2)
);   -- Grain: one row per order line item

-- Periodic snapshot: one row per account per day
CREATE TABLE fact_account_daily (
    date_key BIGINT, account_key BIGINT,
    balance DECIMAL(14,2)            -- semi-additive
);   -- Grain: one row per account per day

-- Accumulating snapshot: one row per order, milestone dates filled over time
CREATE TABLE fact_order_fulfillment (
    order_key BIGINT, customer_key BIGINT,
    order_date_key    BIGINT,
    ship_date_key     BIGINT,        -- NULL until shipped
    deliver_date_key  BIGINT,        -- NULL until delivered
    order_amount DECIMAL(12,2)
);   -- Grain: one row per order (updated in place)
```

### Measures: additive / semi-additive / non-additive

The classification tells you **which aggregations are valid**.

| Type | Can you `SUM` it? | Example | Correct aggregation |
|------|-------------------|---------|---------------------|
| **Additive** | Across **all** dimensions | revenue, quantity, cost | `SUM` |
| **Semi-additive** | Across some, **not time** | account balance, inventory on-hand, headcount | `SUM` within a day; `AVG` / point-in-time across days |
| **Non-additive** | Never | unit price, ratio, percentage | `AVG`, or weighted avg |

```sql
-- Additive: sum freely
SELECT s.region, SUM(f.revenue) AS revenue
FROM fact_sales f JOIN dim_store s ON f.store_key = s.store_key
GROUP BY s.region;

-- Semi-additive: OK within one day...
SELECT SUM(balance) FROM fact_account_daily WHERE date_key = 20250115;
-- ...WRONG across days (double-counts balances over time):
-- SELECT SUM(balance) FROM fact_account_daily;   -- meaningless
SELECT AVG(balance) FROM fact_account_daily;       -- use avg / point-in-time

-- Non-additive: never sum a price; weight it
SELECT p.category,
       AVG(f.unit_price)                                   AS simple_avg,
       SUM(f.quantity * f.unit_price) / SUM(f.quantity)    AS weighted_avg
FROM fact_sales f JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category;
```

### Dimension Tables

Descriptive context: the "who / what / when / where / why." Fewer rows, **wide** (many attributes), change slowly (Note 504).

```sql
CREATE TABLE dim_customer (
    customer_key BIGINT NOT NULL,   -- surrogate (PK)
    customer_id  VARCHAR,           -- natural key from source

    first_name VARCHAR, last_name VARCHAR, full_name VARCHAR,
    email VARCHAR, phone VARCHAR,

    city VARCHAR, state VARCHAR, region VARCHAR, country VARCHAR,  -- hierarchy

    segment VARCHAR, acquisition_channel VARCHAR,                 -- derived

    effective_date DATE, end_date DATE, is_current BOOLEAN        -- SCD audit
);
```

### Surrogate vs. Natural Keys

| Key | What it is | Example |
|-----|------------|---------|
| **Surrogate** | System-generated integer, meaningless outside the warehouse | `12345` |
| **Natural** | The source system's business identifier | `CUST-ABC-001` |

**Always use a surrogate key as the dimension PK and the fact FK. Keep the natural key as an attribute.** Why:

- **Faster joins** — integers beat wide/composite strings.
- **Decoupling** — source can change or renumber its IDs; the warehouse is insulated.
- **SCD Type 2 needs it** — the same customer (one natural key) has multiple versioned rows, each with its **own** surrogate key. A natural key alone cannot express "which version."

### Conformed Dimensions

A **conformed dimension** is one shared *identically* — same key, attributes, values — across multiple fact tables/marts. It is the glue of a galaxy schema and the enabler of cross-process analysis.

```
        +-------------+
        |  dim_date   |   one definition
        +------+------+
   +-----------+-----------+
   |           |           |
fact_sales  fact_inventory  fact_orders
```

Benefits: consistent definitions everywhere, cross-process reporting, single source of truth, maintain-once.

### The Date Dimension (build one in every warehouse)

The most important conformed dimension. Pre-computing calendar attributes means analysts never write `EXTRACT`/date math in every query, and you get holidays, fiscal periods, weekend flags for free.

```sql
-- DuckDB: generate a date dimension in one statement
CREATE TABLE dim_date AS
SELECT
    CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_key,   -- 20250115
    d                                       AS full_date,
    EXTRACT(year    FROM d)                 AS year,
    EXTRACT(quarter FROM d)                 AS quarter,
    EXTRACT(month   FROM d)                 AS month,
    strftime(d, '%B')                       AS month_name,
    EXTRACT(day     FROM d)                 AS day_of_month,
    EXTRACT(dow     FROM d)                 AS day_of_week,   -- 0=Sun
    strftime(d, '%A')                       AS day_name,
    (EXTRACT(dow FROM d) IN (0, 6))         AS is_weekend
FROM (
    SELECT UNNEST(generate_series(DATE '2020-01-01',
                                  DATE '2030-12-31',
                                  INTERVAL 1 DAY)) AS d
);
```

BigQuery equivalent: `GENERATE_DATE_ARRAY('2020-01-01','2030-12-31')` unnested, with `FORMAT_DATE`/`EXTRACT`.

## Code Example

```python
import duckdb
con = duckdb.connect()

con.execute("""
CREATE TABLE dim_product (product_key INTEGER, category VARCHAR, unit_price DECIMAL(10,2));
CREATE TABLE fact_sales (product_key INTEGER, quantity INTEGER, unit_price DECIMAL(10,2), revenue DECIMAL(12,2));
INSERT INTO dim_product VALUES (1,'Hardware',19.99),(2,'Hardware',29.99);
INSERT INTO fact_sales VALUES (1,10,19.99,199.90),(2,4,29.99,119.96);
""")

# Additive revenue vs. non-additive price handled correctly
print(con.execute("""
    SELECT p.category,
           SUM(f.revenue)                                AS revenue,        -- additive
           SUM(f.quantity*f.unit_price)/SUM(f.quantity)  AS weighted_price  -- non-additive
    FROM fact_sales f JOIN dim_product p USING (product_key)
    GROUP BY p.category
""").fetchdf())
```

## Key Takeaways

- Fact tables come in three shapes: **transaction**, **periodic snapshot**, **accumulating snapshot**.
- Classify every measure — **additive / semi-additive / non-additive** — before letting anyone `SUM` it.
- **Surrogate keys** are the dimension PK and fact FK; the natural key rides along as an attribute (and SCD2 requires this split).
- **Conformed dimensions** shared identically across facts enable cross-process analysis.
- Every warehouse needs a pre-built **date dimension**.

## Resources

- Kimball dimensional-modeling techniques: <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/>
- Next: `504-slowly-changing-dimensions.md` — what happens when dimension attributes change.
