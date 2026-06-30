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


def profile(filepath):
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sales_profiler.py <path_to_csv>")
        sys.exit(1)
    profile(sys.argv[1])
