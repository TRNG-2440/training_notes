import csv
import sys
from collections import defaultdict


def read_csv(filepath):
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def profile_column(values):
    """
    Profile a single column of data. Returns a dictionary with statistics about the column, including:
    - total: total number of values
    - non_null: number of non-null values
    - null_count: number of null values
    - null_pct: percentage of null values
    - distinct: number of distinct values
    - type: "numeric" or "text"
    """
    non_null = [v for v in values if v.strip() != ""]
    null_count = len(values) - len(non_null)

    numeric_values = []
    for v in non_null:
        try:
            numeric_values.append(float(v.replace(",", "").replace("$", "")))
        except ValueError:
            pass

    result = {
        "total": len(values),
        "non_null": len(non_null),
        "null_count": null_count,
        "null_pct": round(null_count / len(values) * 100, 1) if values else 0,
        "distinct": len(set(non_null)),
    }

    if numeric_values and len(numeric_values) == len(non_null):
        result["type"] = "numeric"
        result["min"] = min(numeric_values)
        result["max"] = max(numeric_values)
        result["mean"] = round(sum(numeric_values) / len(numeric_values), 2)
    else:
        result["type"] = "text"

    return result

def aggregate_sales_statistics(rows):
    """
    Aggregate sales statistics from a list of rows.
    Returns a dictionary with total sales, average quantity, and average unit price.
    """
    total_sales = 0.0
    total_quantity = 0.0
    total_unit_price = 0.0
    quantity_count = 0
    unit_price_count = 0

    for row in rows:
        total_sale = row.get("total_sale", "").strip()
        quantity = row.get("quantity", "").strip()
        unit_price = row.get("unit_price", "").strip()

        try:
            total_sales += float(total_sale.replace(",", "").replace("$", ""))
        except ValueError:
            pass

        try:
            total_quantity += float(quantity)
            quantity_count += 1
        except ValueError:
            pass

        try:
            total_unit_price += float(unit_price.replace(",", "").replace("$", ""))
            unit_price_count += 1
        except ValueError:
            pass

    return {
        "total_sales": round(total_sales, 2),
        "average_quantity": round(total_quantity / quantity_count, 2) if quantity_count else 0,
        "average_unit_price": round(total_unit_price / unit_price_count, 2) if unit_price_count else 0,
    }


def profile(filepath):
    """
    Profile a CSV file and print statistics about each column."""
    rows = read_csv(filepath)

    if not rows:
        print("No data found.")
        return

    columns = list(rows[0].keys())
    col_values = defaultdict(list)

    for row in rows:
        for col in columns:
            col_values[col].append(row.get(col, ""))

    print(f"\nFile: {filepath}")
    print(f"Rows: {len(rows)}")
    print(f"Columns: {len(columns)}")
    print("-" * 50)

    for col in columns:
        stats = profile_column(col_values[col])
        print(f"\n{col}")
        print(f"  Type:     {stats['type']}")
        print(f"  Non-null: {stats['non_null']} / {stats['total']}  ({stats['null_pct']}% missing)")
        print(f"  Distinct: {stats['distinct']}")
        if stats["type"] == "numeric":
            print(f"  Min:      {stats['min']}")
            print(f"  Max:      {stats['max']}")
            print(f"  Mean:     {stats['mean']}")

    stats = aggregate_sales_statistics(rows)
    print("\nSales summary:")
    print(f"  Total sales:       ${stats['total_sales']}")
    print(f"  Average quantity:  {stats['average_quantity']}")
    print(f"  Average unit price:${stats['average_unit_price']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sales_profiler.py <path_to_csv>")
        sys.exit(1)
    profile(sys.argv[1])
