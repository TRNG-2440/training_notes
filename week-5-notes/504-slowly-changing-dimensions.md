# Slowly Changing Dimensions (SCD)

> Day 5 · Note 504 · refreshes W4 `c197-slowly-changing-dimensions.md` + root `SCD.md` (whose pseudo-SQL is replaced here with correct, runnable versions)

## Learning Objectives

- Explain *why* dimension attributes change and why that threatens historical accuracy
- Implement SCD Types 0, 1, 2, and 3 with concrete before/after examples
- Write a **correct** SCD Type 2 `MERGE` (both BigQuery and a DuckDB-runnable equivalent)
- Run point-in-time queries against a Type 2 dimension

## Why This Matters

Dimensions change: customers move, products get reclassified, reps switch territories. **How you absorb those changes decides whether last year's report still tells the truth.** Overwrite blindly and every historical sale silently re-attributes itself to the new region. SCD techniques are the discipline for preserving (or deliberately discarding) history. Type 2 in particular is the backbone of the Day 5 capstone.

## Concept Explanation

### The Problem

```
2024:  Customer C001 "John Smith"  Region = East
2025:  Customer C001 "John Smith"  Region = West   (he moved)

When you report 2024 sales, which region should John's orders roll up to?
  - East  → historically accurate ("as it was")
  - West  → current attribute ("as it is now")
Your SCD type is the answer to that question.
```

### The four types

| Type | Strategy | History kept | Use when |
|------|----------|--------------|----------|
| **0** | Never change | Original forever | Immutable facts about the entity (birth date, original signup date) |
| **1** | Overwrite | None | Corrections / attributes where history is irrelevant |
| **2** | Add a new versioned row | Full | You must report "as it was" — the workhorse |
| **3** | Add a "previous value" column | Just current + prior | You only care about current vs. one prior value |

#### Type 0 — Retain Original

Never update. Good for attributes that must not drift: `original_signup_date`, `date_of_birth`.

#### Type 1 — Overwrite (history lost)

```
Before                          After update (region East is gone forever)
+------+------+--------+        +------+------+--------+
| key  | name | region |        | key  | name | region |
| 1    | John | East   |   -->  | 1    | John | West   |
+------+------+--------+        +------+------+--------+
```

```sql
UPDATE dim_customer
SET region = 'West'
WHERE customer_id = 'C001';
```

Use when the old value has no analytical meaning (fixing a typo, updating a phone number).

#### Type 2 — Add New Row (full history)

Keep the old row, close it out with an `end_date` and `is_current = false`, and insert a **new versioned row** with a fresh surrogate key.

```
After update: two rows, one natural key (C001), two surrogate keys
+------+-------------+------+--------+----------------+------------+------------+
| key  | customer_id | name | region | effective_date | end_date   | is_current |
+------+-------------+------+--------+----------------+------------+------------+
| 1    | C001        | John | East   | 2020-01-01     | 2025-06-14 | false      |
| 42   | C001        | John | West   | 2025-06-15     | 9999-12-31 | true       |
+------+-------------+------+--------+----------------+------------+------------+
```

Note the columns that make it work: a **surrogate key** distinct per version, **effective_date / end_date** validity window, and an **is_current** flag for the common "latest" query. This is why facts reference the *surrogate* key — a 2024 sale points at surrogate `1` (East), a 2025 sale points at surrogate `42` (West), and history stays correct automatically.

#### Type 3 — Add New Column (limited history)

```
+------+------+----------------+-----------------+
| key  | name | current_region | previous_region |
| 1    | John | West           | East            |
+------+------+----------------+-----------------+
```

Only ever holds *one* prior value. Use for a small, known number of look-backs (e.g. "current vs. prior sales territory").

### Point-in-Time Queries (the payoff of Type 2)

```sql
-- What region was John in on 2024-06-01?
SELECT region
FROM dim_customer
WHERE customer_id = 'C001'
  AND DATE '2024-06-01' >= effective_date
  AND DATE '2024-06-01' <  end_date;      -- returns: East

-- Current view only
SELECT * FROM dim_customer WHERE is_current;
```

### Type selection cheat-sheet

| Type | History | Storage | Complexity |
|------|---------|---------|------------|
| 0 | none (frozen) | minimal | lowest |
| 1 | none (overwrite) | minimal | low |
| 2 | full | higher | moderate |
| 3 | current + 1 prior | moderate | low |

## Code Example

### Correct SCD Type 2 — DuckDB-runnable

DuckDB does not support multi-branch `MERGE` (WHEN MATCHED / WHEN NOT MATCHED with different actions), so the robust, portable pattern is **two statements in one transaction**: (1) expire changed current rows, (2) insert new versions for changed *and* brand-new keys. This is the exact approach the Day 5 demo (`demos/501-scd-type2-merge/`) ships.

