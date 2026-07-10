-- ============================================================================
-- Day 5 · Demo 501 — SCD Type 2 in BigQuery (reference)
-- ============================================================================
-- The Python demo runs the equivalent in DuckDB using a two-statement pattern
-- (DuckDB has no multi-branch MERGE). BigQuery DOES support MERGE, so the
-- idiomatic single-pass version is below.
--
-- Trick: UNION the source so a CHANGED customer appears twice —
--   * once as a row that MATCHES the current version   -> expire it
--   * once as a row that does NOT match (join_key NULL) -> insert new version
-- A brand-new customer appears only on the "not matched" side.
-- ============================================================================

-- One-time: the dimension table with SCD-2 audit columns.
CREATE TABLE IF NOT EXISTS mydataset.dim_customer (
    customer_key   INT64,          -- surrogate key (per version)
    customer_id    STRING,         -- natural key
    name           STRING,
    region         STRING,
    effective_date DATE,
    end_date       DATE,
    is_current     BOOL
);

-- The daily source snapshot lands in staging (from your EL step).
-- Assume mydataset.stg_customer(customer_id, name, region) is populated.

MERGE mydataset.dim_customer AS d
USING (
    -- (A) rows that will MATCH the current version -> candidate to EXPIRE
    SELECT s.customer_id AS join_key, s.customer_id, s.name, s.region
    FROM mydataset.stg_customer s

    UNION ALL

    -- (B) rows that will NOT match (NULL join_key) -> INSERT new version,
    --     but only for customers that are new OR whose attributes changed
    SELECT CAST(NULL AS STRING) AS join_key, s.customer_id, s.name, s.region
    FROM mydataset.stg_customer s
    LEFT JOIN mydataset.dim_customer d
           ON d.customer_id = s.customer_id AND d.is_current
    WHERE d.customer_id IS NULL
       OR d.name <> s.name
       OR d.region <> s.region
) AS src
ON  d.customer_id = src.join_key
AND d.is_current
AND (d.name <> src.name OR d.region <> src.region)   -- only match when changed

-- Expire the outgoing current row.
WHEN MATCHED THEN
    UPDATE SET end_date = CURRENT_DATE(), is_current = FALSE

-- Insert the new current version (and brand-new customers).
WHEN NOT MATCHED AND src.join_key IS NULL THEN
    INSERT (customer_key, customer_id, name, region,
            effective_date, end_date, is_current)
    VALUES (
        -- surrogate key: max+1 for the demo; use GENERATE_UUID() or an
        -- offset+ROW_NUMBER() staging step for real concurrent loads.
        (SELECT COALESCE(MAX(customer_key), 0) + 1 FROM mydataset.dim_customer),
        src.customer_id, src.name, src.region,
        CURRENT_DATE(), DATE '9999-12-31', TRUE
    );

-- Point-in-time query: region of C001 as it was on 2024-06-01
SELECT region
FROM mydataset.dim_customer
WHERE customer_id = 'C001'
  AND DATE '2024-06-01' >= effective_date
  AND DATE '2024-06-01' <  end_date;
