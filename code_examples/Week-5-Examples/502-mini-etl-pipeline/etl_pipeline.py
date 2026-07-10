"""
Day 5 · Demo 502 — Mini ETL pipeline (the week's capstone demo)
===============================================================

A small, self-contained E -> T -> L pipeline that ties the whole week together:

  E  Extract  : pull JSON from a public API with httpx (Day 1),
                falling back to a shipped sample file if offline.
  T  Transform: clean & reshape with pandas (Day 2) — drop dupes/nulls,
                standardize text, derive fields, run data-quality checks (Note 506).
  L  Load     : land into a DuckDB warehouse (Day 4) modeled as a simple STAR
                (Day 5): fact_task + dim_user + dim_date.

Then it runs an analytical query over the star.

Run:
    pip install -r requirements.txt
    python etl_pipeline.py            # tries the API, falls back to sample_data.json
    python etl_pipeline.py --offline  # skip the network, use the sample file

Output warehouse: warehouse.duckdb (created next to this script).
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).parent
API_URL = "https://jsonplaceholder.typicode.com/todos"   # public, no auth
SAMPLE = HERE / "sample_data.json"
WAREHOUSE = HERE / "warehouse.duckdb"


# ---------------------------------------------------------------------------
# E — EXTRACT
# ---------------------------------------------------------------------------
def extract(offline: bool = False) -> list[dict]:
    """Pull JSON from the API with httpx; fall back to the shipped sample."""
    if not offline:
        try:
            import httpx
            print(f"[extract] GET {API_URL}")
            resp = httpx.get(API_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            print(f"[extract] pulled {len(data)} records from API")
            return data
        except Exception as e:  # network down, timeout, DNS, etc.
            print(f"[extract] API unavailable ({type(e).__name__}: {e}); "
                  f"falling back to sample file")

    data = json.loads(SAMPLE.read_text())
    print(f"[extract] loaded {len(data)} records from {SAMPLE.name}")
    return data


# ---------------------------------------------------------------------------
# T — TRANSFORM
# ---------------------------------------------------------------------------
def transform(records: list[dict]) -> pd.DataFrame:
    """Clean & reshape with pandas, then derive dimensional attributes."""
    df = pd.DataFrame(records)

    # Cleaning ---------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["id"])                 # remove dup task ids
    df["title"] = df["title"].astype("string").str.strip() # trim whitespace
    df = df.dropna(subset=["title"])                       # drop rows w/o a title
    df = df[df["title"] != ""]
    print(f"[transform] cleaned {before} -> {len(df)} rows "
          f"({before - len(df)} dropped as dup/null/blank)")

    # Standardization + derivation ------------------------------------------
    df = df.rename(columns={"id": "task_id", "userId": "user_id"})
    df["completed"] = df["completed"].astype(bool)
    # Derive a synthetic load/activity date so we can join a real date dimension.
    # (The demo API has no timestamps; assign deterministic recent dates.)
    base = date.today() - timedelta(days=30)
    df = df.reset_index(drop=True)
    df["activity_date"] = [base + timedelta(days=int(i) % 30) for i in df.index]
    df["title_length"] = df["title"].str.len().astype(int)   # derived measure

    return df[["task_id", "user_id", "activity_date",
               "completed", "title", "title_length"]]


def quality_gate(df: pd.DataFrame) -> None:
    """Minimal data-quality checks (Note 506). Raise to stop before publish."""
    problems = []
    if df["task_id"].duplicated().any():
        problems.append("duplicate task_id")
    if df["task_id"].isnull().any():
        problems.append("null task_id")
    if df["title"].isnull().any() or (df["title"] == "").any():
        problems.append("empty title")
    if problems:
        raise ValueError(f"[quality] FAILED: {problems}")
    print(f"[quality] passed: {len(df)} rows, "
          f"{df['user_id'].nunique()} users, "
          f"{df['activity_date'].nunique()} distinct dates")


# ---------------------------------------------------------------------------
# L — LOAD (into a star schema)
# ---------------------------------------------------------------------------
def load(df: pd.DataFrame, con: duckdb.DuckDBPyConnection) -> None:
    """Build a simple star: dim_user + dim_date + fact_task."""
    con.register("staged", df)

    # dim_date — the conformed date dimension (Note 503)
    con.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        SELECT DISTINCT
            CAST(strftime(activity_date, '%Y%m%d') AS INTEGER) AS date_key,
            activity_date                                       AS full_date,
            EXTRACT(year  FROM activity_date)                   AS year,
            EXTRACT(month FROM activity_date)                   AS month,
            strftime(activity_date, '%A')                       AS day_name,
            (EXTRACT(dow FROM activity_date) IN (0, 6))         AS is_weekend
        FROM staged;
    """)

    # dim_user — one row per user (surrogate = user_id here for simplicity)
    con.execute("""
        CREATE OR REPLACE TABLE dim_user AS
        SELECT DISTINCT
            user_id                       AS user_key,
            'U' || CAST(user_id AS VARCHAR) AS user_natural_id,
            'User ' || CAST(user_id AS VARCHAR) AS user_label
        FROM staged;
    """)

    # fact_task — grain: one row per task; FKs to dims + measures
    con.execute("""
        CREATE OR REPLACE TABLE fact_task AS
        SELECT
            s.task_id,                                                    -- degenerate dim
            CAST(strftime(s.activity_date, '%Y%m%d') AS INTEGER) AS date_key,
            s.user_id                                            AS user_key,
            CAST(s.completed AS INTEGER)                         AS is_completed, -- additive
            s.title_length                                       AS title_length  -- additive
        FROM staged s;
    """)

    n = con.execute("SELECT COUNT(*) FROM fact_task").fetchone()[0]
    print(f"[load] star built: fact_task={n} rows, "
          f"dim_user={con.execute('SELECT COUNT(*) FROM dim_user').fetchone()[0]}, "
          f"dim_date={con.execute('SELECT COUNT(*) FROM dim_date').fetchone()[0]}")


