# Dimensional Modeling Introduction

> Day 5 · Note 501 · refreshes W4 `c192-dimensional-modeling-intro.md`

## Learning Objectives

- Define dimensional modeling and contrast it with normalized (3NF) modeling
- Explain the Kimball methodology and its four-step design process
- Define **grain** and explain why choosing it first is non-negotiable
- Explain *why* we deliberately denormalize for analytics (and what we trade away)

## Why This Matters

By Day 4 you saw the split between **OLTP** (transaction systems, normalized, optimized for writes) and **OLAP** (analytics, optimized for reads). Dimensional modeling is *how* you design the OLAP side. It has been the dominant data-warehouse design technique for 30+ years because it makes analytical queries fast and — just as important — makes the schema legible to business users. Everything the rest of Day 5 does (star schemas, SCDs, the ETL/ELT capstone) is built on this foundation.

## Concept Explanation

### What is Dimensional Modeling?

Dimensional modeling organizes data into two kinds of tables:

- **Facts** — the *measurements* of a business process (revenue, quantity, duration). One fact table per business process.
- **Dimensions** — the *context* that describes those measurements (who, what, when, where, why).

It prioritizes **query performance and human understanding** over storage efficiency. That is the opposite priority from the OLTP databases you normalize to 3NF.

**Origin:** Ralph Kimball, 1990s. Still the default for analytical modeling.

```
Dimensional Model — facts sit at the center, dimensions describe them:

   +----------+       +-------------+       +----------+
   |   WHO    |       |    WHAT     |       |   WHEN   |
   | Customer |------>| Sales Fact  |<------|   Date   |
   +----------+       +------+------+       +----------+
                             ^
                             |
                       +----------+
                       |  WHERE   |
                       |  Store   |
                       +----------+
```

### Normalized (3NF) vs. Dimensional

| Aspect | Normalized (3NF / OLTP) | Dimensional (OLAP) |
|--------|-------------------------|--------------------|
| Optimized for | Fast, safe **writes** | Fast **reads / aggregations** |
| Redundancy | Eliminated | Deliberately allowed |
| Table count | Many small tables | Few wide tables |
| Joins per query | Many | Few |
| Primary audience | Applications | Analysts + BI tools |
| Update anomalies | Avoided by design | Managed via ETL, not schema |

A normalized order system might spread a single sale across `orders`, `order_lines`, `customers`, `addresses`, `products`, `categories`, `suppliers` — six-plus joins to answer "revenue by category by month." A dimensional model collapses the descriptive tables into a handful of wide dimensions so the same question is a 2–3 table join.

### Grain: Choose It First, Choose It Explicitly

**Grain** = what one row of the fact table represents. It is the single most important design decision.

```
Good grain:  "One row per product per sales transaction line item"
Weak grain:  "Sales data"   (too vague — you cannot design against it)
```

Rules of thumb:

- Declare grain as **one sentence** before listing any columns.
- Prefer the **atomic** (most detailed) grain you can afford. You can always aggregate up; you can never drill down below the grain you stored.
- Every dimension and every measure must make sense **at that grain**. If a measure only makes sense at a coarser grain, it belongs in a different fact table.

### Why Denormalize for Analytics?

1. **Fewer joins → faster queries.** Columnar warehouses (BigQuery, DuckDB) scan wide tables efficiently; they do *not* love many-way joins.
2. **Human legibility.** Analysts think "sales **by** region **over** time." A star schema maps directly onto that sentence.
3. **BI-tool friendliness.** Tableau, Looker, Power BI all assume a star.
4. **Stable interface.** The messy source normalization is hidden behind the ETL layer; the model stays clean.

What you trade away: some storage, and the *possibility* of update anomalies — which you now manage in the **ETL/load layer** (Notes 505–506) rather than in the schema.

### The Kimball Four-Step Process

1. **Select the business process** — Sales, Inventory, Subscriptions. One fact table serves one process.
2. **Declare the grain** — one sentence (see above).
3. **Identify the dimensions** — the "by what?" filters: who, what, when, where.
4. **Identify the facts (measures)** — the numbers you will `SUM`/`AVG`.

### Kimball vs. Inmon (know the distinction)

| Aspect | Kimball | Inmon |
|--------|---------|-------|
| Approach | Bottom-up (marts first) | Top-down (enterprise EDW first) |
| Structure | Star schemas | Normalized enterprise model, marts downstream |
| Time to value | Faster | Slower |
| Complexity | Simpler | More complex |

This week uses the **Kimball** approach throughout.

## Code Example

```python
from dataclasses import dataclass, field

@dataclass
class DimensionalModel:
    """A lightweight sketch of a Kimball four-step design."""
    business_process: str
    grain: str                      # step 2 — one sentence
    dimensions: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)

    def describe(self) -> None:
        print(f"Business Process : {self.business_process}")
        print(f"Grain            : {self.grain}")
        print(f"Dimensions       : {', '.join(self.dimensions)}")
        print(f"Measures         : {', '.join(self.measures)}")


retail_sales = DimensionalModel(
    business_process="Retail Sales",
    grain="One row per product per sales-order line item",
    dimensions=["Date", "Customer", "Product", "Store", "Promotion"],
    measures=["quantity", "unit_price", "discount_amount", "revenue", "cost"],
)
retail_sales.describe()
```

## Key Takeaways

- Dimensional modeling splits data into **facts** (measures) and **dimensions** (context).
- It optimizes for **reads and human understanding**, the inverse of 3NF/OLTP priorities.
- **Grain comes first** and is stated in one sentence; store the most atomic grain you can.
- Denormalization buys query speed and legibility; you manage the anomaly risk in ETL.
- Kimball's four steps: process → grain → dimensions → facts.

## Resources

- The Data Warehouse Toolkit (Kimball): <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/>
- Next: `502-star-snowflake-galaxy-schemas.md` — how these tables get wired together.
- Back-reference: Day 4 OLTP vs OLAP notes.
