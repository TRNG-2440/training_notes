"""
Day 5 · Demo 501 — SCD Type 2 in DuckDB
=======================================

Builds a customer dimension, applies a batch of source changes, and performs a
Slowly Changing Dimension **Type 2** update:
  - expire the current row of any customer whose tracked attributes changed
  - insert a new versioned row (fresh surrogate key, new effective window, is_current=TRUE)
  - insert brand-new customers as current rows

Everything runs offline in an in-memory DuckDB database. No cloud needed.

Run:
    pip install -r requirements.txt
    python scd_type2_demo.py

See README.md for the equivalent BigQuery MERGE (also in scd_type2_bigquery.sql).
"""
from __future__ import annotations
import duckdb

# A fixed "load date" so demo output is stable/reproducible.
LOAD_DATE = "2025-06-15"
END_OF_TIME = "9999-12-31"


def build_initial_dimension(con: duckdb.DuckDBPyConnection) -> None:
    """Create dim_customer with SCD-2 audit columns and seed 3 customers."""
    con.execute("CREATE SEQUENCE customer_key_seq START 1;")
    con.execute("""
        CREATE TABLE dim_customer (
            customer_key   BIGINT PRIMARY KEY,   -- surrogate key (per VERSION)
            customer_id    VARCHAR,              -- natural key (per CUSTOMER)
            name           VARCHAR,
            region         VARCHAR,
            effective_date DATE,
            end_date       DATE,
            is_current     BOOLEAN
        );
    """)
    # Seed rows: three customers, all current, effective from 2020.
    con.execute("""
        INSERT INTO dim_customer VALUES
            (nextval('customer_key_seq'), 'C001', 'John Smith',  'East',  DATE '2020-01-01', DATE '9999-12-31', TRUE),
            (nextval('customer_key_seq'), 'C002', 'Jane Doe',    'West',  DATE '2020-01-01', DATE '9999-12-31', TRUE),
            (nextval('customer_key_seq'), 'C003', 'Sam Rivera',  'North', DATE '2020-01-01', DATE '9999-12-31', TRUE);
    """)


def load_source_batch(con: duckdb.DuckDBPyConnection) -> None:
    """Today's incoming source snapshot lands in a staging table.

    - C001 moved East -> West        (attribute changed  -> new version)
    - C002 unchanged                 (no-op)
    - C003 renamed Sam -> Samuel      (attribute changed  -> new version)
    - C004 brand new                 (insert as current)
    """
    con.execute("""
        CREATE TABLE stg_customer (customer_id VARCHAR, name VARCHAR, region VARCHAR);
        INSERT INTO stg_customer VALUES
            ('C001', 'John Smith',    'West'),
            ('C002', 'Jane Doe',      'West'),
            ('C003', 'Samuel Rivera', 'North'),
            ('C004', 'Priya Patel',   'South');
    """)


def apply_scd_type2(con: duckdb.DuckDBPyConnection) -> None:
    """The core SCD Type 2 operation: expire-then-insert, in one transaction.

    DuckDB has no multi-branch MERGE, so we use the portable two-statement pattern.
    """
    con.execute("BEGIN")

    # STEP 1 — expire current rows whose tracked attributes changed.
    con.execute(f"""
        UPDATE dim_customer AS d
        SET end_date   = DATE '{LOAD_DATE}',
            is_current = FALSE
        FROM stg_customer AS s
        WHERE d.customer_id = s.customer_id
          AND d.is_current  = TRUE
          AND (d.name <> s.name OR d.region <> s.region);   -- change detection
    """)

    # STEP 2 — insert new current version for changed keys AND brand-new keys.
    con.execute(f"""
        INSERT INTO dim_customer
            (customer_key, customer_id, name, region, effective_date, end_date, is_current)
        SELECT
            nextval('customer_key_seq'),
            s.customer_id, s.name, s.region,
            DATE '{LOAD_DATE}', DATE '{END_OF_TIME}', TRUE
        FROM stg_customer s
        LEFT JOIN dim_customer d
               ON d.customer_id = s.customer_id AND d.is_current = TRUE
        WHERE d.customer_id IS NULL                          -- brand-new customer
           OR d.name <> s.name OR d.region <> s.region;      -- changed customer
    """)

    con.execute("COMMIT")


def show(con: duckdb.DuckDBPyConnection, title: str) -> None:
    print(f"\n=== {title} ===")
    df = con.execute("""
        SELECT customer_key, customer_id, name, region,
               effective_date, end_date, is_current
        FROM dim_customer
        ORDER BY customer_id, effective_date
    """).fetchdf()
    print(df.to_string(index=False))


def point_in_time_examples(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Point-in-time queries (the payoff of Type 2) ===")

    region_2024 = con.execute("""
        SELECT region FROM dim_customer
        WHERE customer_id = 'C001'
          AND DATE '2024-06-01' >= effective_date
          AND DATE '2024-06-01' <  end_date
    """).fetchone()[0]
    print(f"C001 region as of 2024-06-01 : {region_2024}   (historically accurate)")

    region_now = con.execute("""
        SELECT region FROM dim_customer WHERE customer_id = 'C001' AND is_current
    """).fetchone()[0]
    print(f"C001 region right now        : {region_now}")

    n_current = con.execute(
        "SELECT COUNT(*) FROM dim_customer WHERE is_current").fetchone()[0]
    n_rows = con.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0]
    print(f"Current customers: {n_current}   |   Total versioned rows: {n_rows}")


def main() -> None:
    con = duckdb.connect()  # in-memory
    build_initial_dimension(con)
    show(con, "BEFORE — initial dimension (3 current rows)")

    load_source_batch(con)
    apply_scd_type2(con)
    show(con, "AFTER — SCD Type 2 applied "
              "(C001 & C003 versioned, C004 added, C002 untouched)")

    point_in_time_examples(con)
    print("\nDone. Notice: no history was overwritten — old rows were closed out, "
          "not deleted.")


if __name__ == "__main__":
    main()
