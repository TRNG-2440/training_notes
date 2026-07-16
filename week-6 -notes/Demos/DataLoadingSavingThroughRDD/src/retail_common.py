from __future__ import annotations

import csv
import itertools
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from pyspark.sql import SparkSession


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DIR = PROJECT_ROOT / "output" / "generated"

ORDER_FIELDS = [
    "order_id",
    "order_date",
    "customer_id",
    "city",
    "category",
    "quantity",
    "unit_price",
    "discount_pct",
    "status",
]


def create_spark(app_name: str) -> SparkSession:
    """Create a local Spark session suitable for Windows training demos."""

    os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[2]")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.ui.enabled", "false")
        .config("spark.python.worker.faulthandler.enabled", "true")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")
    return spark


def file_uri(path: Path) -> str:
    """
    Return a Spark-compatible local path.

    On Windows, returning a POSIX-style path avoids encoding spaces
    as %20, which may cause local Hadoop path problems.
    """

    resolved_path = path.resolve()

    if os.name == "nt":
        return resolved_path.as_posix()

    return resolved_path.as_uri()


def reset_directory(path: Path) -> None:
    """Delete an existing output directory before Spark writes to it."""

    if path.exists():
        shutil.rmtree(path)


def parse_order_partition(
    lines: Iterator[str],
) -> Iterator[dict[str, Any]]:
    """Parse CSV records inside each Spark partition."""

    reader = csv.reader(lines)

    for values in reader:
        try:
            if len(values) != 9:
                yield {
                    "_error": "INVALID_COLUMN_COUNT",
                    "_raw": values,
                }
                continue

            row = dict(zip(ORDER_FIELDS, values))

            row["order_id"] = int(row["order_id"])
            datetime.strptime(row["order_date"], "%Y-%m-%d")
            row["quantity"] = int(row["quantity"])
            row["unit_price"] = float(row["unit_price"])
            row["discount_pct"] = float(row["discount_pct"])

            row["city"] = row["city"].strip()
            row["category"] = row["category"].strip()
            row["status"] = row["status"].strip().upper()

            yield row

        except (ValueError, KeyError, TypeError):
            yield {
                "_error": "PARSE_ERROR",
                "_raw": values,
            }


def validate_order(
    row: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Validate one parsed retail order."""

    if "_error" in row:
        return False, [row["_error"]]

    reasons: list[str] = []

    if not row["city"]:
        reasons.append("MISSING_CITY")

    if not row["category"]:
        reasons.append("MISSING_CATEGORY")

    if row["quantity"] <= 0:
        reasons.append("INVALID_QUANTITY")

    if row["unit_price"] < 0:
        reasons.append("INVALID_UNIT_PRICE")

    if not 0 <= row["discount_pct"] <= 100:
        reasons.append("INVALID_DISCOUNT")

    if row["status"] not in {
        "COMPLETED",
        "CANCELLED",
        "RETURNED",
    }:
        reasons.append("INVALID_STATUS")

    return len(reasons) == 0, reasons


def classify_order(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Classify a row as valid or rejected and calculate amounts."""

    valid, reasons = validate_order(row)

    if not valid:
        return {
            "valid": False,
            "row": row,
            "reasons": reasons,
        }

    gross_amount = row["quantity"] * row["unit_price"]

    enriched_row = {
        **row,
        "gross_amount": round(gross_amount, 2),
        "net_amount": round(
            gross_amount
            * (1 - row["discount_pct"] / 100.0),
            2,
        ),
    }

    return {
        "valid": True,
        "row": enriched_row,
        "reasons": [],
    }


def add_header(
    index: int,
    rows: Iterator[str],
    header: str,
):
    """Add a header only to the first output partition."""

    return itertools.chain(
        [header] if index == 0 else [],
        rows,
    )


def csv_escape(value: Any) -> str:
    """Escape a value so it can be safely written to CSV."""

    text = "" if value is None else str(value)

    if any(character in text for character in [",", '"', "\n"]):
        return '"' + text.replace('"', '""') + '"'

    return text