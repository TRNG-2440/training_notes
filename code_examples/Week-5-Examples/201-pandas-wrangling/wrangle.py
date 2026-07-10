"""
201 - Pandas wrangling demo.

Walks through the core pandas operations from notes/201-pandas-refresher.md
against a tiny sales dataset, printing the result of each step so you can
watch the transformation happen.

Run:
    pip install -r requirements.txt
    python wrangle.py
"""

from pathlib import Path
import pandas as pd
import numpy as np

HERE = Path(__file__).parent


def banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    # ------------------------------------------------------------------
    # 1. LOAD  ---------------------------------------------------------
    # ------------------------------------------------------------------
    banner("1. LOAD  (read_csv, parse dates)")
    sales = pd.read_csv(HERE / "sales.csv", parse_dates=["order_date"])
    print(sales.head())

    # ------------------------------------------------------------------
    # 2. INSPECT  ------------------------------------------------------
    # ------------------------------------------------------------------
    banner("2. INSPECT  (shape / dtypes / info / describe)")
    print("shape:", sales.shape)
    print("\ndtypes:\n", sales.dtypes)
    print("\ninfo():")
    sales.info()
    print("\ndescribe():\n", sales.describe())

    banner("2b. MISSING VALUES  (isna().sum())")
    # Note: quantity and unit_price each have one blank cell in the CSV.
    print(sales.isna().sum())

    # ------------------------------------------------------------------
    # 3. SELECTION  ----------------------------------------------------
    # ------------------------------------------------------------------
    banner("3. SELECTION  ([] vs .loc vs .iloc)")
    print("single column -> Series:\n", sales["customer"].head(3))
    print("\ntwo columns -> DataFrame:\n", sales[["customer", "region"]].head(3))
    print("\n.loc[0, 'customer']:", sales.loc[0, "customer"])
    print(".iloc[0, 1] (first row, 2nd col):", sales.iloc[0, 1])

    # ------------------------------------------------------------------
    # 4. HANDLE MISSING VALUES  ----------------------------------------
    # ------------------------------------------------------------------
    banner("4. CLEAN  (fill missing values)")
    # unit_price: fill the blank with the average price of its category.
    sales["unit_price"] = sales["unit_price"].fillna(
        sales.groupby("category")["unit_price"].transform("mean")
    )
    # quantity: a missing quantity most sensibly defaults to 1.
    sales["quantity"] = sales["quantity"].fillna(1).astype(int)
    print("missing after cleaning:\n", sales.isna().sum())

    # ------------------------------------------------------------------
    # 5. DERIVED COLUMNS  ----------------------------------------------
    # ------------------------------------------------------------------
    banner("5. DERIVE  (revenue + a big/small flag)")
    sales["revenue"] = (sales["quantity"] * sales["unit_price"]).round(2)
    sales["size"] = np.where(sales["revenue"] >= 100, "big", "small")
    print(sales[["order_id", "quantity", "unit_price", "revenue", "size"]].head())

    # ------------------------------------------------------------------
    # 6. FILTER  (boolean masks)  --------------------------------------
    # ------------------------------------------------------------------
    banner("6. FILTER  (boolean masks / .isin)")
    east_big = sales[(sales["region"] == "East") & (sales["revenue"] >= 100)]
    print("East orders with revenue >= 100:\n",
          east_big[["order_id", "customer", "revenue"]])
    print("\nWidgets or Gadgets only (isin):",
          len(sales[sales["category"].isin(["Widgets", "Gadgets"])]), "rows")

    # ------------------------------------------------------------------
    # 7. GROUPBY + AGG  ------------------------------------------------
    # ------------------------------------------------------------------
    banner("7. AGGREGATE  (groupby + agg, then sort)")
    by_category = (
        sales.groupby("category")
        .agg(orders=("order_id", "count"),
             total_revenue=("revenue", "sum"),
             avg_revenue=("revenue", "mean"))
        .round(2)
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    print(by_category)

    # ------------------------------------------------------------------
    # 8. MERGE  --------------------------------------------------------
    # ------------------------------------------------------------------
    banner("8. MERGE  (join region lookup, compare to target)")
    regions = pd.read_csv(HERE / "regions.csv")
    by_region = (
        sales.groupby("region")["revenue"].sum()
        .reset_index()
        .rename(columns={"revenue": "actual"})
    )
    scorecard = by_region.merge(regions, on="region", how="left")
    scorecard["pct_of_target"] = (
        (scorecard["actual"] / scorecard["target"] * 100).round(1)
    )
    print(scorecard)

    # ------------------------------------------------------------------
    # 9. CONCAT  -------------------------------------------------------
    # ------------------------------------------------------------------
    banner("9. CONCAT  (stack two subsets back together)")
    east = sales[sales["region"] == "East"]
    west = sales[sales["region"] == "West"]
    stacked = pd.concat([east, west], ignore_index=True)
    print("East rows:", len(east), "+ West rows:", len(west),
          "-> concat:", len(stacked))

    # ------------------------------------------------------------------
    # 10. EXPORT  ------------------------------------------------------
    # ------------------------------------------------------------------
    banner("10. EXPORT  (write the cleaned data to Parquet)")
    out = HERE / "sales_clean.parquet"
    sales.to_parquet(out, index=False)
    print(f"wrote {out.name} ({out.stat().st_size:,} bytes)")
    print("read back OK ->", pd.read_parquet(out).shape)


if __name__ == "__main__":
    main()
