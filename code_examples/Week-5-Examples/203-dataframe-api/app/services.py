"""Service layer — all the pandas/data logic lives here.

This layer knows NOTHING about HTTP. It loads the dataset once and exposes plain
functions that return lists of dicts (JSON-ready). If the data source later
changes from a CSV to BigQuery, only this file changes.
"""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).parent.parent / "data" / "sales.csv"

_DF: pd.DataFrame | None = None


def load_data() -> pd.DataFrame:
    """Read the CSV once, cache it, and add a derived `revenue` column.

    Called at startup (see main.py lifespan) so the file is read a single time
    for the whole process, not on every request.
    """
    global _DF
    if _DF is None:
        df = pd.read_csv(DATA_FILE, parse_dates=["order_date"])
        df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
        _DF = df
    return _DF


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list of dicts, with NaN turned into None (valid JSON)."""
    df = df.copy()
    if "order_date" in df.columns:
        df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    return df.where(df.notna(), None).to_dict(orient="records")


def summary() -> dict:
    """Overall totals across the whole dataset."""
    df = load_data()
    return {
        "orders": int(len(df)),
        "total_revenue": round(float(df["revenue"].sum()), 2),
        "avg_order_revenue": round(float(df["revenue"].mean()), 2),
        "customers": int(df["customer"].nunique()),
    }


def by_category() -> list[dict]:
    """Aggregate revenue per category (GROUP BY category)."""
    df = load_data()
    agg = (
        df.groupby("category")
        .agg(orders=("order_id", "count"),
             total_revenue=("revenue", "sum"),
             avg_revenue=("revenue", "mean"))
        .round(2)
        .reset_index()                        # group key -> column
        .sort_values("total_revenue", ascending=False)
    )
    return _records(agg)


def orders_page(limit: int, offset: int, region: str | None) -> dict:
    """Paginated raw orders, with an optional region filter."""
    df = load_data()
    if region:
        df = df[df["region"] == region]
    total = len(df)
    page = df.iloc[offset:offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": _records(page),
    }