# ---------------------------------------------------------------------------
# Analytical query over the star
# ---------------------------------------------------------------------------
def report(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Analytical report: task completion by user ===")
    df = con.execute("""
        SELECT
            u.user_label,
            COUNT(*)                        AS total_tasks,
            SUM(f.is_completed)             AS completed_tasks,
            ROUND(100.0 * SUM(f.is_completed) / COUNT(*), 1) AS pct_complete,
            ROUND(AVG(f.title_length), 1)   AS avg_title_len
        FROM fact_task f
        JOIN dim_user u ON f.user_key = u.user_key
        GROUP BY u.user_label
        ORDER BY completed_tasks DESC, u.user_label
    """).fetchdf()
    print(df.to_string(index=False))

    print("\n=== Completion by weekend vs. weekday (uses dim_date) ===")
    df2 = con.execute("""
        SELECT
            CASE WHEN d.is_weekend THEN 'weekend' ELSE 'weekday' END AS day_type,
            COUNT(*)            AS tasks,
            SUM(f.is_completed) AS completed
        FROM fact_task f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY day_type
        ORDER BY day_type
    """).fetchdf()
    print(df2.to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(description="Mini E->T->L pipeline (Day 5 capstone demo)")
    ap.add_argument("--offline", action="store_true",
                    help="skip the API and use the shipped sample file")
    args = ap.parse_args()

    print("--- E: EXTRACT ---")
    records = extract(offline=args.offline)

    print("\n--- T: TRANSFORM ---")
    df = transform(records)
    quality_gate(df)

    print("\n--- L: LOAD (star schema in DuckDB) ---")
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()                 # idempotent: fresh warehouse each run
    con = duckdb.connect(str(WAREHOUSE))
    load(df, con)

    report(con)
    con.close()
    print(f"\nDone. Warehouse written to {WAREHOUSE.name}. "
          f"Open it: duckdb {WAREHOUSE.name}")


if __name__ == "__main__":
    sys.exit(main())
