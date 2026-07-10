"""
Demo 401 - Run an analytical query and get back a pandas DataFrame,
against EITHER real BigQuery OR a local DuckDB fallback.

Same SQL logic on both engines. The only real difference is how the table
is addressed (backtick `project.dataset.table` on BigQuery vs a plain name
on DuckDB) and the cost/stats reporting (bytes scanned vs rows/time).

Run offline (zero cloud setup):
    python analytics.py --engine duckdb

Run against real BigQuery (needs sandbox + auth, see README):
    python analytics.py --engine bigquery
"""
from __future__ import annotations

import argparse
import time

import pandas as pd

ON_DEMAND_USD_PER_TB = 6.25  # BigQuery on-demand price (approx)


# --------------------------------------------------------------------------
# The analytical question (same for both engines):
#   Top product categories by revenue and order count in 2023.
# BigQuery reads the public thelook_ecommerce dataset directly.
# DuckDB reads a small local sample table we build on the fly.
# --------------------------------------------------------------------------

BIGQUERY_SQL = """
SELECT
    p.category,
    COUNT(*)                AS line_items,
    ROUND(SUM(oi.sale_price), 2) AS revenue
FROM `bigquery-public-data.thelook_ecommerce.order_items` AS oi
JOIN `bigquery-public-data.thelook_ecommerce.products`   AS p
    ON oi.product_id = p.id
WHERE oi.created_at >= @start_date
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 10
"""

DUCKDB_SQL = """
SELECT
    p.category,
    COUNT(*)                AS line_items,
    ROUND(SUM(oi.sale_price), 2) AS revenue
FROM order_items AS oi
JOIN products   AS p
    ON oi.product_id = p.id
WHERE oi.created_at >= $start_date
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 10
"""

START_DATE = "2023-01-01"


def run_bigquery() -> pd.DataFrame:
    from google.cloud import bigquery

    client = bigquery.Client()  # uses Application Default Credentials

    cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", START_DATE)
        ]
    )
    job = client.query(BIGQUERY_SQL, job_config=cfg)
    df = job.to_dataframe()  # blocks until the job finishes

    scanned_gb = (job.total_bytes_processed or 0) / 1e9
    est_usd = scanned_gb / 1000 * ON_DEMAND_USD_PER_TB
    print(f"[bigquery] scanned {scanned_gb:.3f} GB  "
          f"~ ${est_usd:.4f} (free within 1 TB/month)")
    return df


def _build_sample(con) -> None:
    """Create a small local dataset that mimics thelook_ecommerce shape."""
    con.execute("""
        CREATE TABLE products AS
        SELECT * FROM (VALUES
            (1, 'Jeans'), (2, 'Tops'), (3, 'Shoes'),
            (4, 'Accessories'), (5, 'Outerwear')
        ) AS t(id, category)
    """)
    # Deterministic pseudo-random order items across 2022-2023.
    con.execute("""
        CREATE TABLE order_items AS
        SELECT
            i                                         AS order_item_id,
            (i % 5) + 1                               AS product_id,
            ROUND(5 + (i * 7 % 200) + (i % 13), 2)    AS sale_price,
            DATE '2022-06-01' + (i % 500) * INTERVAL 1 DAY AS created_at
        FROM range(20000) AS r(i)
    """)


def run_duckdb() -> pd.DataFrame:
    import duckdb

    con = duckdb.connect()  # in-memory
    _build_sample(con)

    t0 = time.perf_counter()
    df = con.execute(DUCKDB_SQL, {"start_date": START_DATE}).df()
    elapsed = time.perf_counter() - t0
    print(f"[duckdb] {len(df)} rows in {elapsed:.3f}s "
          f"(local, no billing)")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=["bigquery", "duckdb"],
        default="duckdb",
        help="Which backend to run against (default: duckdb, zero setup).",
    )
    args = parser.parse_args()

    print(f"Engine: {args.engine}\n")
    df = run_bigquery() if args.engine == "bigquery" else run_duckdb()

    print("\nTop categories by revenue:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
