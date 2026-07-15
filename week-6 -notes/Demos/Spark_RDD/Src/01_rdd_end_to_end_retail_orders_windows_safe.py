from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

# Set this before importing PySpark so the stage progress bar is disabled.
os.environ.setdefault(
    "PYSPARK_SUBMIT_ARGS",
    "--conf spark.ui.showConsoleProgress=false pyspark-shell",
)

from pyspark import SparkContext
from pyspark.sql import SparkSession


# ---------------------------------------------------------------------------
# Type aliases make the code easier for a beginner to read.
# ---------------------------------------------------------------------------

Order = Dict[str, Any]
ValidationResult = Dict[str, Any]


# ---------------------------------------------------------------------------
# STEP 1 — Locate the attached CSV automatically.
# ---------------------------------------------------------------------------

def find_csv_file() -> Path:
    """
    Search common VS Code project locations for retail_orders.csv.

    This avoids hard-coding a full Windows path such as:
    C:/Personal/.../retail_orders.csv
    """
    script_directory = Path(__file__).resolve().parent

    candidates = [
        script_directory / "retail_orders.csv",
        script_directory / "data" / "retail_orders.csv",
        script_directory.parent / "retail_orders.csv",
        script_directory.parent / "data" / "retail_orders.csv",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    searched = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(
        "retail_orders.csv was not found.\n"
        "Place it beside this Python file or inside a data folder.\n"
        f"Searched:\n{searched}"
    )


# ---------------------------------------------------------------------------
# Convert a local Path to a Spark/Hadoop-friendly Windows path.
# ---------------------------------------------------------------------------

def prepare_spark_input(source_path: Path) -> tuple[Path, str]:
    """
    Prepare a local file path that Spark/Hadoop can read reliably on Windows.

    Some Windows Hadoop setups fail to resolve local paths containing spaces,
    even though Python can read the same file. On Windows, copy the CSV to a
    simple directory directly under the system drive:

        C:/spark_rdd_input/retail_orders.csv

    The original source file is not changed.
    """
    resolved_source = source_path.resolve()

    if not resolved_source.is_file():
        raise FileNotFoundError(
            f"Python cannot find the CSV file: {resolved_source}"
        )

    if os.name == "nt":
        system_drive = os.environ.get("SystemDrive", "C:")
        staging_directory = Path(f"{system_drive}/spark_rdd_input")
        staging_directory.mkdir(parents=True, exist_ok=True)

        staged_file = staging_directory / resolved_source.name
        shutil.copy2(resolved_source, staged_file)
        spark_path = staged_file.resolve().as_posix()

        return staged_file.resolve(), spark_path

    return resolved_source, resolved_source.as_posix()


# ---------------------------------------------------------------------------
# STEP 2 — Create a quiet local SparkSession for VS Code.
# ---------------------------------------------------------------------------

def create_spark() -> SparkSession:
    """Create one local SparkSession using four worker threads."""
    project_directory = Path(__file__).resolve().parent
    spark_temp = project_directory / ".spark-temp"
    spark_warehouse = project_directory / ".spark-warehouse"

    spark_temp.mkdir(exist_ok=True)
    spark_warehouse.mkdir(exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("RetailOrdersRDDStepByStep")
        .master("local[4]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.local.dir", str(spark_temp))
        .config("spark.sql.warehouse.dir", str(spark_warehouse))
        .getOrCreate()
    )

    # ERROR produces much cleaner training output than WARN.
    spark.sparkContext.setLogLevel("ERROR")
    return spark


# ---------------------------------------------------------------------------
# STEP 3 — Small printing helpers.
# ---------------------------------------------------------------------------

def section(number: str, title: str) -> None:
    """Print a visible section heading."""
    print("\n" + "=" * 92)
    print(f"STEP {number} — {title}")
    print("=" * 92)


def show(title: str, values: List[Any]) -> None:
    """Display a small driver-side result."""
    print(f"\n{title}")
    print("-" * len(title))

    if not values:
        print("(no records)")
        return

    for value in values:
        print(value)


def money(value: float) -> str:
    """Format a numeric amount."""
    return f"{value:,.2f}"


# ---------------------------------------------------------------------------
# STEP 4 — Remove only the CSV header.
# ---------------------------------------------------------------------------

def remove_header(
    partition_index: int,
    lines: Iterator[str],
) -> Iterator[str]:
    """
    textFile() creates an RDD of lines.

    The header exists only at the beginning of the first partition, so this
    function skips one line only when partition_index == 0.
    """
    if partition_index == 0:
        next(lines, None)

    yield from lines


# ---------------------------------------------------------------------------
# STEP 5 — Parse and validate one CSV line.
# ---------------------------------------------------------------------------

def parse_and_validate(line: str) -> ValidationResult:
    """
    Convert one CSV line into typed Python values.

    The attached file intentionally contains data-quality issues:
    - a missing city
    - a negative quantity
    - a discount above 100

    Instead of crashing, this function returns either:
    {
        "is_valid": True,
        "record": {...},
        "errors": []
    }

    or:
    {
        "is_valid": False,
        "record": {... or None},
        "errors": [...]
    }
    """
    try:
        row = next(csv.reader([line]))

        if len(row) != 9:
            return {
                "is_valid": False,
                "record": None,
                "raw_line": line,
                "errors": [
                    f"Expected 9 columns but received {len(row)}"
                ],
            }

        order: Order = {
            "order_id": int(row[0]),
            "order_date": row[1].strip(),
            "customer_id": row[2].strip(),
            "city": row[3].strip(),
            "category": row[4].strip(),
            "quantity": int(row[5]),
            "unit_price": float(row[6]),
            "discount_pct": float(row[7]),
            "status": row[8].strip().upper(),
        }

        errors: List[str] = []

        if not order["customer_id"]:
            errors.append("customer_id is missing")

        if not order["city"]:
            errors.append("city is missing")

        if not order["category"]:
            errors.append("category is missing")

        if order["quantity"] <= 0:
            errors.append("quantity must be greater than zero")

        if order["unit_price"] <= 0:
            errors.append("unit_price must be greater than zero")

        if not 0 <= order["discount_pct"] <= 100:
            errors.append("discount_pct must be between 0 and 100")

        allowed_statuses = {"COMPLETED", "CANCELLED", "RETURNED"}

        if order["status"] not in allowed_statuses:
            errors.append(
                "status must be COMPLETED, CANCELLED, or RETURNED"
            )

        return {
            "is_valid": len(errors) == 0,
            "record": order,
            "raw_line": line,
            "errors": errors,
        }

    except (ValueError, csv.Error) as error:
        return {
            "is_valid": False,
            "record": None,
            "raw_line": line,
            "errors": [f"Parsing error: {error}"],
        }


# ---------------------------------------------------------------------------
# STEP 6 — Add calculated business columns using map().
# ---------------------------------------------------------------------------

def add_amounts(order: Order) -> Order:
    """
    RDDs are immutable, so return a new dictionary rather than changing the
    original record.

    gross_amount = quantity * unit_price
    discount_amount = gross_amount * discount_pct / 100
    net_amount = gross_amount - discount_amount
    """
    gross_amount = order["quantity"] * order["unit_price"]
    discount_amount = gross_amount * order["discount_pct"] / 100
    net_amount = gross_amount - discount_amount

    return {
        **order,
        "gross_amount": round(gross_amount, 2),
        "discount_amount": round(discount_amount, 2),
        "net_amount": round(net_amount, 2),
    }


# ---------------------------------------------------------------------------
# STEP 7 — Main program.
# ---------------------------------------------------------------------------

def main() -> None:
    csv_path = find_csv_file()
    staged_csv_path, spark_csv_path = prepare_spark_input(csv_path)
    spark = create_spark()
    sc: SparkContext = spark.sparkContext

    try:
        # ===================================================================
        # RDD CREATION METHOD 1: parallelize()
        # ===================================================================

        section("1", "RDD creation using parallelize()")

        category_master_data = [
            ("Electronics", {"department": "Durables", "tax_pct": 18.0}),
            ("Fashion", {"department": "Lifestyle", "tax_pct": 12.0}),
            ("Grocery", {"department": "Daily Needs", "tax_pct": 5.0}),
        ]

        category_master_rdd = sc.parallelize(
                category_master_data,
                numSlices=2,
            )

        # print(
        #     "parallelize() converts a small Python collection in driver "
        #     "memory into a distributed RDD."
        # )
        # print("Category master partitions:",
        #       category_master_rdd.getNumPartitions())
        # show(
        #     "Category master records:",
        #     category_master_rdd.collect(),
        # )

        # # ===================================================================
        # # RDD CREATION METHOD 2: textFile()
        # # ===================================================================

        # section("2", "RDD creation using textFile()")

        # print("Original CSV path:", csv_path)
        # print("Python sees original file:", csv_path.is_file())
        # print("Staged CSV path:", staged_csv_path)
        # print("Python sees staged file:", staged_csv_path.is_file())
        # print("Spark/Hadoop input path:", spark_csv_path)

        raw_lines_rdd = sc.textFile(
            spark_csv_path,
            minPartitions=4,
        ).setName("RawRetailOrderLines")

        print(
            "textFile() creates an RDD[str]. Normally, each element is one "
            "line from the source file."
        )
        print("Raw partitions:", raw_lines_rdd.getNumPartitions())
        print("First raw line:", raw_lines_rdd.first())

        # # ===================================================================
        # # RDD CREATION METHOD 3: wholeTextFiles()
        # # ===================================================================

        # section("3", "RDD creation using wholeTextFiles()")

        # whole_file_rdd = sc.wholeTextFiles(spark_csv_path)

        # whole_file_summary = whole_file_rdd.map(
        #     lambda pair: {
        #         "file": pair[0].split("/")[-1],
        #         "characters": len(pair[1]),
        #         "line_count": len(pair[1].splitlines()),
        #     }
        # )

        # print(
        #     "wholeTextFiles() creates one (file_path, complete_content) "
        #     "record per file. It is shown only for comparison; textFile() "
        #     "is more suitable for this line-oriented CSV."
        # )
        # show(
        #     "Whole-file summary:",
        #     whole_file_summary.collect(),
        # )

        # # ===================================================================
        # # RDD CREATION METHOD 4: emptyRDD()
        # # ===================================================================

        # section("4", "RDD creation using emptyRDD()")

        # empty_rdd = sc.emptyRDD()

        # print(
        #     "emptyRDD() is useful when a function must return an RDD even "
        #     "when no input data is available."
        # )
        # print("Empty RDD count:", empty_rdd.count())
        # print("Empty RDD partitions:", empty_rdd.getNumPartitions())

        # empty_rdd_with_partitions = sc.parallelize([],numSlices=4,)

        # print("Count:", empty_rdd_with_partitions.count())
        # print(
        #     "Partitions:",
        #     empty_rdd_with_partitions.getNumPartitions(),
        # )
        # print("Data:", empty_rdd_with_partitions.collect())
        
        
        # # ===================================================================
        # # TRANSFORMATION: mapPartitionsWithIndex()
        # # TRANSFORMATION: filter()
        # # ===================================================================

        # section("5", "Remove the header and blank lines")

        data_lines_rdd = (
            raw_lines_rdd
            .mapPartitionsWithIndex(remove_header)
            .filter(lambda line: bool(line.strip()))
            .setName("RetailOrderDataLines")
        )

        # print(
        #     "mapPartitionsWithIndex() removes the header only from the first "
        #     "partition. filter() removes empty lines."
        # )
        # print("CSV data-row count:", data_lines_rdd.count())
        # show(
        #     "First three data lines:",
        #     data_lines_rdd.take(3),
        # )

        # # ===================================================================
        # # TRANSFORMATION: map()
        # # TRANSFORMATION: filter()
        # # ===================================================================

        # # section("6", "Parse and validate the CSV")

        validation_rdd = (
            data_lines_rdd
            .map(parse_and_validate)
            .cache()
        )

        valid_orders_rdd = (
            validation_rdd
            .filter(lambda result: result["is_valid"])
            .map(lambda result: result["record"])
            .setName("ValidRetailOrders")
            .cache()
        )

        # invalid_orders_rdd = (
        #     validation_rdd
        #     .filter(lambda result: not result["is_valid"])
        #     .map(
        #         lambda result: {
        #             "order_id": (
        #                 result["record"]["order_id"]
        #                 if result["record"] is not None
        #                 else None
        #             ),
        #             "errors": result["errors"],
        #             "raw_line": result["raw_line"],
        #         }
        #     )
        #     .setName("InvalidRetailOrders")
        # )

        # print("Valid order count:", valid_orders_rdd.count())
        # print("Invalid order count:", invalid_orders_rdd.count())
        # show(
        #     "Invalid records and validation errors:",
        #     invalid_orders_rdd.collect(),
        # )

        # # ===================================================================
        # # TRANSFORMATION: map()
        # # ===================================================================

        section("7", "Calculate gross, discount, and net amounts")

        enriched_orders_rdd = (
            valid_orders_rdd
            .map(add_amounts)
            .setName("EnrichedRetailOrders")
            .cache()
        )

        # show(
        #     "First three enriched records:",
        #     enriched_orders_rdd.take(3),
        # )

        # # ===================================================================
        # # BASIC ACTIONS
        # # ===================================================================

        # section("8", "Basic RDD actions")

        # print("count() ->", enriched_orders_rdd.count())
        # print("first() ->", enriched_orders_rdd.first())
        # show("take(2) ->", enriched_orders_rdd.take(2))

        # status_counts = (
        #     enriched_orders_rdd
        #     .map(lambda order: order["status"])
        #     .countByValue()
        # )
        # print("\ncountByValue() status totals ->", dict(status_counts))

        # total_valid_net_amount = (
        #     enriched_orders_rdd
        #     .map(lambda order: order["net_amount"])
        #     .reduce(lambda left, right: left + right)
        # )
        # print(
        #     "reduce() total net amount for all valid rows ->",
        #     money(total_valid_net_amount),
        # )

        # # ===================================================================
        # # TRANSFORMATION: filter()
        # # ===================================================================

        # section("9", "Filter only completed orders")

        completed_orders_rdd = (
            enriched_orders_rdd
            .filter(lambda order: order["status"] == "COMPLETED")
            .setName("CompletedRetailOrders")
            .cache()
        )

        # print("Completed valid orders:", completed_orders_rdd.count())
        # show(
        #     "Completed-order sample:",
        #     completed_orders_rdd.take(5),
        # )

        # # ===================================================================
        # # TRANSFORMATION: distinct()
        # # ===================================================================

        # section("10", "Find distinct cities and categories")

        # distinct_cities = (
        #     valid_orders_rdd
        #     .map(lambda order: order["city"])
        #     .distinct()
        #     .sortBy(lambda city: city)
        # )

        # distinct_categories = (
        #     valid_orders_rdd
        #     .map(lambda order: order["category"])
        #     .distinct()
        #     .sortBy(lambda category: category)
        # )

        # show("Distinct cities:", distinct_cities.collect())
        # show("Distinct categories:", distinct_categories.collect())

        # # ===================================================================
        # # TRANSFORMATION: flatMap()
        # # ===================================================================

        # section("11", "Create searchable business tags using flatMap()")

        # order_tags_rdd = (
        #     valid_orders_rdd
        #     .flatMap(
        #         lambda order: [
        #             f"city:{order['city']}",
        #             f"category:{order['category']}",
        #             f"status:{order['status']}",
        #         ]
        #     )
        # )

        # tag_counts_rdd = (
        #     order_tags_rdd
        #     .map(lambda tag: (tag, 1))
        #     .reduceByKey(lambda left, right: left + right)
        #     .sortByKey()
        # )

        # print(
        #     "flatMap() produces multiple tag records from each single order."
        # )
        # show("Tag counts:", tag_counts_rdd.collect())

        # # ===================================================================
        # # TRANSFORMATION: map() -> Pair RDD
        # # TRANSFORMATION: reduceByKey()
        # # TRANSFORMATION: sortBy()
        # # ===================================================================

        # section("12", "Revenue by city using reduceByKey()")

        # city_revenue_rdd = (
        #     completed_orders_rdd
        #     .map(
        #         lambda order: (
        #             order["city"],
        #             order["net_amount"],
        #         )
        #     )
        #     .reduceByKey(
        #         lambda left, right: left + right,
        #         numPartitions=2,
        #     )
        #     .sortBy(
        #         keyfunc=lambda pair: pair[1],
        #         ascending=True,
        #     )
        #     .setName("CompletedRevenueByCity")
        # )

        # show(
        #     "Completed net revenue by city:",
        #     city_revenue_rdd
        #     .mapValues(money)
        #     .collect(),
        # )

        # print("\nLineage for city revenue:")
        # print(city_revenue_rdd.toDebugString().decode("utf-8"))

        # # ===================================================================
        # # TRANSFORMATION: reduceByKey()
        # # TRANSFORMATION: sortByKey()
        # # ACTION: collectAsMap()
        # # ===================================================================

        # section("13", "Revenue by category")

        category_revenue_rdd = (
            completed_orders_rdd
            .map(
                lambda order: (
                    order["category"],
                    order["net_amount"],
                )
            )
            .reduceByKey(lambda left, right: left + right)
            .sortByKey()
            .setName("CompletedRevenueByCategory")
        )

        # show(
        #     "Completed net revenue by category:",
        #     category_revenue_rdd
        #     .mapValues(money)
        #     .collect(),
        # )

        # category_revenue_map = category_revenue_rdd.collectAsMap()
        # print(
        #     "\ncollectAsMap() ->",
        #     {
        #         key: money(value)
        #         for key, value in category_revenue_map.items()
        #     },
        # )

        # # ===================================================================
        # # TRANSFORMATION: groupByKey()
        # # ===================================================================

        # section("14", "Group order IDs by category")

        # order_ids_by_category_rdd = (
        #     completed_orders_rdd
        #     .map(
        #         lambda order: (
        #             order["category"],
        #             order["order_id"],
        #         )
        #     )
        #     .groupByKey()
        #     .mapValues(lambda order_ids: sorted(order_ids))
        #     .sortByKey()
        # )

        # print(
        #     "groupByKey() is used here because the complete list of order "
        #     "IDs is required. Do not use groupByKey() merely to calculate "
        #     "a sum; reduceByKey() is more efficient for that."
        # )
        # show(
        #     "Order IDs grouped by category:",
        #     order_ids_by_category_rdd.collect(),
        # )

        # # ===================================================================
        # # TRANSFORMATION: keyBy()
        # # TRANSFORMATION: values()
        # # ===================================================================

        # section("15", "Create a Pair RDD using keyBy()")

        # orders_keyed_by_customer = completed_orders_rdd.keyBy(
        #     lambda order: order["customer_id"]
        # )

        # show(
        #     "First three (customer_id, order) pairs:",
        #     orders_keyed_by_customer.take(3),
        # )

        # show(
        #     "values() returns only the order dictionaries:",
        #     orders_keyed_by_customer.values().take(2),
        # )

        # # ===================================================================
        # # TRANSFORMATION: join()
        # # ===================================================================

        # section("16", "Join revenue with category master data")

        # category_business_summary_rdd = (
        #     category_revenue_rdd
        #     .join(category_master_rdd)
        #     .mapValues(
        #         lambda value: {
        #             "net_revenue": money(value[0]),
        #             "department": value[1]["department"],
        #             "tax_pct": value[1]["tax_pct"],
        #             "estimated_tax": money(
        #                 value[0] * value[1]["tax_pct"] / 100
        #             ),
        #         }
        #     )
        #     .sortByKey()
        # )

        # print(
        #     "join() matches records that have the same key in both Pair RDDs."
        # )
        # show(
        #     "Category business summary:",
        #     category_business_summary_rdd.collect(),
        # )

        # # ===================================================================
        # # TRANSFORMATION: union()
        # # ===================================================================

        # section("17", "Combine customer IDs using union()")

        # completed_customer_ids = (
        #     valid_orders_rdd
        #     .filter(lambda order: order["status"] == "COMPLETED")
        #     .map(lambda order: order["customer_id"])
        # )

        # non_completed_customer_ids = (
        #     valid_orders_rdd
        #     .filter(lambda order: order["status"] != "COMPLETED")
        #     .map(lambda order: order["customer_id"])
        # )

        # all_customer_ids_again = (
        #     completed_customer_ids
        #     .union(non_completed_customer_ids)
        #     .distinct()
        #     .sortBy(lambda customer_id: customer_id)
        # )

        # print(
        #     "union() appends both RDDs and keeps duplicates. distinct() is "
        #     "used afterward to return unique customer IDs."
        # )
        # show(
        #     "Unique customer IDs after union():",
        #     all_customer_ids_again.collect(),
        # )

        # ===================================================================
        # TRANSFORMATION: repartition()
        # TRANSFORMATION: coalesce()
        # ===================================================================

        # section("18", "Change the number of partitions")

        # print(
        #     "Original enriched partitions:",
        #     enriched_orders_rdd.getNumPartitions(),
        # )

        # repartitioned_rdd = enriched_orders_rdd.repartition(6)
        # print(
        #     "After repartition(6):",
        #     repartitioned_rdd.getNumPartitions(),
        # )

        # coalesced_rdd = repartitioned_rdd.coalesce(2)
        # print(
        #     "After coalesce(2):",
        #     coalesced_rdd.getNumPartitions(),
        # )

        # print(
        #     "repartition() performs a shuffle and can increase or decrease "
        #     "partitions. coalesce() is commonly used to reduce partitions "
        #     "with less data movement."
        # )

        # # ===================================================================
        # # ACTION: takeOrdered()
        # # ===================================================================

        section("19", "Find the top three completed orders")

        top_three = completed_orders_rdd.takeOrdered(
            3,
            key=lambda order: -order["net_amount"],
        )

        show(
            "Top three by net amount:",
            [
                (
                    order["order_id"],
                    order["customer_id"],
                    order["category"],
                    money(order["net_amount"]),
                )
                for order in top_three
            ],
        )

        # # ===================================================================
        # # FINAL SUMMARY
        # # ===================================================================

        section("20", "Expected summary for the attached CSV")

        print("CSV data rows                 : 14")
        print("Valid rows                    : 12")
        print("Invalid rows                  : 2")
        print("Valid COMPLETED rows          : 10")
        print("Completed net revenue         : 169,932.00")
        print("Completed Electronics revenue : 144,140.00")
        print("Completed Grocery revenue     : 6,452.00")
        print("Completed Fashion revenue     : 19,340.00")

        print(
            "\nThe expected totals above help you verify that the program "
            "is reading, validating, transforming, and aggregating the "
            "attached CSV correctly."
        )

        # Remove cached RDDs from memory when the training program is done.
        completed_orders_rdd.unpersist()
        enriched_orders_rdd.unpersist()
        valid_orders_rdd.unpersist()
        validation_rdd.unpersist()

    finally:
        spark.stop()


if __name__ == "__main__":
    main()