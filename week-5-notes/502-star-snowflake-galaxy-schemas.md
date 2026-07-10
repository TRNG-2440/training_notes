# Star, Snowflake & Galaxy Schemas

> Day 5 · Note 502 · refreshes W4 `c193` (star) + `c194` (snowflake) + `c200` (galaxy)

## Learning Objectives

- Describe the three dominant dimensional schema shapes and how they differ
- Read and draw each schema as a diagram
- Choose a schema shape for a given workload and justify the trade-off

## Why This Matters

Once you know the grain and your facts/dimensions (Note 501), the next decision is *how the tables are wired together*. That wiring choice — star vs. snowflake vs. galaxy — determines query complexity, join count, and how well BI tools understand your warehouse. Pick wrong and every downstream query pays for it.

## Concept Explanation

### 1. Star Schema — the default

A central **fact** table surrounded by **flat, denormalized dimensions**. Named for its star-like diagram.

```
                        +----------+
                        | dim_date |
                        +----+-----+
                             |
+----------+          +------+------+          +----------+
|   dim_   |          |             |          |   dim_   |
| customer |--------->| fact_sales  |<---------| product  |
+----------+          |             |          +----------+
                      +------+------+
                             |
                        +----+-----+
                        | dim_store|
                        +----------+
```

Design principles:

1. **Denormalized dimensions** — redundancy is allowed and expected (`category` and `category_desc` live right in `dim_product`).
2. **Surrogate keys** — integer keys for joins, not business/natural keys (Note 503).
3. **Single join path** — every dimension joins directly to the fact, one hop.
4. **Wide dimensions** — many descriptive columns per dimension.

```sql
-- One-hop join: simple and fast
SELECT d.year, d.quarter, p.category, s.region,
       SUM(f.total_revenue) AS revenue,
       SUM(f.quantity)      AS units
FROM fact_sales f
JOIN dim_date    d ON f.date_key     = d.date_key
JOIN dim_product p ON f.product_key  = p.product_key
JOIN dim_store   s ON f.store_key    = s.store_key
WHERE d.year = 2025
GROUP BY d.year, d.quarter, p.category, s.region;
```

### 2. Snowflake Schema — normalized dimensions

Same idea, but dimensions are **normalized** into sub-tables (the flat dimension "snowflakes" out into a chain).

```
                              +----------+
                              | dim_year |
                              +----+-----+
                                   |
                        +----------+----------+
                        |      dim_date        |
                        +----------+----------+
                                   |
+----------+          +-----------+-----------+          +-----------+
|   dim_   |          |                       |          |   dim_    |
| customer |--------->|      fact_sales       |<---------|  product  |
+----+-----+          +-----------------------+          +-----+-----+
     |                                                         |
+----+------+                                          +-------+------+
| dim_region|                                          | dim_category |
+-----------+                                          +--------------+
```

```sql
-- Star: flat product dimension (redundant category text stored per row)
CREATE TABLE dim_product_star (
    product_key   BIGINT,
    product_name  VARCHAR,
    category_name VARCHAR,   -- redundant
    category_desc VARCHAR    -- redundant
);

-- Snowflake: normalized into a chain of tables
CREATE TABLE dim_product (
    product_key     BIGINT,
    product_name    VARCHAR,
    subcategory_key BIGINT   -- FK
);
CREATE TABLE dim_subcategory (
    subcategory_key  BIGINT,
    subcategory_name VARCHAR,
    category_key     BIGINT   -- FK
);
CREATE TABLE dim_category (
    category_key  BIGINT,
    category_name VARCHAR,
    category_desc VARCHAR
);
```

The same "revenue by category" query now needs **extra joins** (`fact → dim_product → dim_subcategory → dim_category`).

### 3. Galaxy Schema (Fact Constellation) — the enterprise picture

**Multiple fact tables** sharing **conformed dimensions** (Note 503). This is what a mature enterprise warehouse actually looks like.

```
              +-------------+
              |  dim_date   |   <- conformed, shared by every fact
              +------+------+
                     |
    +----------------+----------------+
    |                |                |
+---+---+        +---+----+       +---+----+
| fact_ |        | fact_  |       | fact_  |
| sales |        |invent. |       |orders  |
+---+---+        +---+----+       +---+----+
    |                |                |
    +----------------+----------------+
                     |
              +------+------+
              | dim_product |   <- conformed, shared
              +-------------+
```

- Each business process gets its **own fact table**.
- **Conformed dimensions** (`dim_date`, `dim_product`) are shared identically across facts — that shared definition is what makes cross-process analysis possible.
- Some dimensions are **process-specific** (e.g. `dim_supplier` only touches purchasing).

### Trade-offs at a glance

| | Star | Snowflake | Galaxy |
|--|------|-----------|--------|
| Dimension shape | Flat, denormalized | Normalized chains | Flat (usually) |
| Joins per query | Fewest | More | Depends on facts joined |
| Query speed | Fastest | Slower | Fast per-fact |
| Storage | Higher (redundant) | Lower | Higher |
| BI-tool friendliness | Best | Weaker | Good (per star) |
| Scope | One process | One process | Whole enterprise |
| When to use | Default choice | Huge dimensions where storage/consistency dominates | Many processes needing cross-analysis |

**Practical guidance:** default to **star**. Only snowflake a specific dimension when it is genuinely large and its normalization buys real consistency/storage wins. A galaxy is simply *several stars that share conformed dimensions* — you build it naturally as you add business processes.

## Code Example

```python
import duckdb

con = duckdb.connect()  # in-memory

# A tiny star: one fact + two flat dimensions
con.execute("""
CREATE TABLE dim_date (
    date_key   INTEGER PRIMARY KEY,
    full_date  DATE, year INTEGER, quarter INTEGER, month_name VARCHAR
);
CREATE TABLE dim_product (
    product_key  INTEGER PRIMARY KEY,
    product_name VARCHAR, category VARCHAR      -- denormalized on purpose
);
CREATE TABLE fact_sales (
    date_key INTEGER, product_key INTEGER,
    quantity INTEGER, revenue DECIMAL(12,2)
);
""")

con.execute("INSERT INTO dim_date VALUES (20250115,'2025-01-15',2025,1,'January')")
con.execute("INSERT INTO dim_product VALUES (1,'Widget','Hardware'),(2,'Gadget','Hardware')")
con.execute("""INSERT INTO fact_sales VALUES
    (20250115,1,10,199.90),(20250115,2,5,149.95)""")

print(con.execute("""
    SELECT d.month_name, p.category,
           SUM(f.revenue) AS revenue, SUM(f.quantity) AS units
    FROM fact_sales f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY d.month_name, p.category
""").fetchdf())
```

## Key Takeaways

- **Star** = central fact + flat denormalized dimensions; the default, fewest joins.
- **Snowflake** = star with dimensions normalized into chains; saves storage/consistency at the cost of more joins.
- **Galaxy / fact constellation** = multiple facts sharing conformed dimensions; the enterprise-scale shape.
- Default to star; snowflake surgically; a galaxy emerges as you add processes.

## Resources

- Kimball — Star schema: <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/star-schema-olap-cube/>
- Next: `503-facts-dimensions-and-measures.md` — the anatomy of the tables themselves.
