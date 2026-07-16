"""
AWS EMR RDD loading and saving demo.

Loads retail_orders.csv from Amazon S3, calculates completed-order
revenue by category, and saves the output back to Amazon S3.

Example:

spark-submit 06_rdd_aws_loading_saving_demo.py \
  --input s3://geetha-pyspark-rdd-demo-2026/rdd-demo/input/retail_orders.csv \
  --output s3://geetha-pyspark-rdd-demo-2026/rdd-demo/output/run-001/
"""

from __future__ import annotations

import argparse
import csv
from io import StringIO
from typing import Iterator

from pyspark.sql import SparkSession


def parse_arguments() -> argparse.Namespace:
    """Read the input and output S3 paths supplied to spark-submit."""

    parser = argparse.ArgumentParser(
        description="Calculate completed revenue by category using RDDs."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="S3 URI of retail_orders.csv",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="New S3 output prefix",
    )

    return parser.parse_args()


def parse_csv_line(line: str) -> list[str]:
    """Convert one CSV line into a list of values."""

    return next(csv.reader(StringIO(line)))


def parse_completed_order(
    values: list[str],
) -> tuple[str, float]:
    """
    Convert a completed order into:

        (category, net_amount)
    """

    category = values[4].strip()
    quantity = int(values[5])
    unit_price = float(values[6])
    discount_pct = float(values[7])

    gross_amount = quantity * unit_price

    net_amount = gross_amount * (
        1 - discount_pct / 100.0
    )

    return category, net_amount


def format_output_partition(
    partition_index: int,
    rows: Iterator[tuple[str, float]],
) -> Iterator[str]:
    """Convert Pair-RDD rows to CSV-formatted strings."""

    if partition_index == 0:
        yield "category,total_completed_revenue"

    for category, revenue in rows:
        yield f"{category},{revenue:.2f}"


def main() -> None:
    args = parse_arguments()

    # No master("local[2]") is set.
    # EMR spark-submit connects the application to YARN.
    spark = (
        SparkSession.builder
        .appName("RDD-AWS-Loading-Saving-Demo")
        .getOrCreate()
    )

    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    try:
        input_path = args.input
        output_path = args.output.rstrip("/")

        print("\nAWS RDD DEMO")
        print("Input :", input_path)
        print("Output:", output_path)

        # ----------------------------------------------------------
        # STEP 1: Load CSV lines from Amazon S3.
        # ----------------------------------------------------------
        raw_lines_rdd = sc.textFile(
            input_path,
            minPartitions=2,
        )

        header = raw_lines_rdd.first()

        # ----------------------------------------------------------
        # STEP 2: Remove header and blank lines.
        # ----------------------------------------------------------
        data_lines_rdd = raw_lines_rdd.filter(
            lambda line: (
                line != header
                and line.strip() != ""
            )
        )

        # ----------------------------------------------------------
        # STEP 3: Parse CSV records.
        # ----------------------------------------------------------
        parsed_rdd = data_lines_rdd.map(
            parse_csv_line
        )

        # ----------------------------------------------------------
        # STEP 4: Keep valid completed orders.
        # ----------------------------------------------------------
        completed_orders_rdd = parsed_rdd.filter(
            lambda values: (
                len(values) == 9
                and values[8].strip().upper()
                == "COMPLETED"
            )
        )

        # ----------------------------------------------------------
        # STEP 5: Create Pair RDD:
        #
        #     (category, net_amount)
        # ----------------------------------------------------------
        category_revenue_pair_rdd = (
            completed_orders_rdd
            .map(parse_completed_order)
        )

        # ----------------------------------------------------------
        # STEP 6: Calculate revenue by category.
        # ----------------------------------------------------------
        revenue_by_category_rdd = (
            category_revenue_pair_rdd
            .reduceByKey(
                lambda left, right: left + right
            )
            .mapValues(
                lambda revenue: round(revenue, 2)
            )
            .sortBy(
                lambda item: item[1],
                ascending=False,
            )
        )

        print("\nRESULT PREVIEW")

        for category, revenue in (
            revenue_by_category_rdd.take(20)
        ):
            print(
                f"{category:20} {revenue:12.2f}"
            )

        # ----------------------------------------------------------
        # STEP 7: Convert Pair-RDD records to CSV strings.
        # ----------------------------------------------------------
        output_lines_rdd = (
            revenue_by_category_rdd
            .coalesce(1)
            .mapPartitionsWithIndex(
                format_output_partition
            )
        )

        # ----------------------------------------------------------
        # STEP 8: Save the result directly to Amazon S3.
        # ----------------------------------------------------------
        output_lines_rdd.saveAsTextFile(
            output_path
        )

        print("\nOUTPUT SAVED SUCCESSFULLY")
        print(output_path)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()