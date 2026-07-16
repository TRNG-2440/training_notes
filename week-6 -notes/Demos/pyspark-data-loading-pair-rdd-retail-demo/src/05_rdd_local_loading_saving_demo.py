"""
05_rdd_local_loading_saving_demo.py

Beginner-friendly PySpark RDD demo for:

1. Loading a local CSV file with sc.textFile()
2. Removing the header
3. Parsing CSV rows
4. Filtering completed orders
5. Creating a Pair RDD
6. Aggregating revenue by category
7. Saving the result to the local output folder

This demo does not require a Hadoop cluster, HDFS, YARN, or Kubernetes.
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Iterator

from retail_common import DATA_DIR, GENERATED_DIR, create_spark, file_uri, reset_directory


def parse_csv_line(line: str) -> list[str]:
    """Convert one CSV line into a list of values."""
    return next(csv.reader(StringIO(line)))


def format_output_partition(
    partition_index: int,
    rows: Iterator[tuple[str, float]],
) -> Iterator[str]:
    """Convert Pair-RDD rows into CSV text and add one header."""
    if partition_index == 0:
        yield "category,total_completed_revenue"

    for category, revenue in rows:
        yield f"{category},{revenue:.2f}"


def main() -> None:
    # STEP 1: Create Spark in local mode.
    spark = create_spark("05_RDD_Local_Loading_And_Saving")
    sc = spark.sparkContext

    try:
        # STEP 2: Define local paths.
        input_path: Path = DATA_DIR / "retail_orders.csv"
        output_path: Path = GENERATED_DIR / "completed_revenue_by_category"

        print("\nSTEP 1 - INPUT AND OUTPUT PATHS")
        print("Input CSV :", input_path)
        print("Output dir:", output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file was not found: {input_path}\n"
                "Place retail_orders.csv inside the data folder."
            )

        # Spark will not overwrite an existing output directory.
        reset_directory(output_path)

        # STEP 3: Load the local CSV as RDD[str].
        raw_lines_rdd = sc.textFile(file_uri(input_path), minPartitions=2)

        print("\nSTEP 2 - RAW FILE LOADING")
        print("Total lines    :", raw_lines_rdd.count())
        print("First CSV line :", raw_lines_rdd.first())

        # STEP 4: Remove header and empty lines.
        header = raw_lines_rdd.first()
        data_lines_rdd = raw_lines_rdd.filter(
            lambda line: line != header and line.strip() != ""
        )

        print("\nSTEP 3 - HEADER REMOVAL")
        print("Data rows after removing header:", data_lines_rdd.count())

        # STEP 5: Parse each CSV line.
        parsed_rdd = data_lines_rdd.map(parse_csv_line)

        print("\nSTEP 4 - CSV PARSING")
        print("First parsed row:", parsed_rdd.first())

        # Expected columns:
        # 0 order_id, 1 order_date, 2 customer_id, 3 city,
        # 4 category, 5 quantity, 6 unit_price,
        # 7 discount_pct, 8 status
        completed_orders_rdd = parsed_rdd.filter(
            lambda values: len(values) == 9
            and values[8].strip().upper() == "COMPLETED"
        )

        print("\nSTEP 5 - FILTERING")
        print("Completed order rows:", completed_orders_rdd.count())

        # STEP 6: Create Pair RDD: (category, net_amount).
        category_revenue_pair_rdd = completed_orders_rdd.map(
            lambda values: (
                values[4].strip(),
                int(values[5])
                * float(values[6])
                * (1 - float(values[7]) / 100.0),
            )
        )

        print("\nSTEP 6 - PAIR RDD CREATION")
        for item in category_revenue_pair_rdd.take(5):
            print(" ", item)

        # STEP 7: Add revenue values for each category.
        revenue_by_category_rdd = (
            category_revenue_pair_rdd
            .reduceByKey(lambda left, right: left + right)
            .mapValues(lambda revenue: round(revenue, 2))
            .sortBy(lambda item: item[1], ascending=False)
        )

        print("\nSTEP 7 - AGGREGATED RESULT")
        for category, revenue in revenue_by_category_rdd.collect():
            print(f"{category:20} {revenue:12.2f}")

        # STEP 8: Convert tuples into CSV text.
        # coalesce(1) is suitable only for this small training demo.
        output_lines_rdd = (
            revenue_by_category_rdd
            .coalesce(1)
            .mapPartitionsWithIndex(format_output_partition)
        )
        output_rows = revenue_by_category_rdd.collect()

        # STEP 9: Save using Python instead of saveAsTextFile().
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / "completed_revenue_by_category.csv"

        with output_file.open(
            mode="w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(
                ["category", "total_completed_revenue"]
            )

            for category, revenue in output_rows:
                writer.writerow(
                    [category, f"{revenue:.2f}"]
                )

        print("\nSTEP 8 - SAVING")
        print("Output file:", output_file)

        # STEP 10: Load the saved file again using Python.
        print("\nSTEP 9 - VERIFY SAVED OUTPUT")

        with output_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line in file:
                print(line.rstrip())

        print("\nDEMO COMPLETED SUCCESSFULLY")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