```sql
-- Staging table `stg_customer` holds today's incoming source snapshot:
--   (customer_id, name, region)

BEGIN;

-- STEP 1: expire current rows whose tracked attributes changed
UPDATE dim_customer AS d
SET end_date   = CURRENT_DATE,
    is_current = FALSE
FROM stg_customer AS s
WHERE d.customer_id = s.customer_id
  AND d.is_current  = TRUE
  AND (d.name <> s.name OR d.region <> s.region);   -- change detection

-- STEP 2: insert a new current version for
--   (a) keys we just expired, and (b) brand-new keys
INSERT INTO dim_customer
    (customer_key, customer_id, name, region, effective_date, end_date, is_current)
SELECT
    nextval('customer_key_seq'),          -- surrogate key from a sequence
    s.customer_id, s.name, s.region,
    CURRENT_DATE, DATE '9999-12-31', TRUE
FROM stg_customer s
LEFT JOIN dim_customer d
       ON d.customer_id = s.customer_id AND d.is_current = TRUE
WHERE d.customer_id IS NULL                          -- (b) brand-new key
   OR d.name <> s.name OR d.region <> s.region;      -- (a) changed key

COMMIT;
```

Create the sequence once: `CREATE SEQUENCE customer_key_seq START 1;`

### Correct SCD Type 2 — BigQuery `MERGE` (reference)

BigQuery supports a single-pass `MERGE`. The standard trick: the source is `UNION`ed so a *changed* key appears **twice** — once to expire (matched) and once as a NULL-join row to insert (not matched).

```sql
MERGE dataset.dim_customer AS d
USING (
    -- row that will MATCH the current version -> expire it
    SELECT s.customer_id AS join_key, s.customer_id, s.name, s.region FROM staging.customer s
    UNION ALL
    -- row that will NOT match (join_key NULL) -> insert new version, but only when changed/new
    SELECT NULL AS join_key, s.customer_id, s.name, s.region
    FROM staging.customer s
    LEFT JOIN dataset.dim_customer d
           ON d.customer_id = s.customer_id AND d.is_current
    WHERE d.customer_id IS NULL
       OR d.name <> s.name OR d.region <> s.region
) AS src
ON d.customer_id = src.join_key AND d.is_current
   AND (d.name <> src.name OR d.region <> src.region)   -- only match when changed

WHEN MATCHED THEN
    UPDATE SET end_date = CURRENT_DATE(), is_current = FALSE

WHEN NOT MATCHED AND src.join_key IS NULL THEN
    INSERT (customer_key, customer_id, name, region, effective_date, end_date, is_current)
    VALUES (
        (SELECT COALESCE(MAX(customer_key),0)+1 FROM dataset.dim_customer),  -- or GENERATE_UUID()
        src.customer_id, src.name, src.region,
        CURRENT_DATE(), DATE '9999-12-31', TRUE
    );
```

> The root `W4/SCD.md` sketch used `IF NOT EXISTS ... INSERT` pseudo-SQL that (a) had no versioning columns and (b) is not valid standalone SQL. The two versions above are the correct, tested-pattern replacements — prefer the DuckDB two-statement form for the offline demos, the `MERGE` for BigQuery.

### Python wrapper (used by the demo)

```python
import duckdb

def apply_scd_type2(con: duckdb.DuckDBPyConnection) -> None:
    """Expire changed current rows, then insert new versions (changed + new)."""
    con.execute("BEGIN")
    con.execute("""
        UPDATE dim_customer AS d
        SET end_date = CURRENT_DATE, is_current = FALSE
        FROM stg_customer AS s
        WHERE d.customer_id = s.customer_id AND d.is_current
          AND (d.name <> s.name OR d.region <> s.region)
    """)
    con.execute("""
        INSERT INTO dim_customer
        SELECT nextval('customer_key_seq'), s.customer_id, s.name, s.region,
               CURRENT_DATE, DATE '9999-12-31', TRUE
        FROM stg_customer s
        LEFT JOIN dim_customer d ON d.customer_id = s.customer_id AND d.is_current
        WHERE d.customer_id IS NULL OR d.name <> s.name OR d.region <> s.region
    """)
    con.execute("COMMIT")
```

## Key Takeaways

- SCD **Type 1** overwrites (no history); **Type 2** versions with dates + `is_current` (full history); **Type 3** keeps one prior value; **Type 0** freezes.
- Type 2 needs **surrogate keys** so each version is independently referenceable — facts point at the version that was current when the event happened.
- DuckDB: **two statements in a transaction** (expire, then insert). BigQuery: a single **`MERGE`** with a `UNION ALL` source so changed keys both expire and insert.
- Type 2 unlocks **point-in-time** queries via `effective_date <= d < end_date`.

## Resources

- Kimball SCD Type 2: <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/>
- BigQuery `MERGE`: <https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement>
- Runnable demo: `demos/501-scd-type2-merge/` · Applied in capstone: `exercises/502-capstone-etl-pipeline.md`
