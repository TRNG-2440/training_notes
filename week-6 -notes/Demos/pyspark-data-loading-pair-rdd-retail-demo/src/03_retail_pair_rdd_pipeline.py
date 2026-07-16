"""Industry-standard retail data-loading, Pair-RDD, join, and saving demo."""
from __future__ import annotations
import json
from retail_common import (
    DATA_DIR,
    classify_order,
    create_spark,
    file_uri,
    parse_order_partition,
)


def add_metric(acc: tuple[int, int, float], value: tuple[int, int, float]):
    return (acc[0] + value[0], acc[1] + value[1], acc[2] + value[2])


def main() -> None:
    spark = create_spark("03_Retail_Pair_RDD_Industry_Pipeline")
    sc = spark.sparkContext

    orders_path = DATA_DIR / "retail_orders.csv"
    master_path = DATA_DIR / "category_master.csv"

    raw_orders = sc.textFile(file_uri(orders_path), 4)
    order_header = raw_orders.first()

    # Parse once, then classify every record as valid or rejected.
    classified = (
        raw_orders
        .filter(lambda line: line != order_header)
        .mapPartitions(parse_order_partition)
        .map(classify_order)
        .cache()
    )

    # Materialize all cached partitions once.
    input_count = classified.count()

    clean_orders = classified.filter(lambda item: item["valid"]).map(lambda item: item["row"]).cache()
    rejected_orders = classified.filter(lambda item: not item["valid"])

    # Completed sales only become reportable revenue.
    completed_orders = clean_orders.filter(lambda row: row["status"] == "COMPLETED")

    # Pair RDD: key = category; value = (order_count, units, net_revenue).
    category_metrics = completed_orders.map(
        lambda row: (
            row["category"],
            (1, row["quantity"], row["net_amount"]),
        )
    )

    # aggregateByKey combines values locally and then across shuffled partitions.
    category_summary = category_metrics.aggregateByKey(
        (0, 0, 0.0),
        add_metric,
        add_metric,
    )

    # Load the small category master as another Pair RDD.
    raw_master = sc.textFile(file_uri(master_path), 2)
    master_header = raw_master.first()
    category_master = (
        raw_master
        .filter(lambda line: line != master_header)
        .map(lambda line: line.split(","))
        .map(lambda values: (
            values[0],
            (values[1], values[2], float(values[3])),
        ))
    )

    # Inner join by category key.
    joined = category_summary.join(category_master)

    report_rdd = (
        joined
        .map(lambda item: {
            "category": item[0],
            "department": item[1][1][0],
            "manager": item[1][1][1],
            "completed_orders": item[1][0][0],
            "units_sold": item[1][0][1],
            "net_revenue": round(item[1][0][2], 2),
            "average_order_value": round(item[1][0][2] / item[1][0][0], 2),
            "monthly_target": item[1][1][2],
            "achievement_pct": round(item[1][0][2] / item[1][1][2] * 100, 2),
        })
        .sortBy(lambda row: row["net_revenue"], ascending=False)
        .cache()
    )

    clean_output = GENERATED_DIR / "cleaned_orders_rdd"
    reject_output = GENERATED_DIR / "rejected_orders_rdd"
    report_output = GENERATED_DIR / "category_sales_report_rdd"
    sequence_output = GENERATED_DIR / "category_report_sequence"

    for path in [clean_output, reject_output, report_output, sequence_output]:
        reset_directory(path)

    clean_header = "order_id,order_date,customer_id,city,category,quantity,unit_price,discount_pct,status,gross_amount,net_amount"
    clean_lines = (
        clean_orders
        .sortBy(lambda row: row["order_id"])
        .map(lambda row: ",".join(csv_escape(row[name]) for name in [
            "order_id","order_date","customer_id","city","category","quantity",
            "unit_price","discount_pct","status","gross_amount","net_amount",
        ]))
        .coalesce(1)
        .mapPartitionsWithIndex(lambda index, rows: add_header(index, rows, clean_header))
    )
    clean_lines.saveAsTextFile(file_uri(clean_output))

    reject_header = "order_id,raw_or_city,rejection_reason"
    reject_lines = (
        rejected_orders
        .map(lambda item: ",".join([
            csv_escape(item["row"].get("order_id", "")),
            csv_escape(item["row"].get("city", item["row"].get("_raw", ""))),
            csv_escape("|".join(item["reasons"])),
        ]))
        .coalesce(1)
        .mapPartitionsWithIndex(lambda index, rows: add_header(index, rows, reject_header))
    )
    reject_lines.saveAsTextFile(file_uri(reject_output))

    report_header = "category,department,manager,completed_orders,units_sold,net_revenue,average_order_value,monthly_target,achievement_pct"
    report_lines = (
        report_rdd
        .map(lambda row: ",".join(csv_escape(row[name]) for name in [
            "category","department","manager","completed_orders","units_sold",
            "net_revenue","average_order_value","monthly_target","achievement_pct",
        ]))
        .coalesce(1)
        .mapPartitionsWithIndex(lambda index, rows: add_header(index, rows, report_header))
    )
    report_lines.saveAsTextFile(file_uri(report_output))

    # SequenceFile specifically preserves a key-value output shape.
    report_pair_for_sequence = report_rdd.map(
        lambda row: (row["category"], json.dumps(row, sort_keys=True))
    )
    report_pair_for_sequence.saveAsSequenceFile(file_uri(sequence_output))

    report_rows = report_rdd.collect()
    rejected_count = rejected_orders.count()
    clean_count = clean_orders.count()

    print("\nPIPELINE CONTROL TOTALS")
    print("Input rows             :", input_count)
    print("Valid rows             :", clean_count)
    print("Rejected rows          :", rejected_count)
    print("Completed report rows  :", sum(row["completed_orders"] for row in report_rows))
    print("Reconciled             :", input_count == clean_count + rejected_count)

    print("\nCATEGORY SALES REPORT")
    for row in report_rows:
        print(row)

    print("\nOUTPUT DIRECTORIES")
    print(clean_output)
    print(reject_output)
    print(report_output)
    print(sequence_output)

    assert input_count == clean_count + rejected_count

    report_rdd.unpersist()
    clean_orders.unpersist()
    classified.unpersist()
    spark.stop()


if __name__ == "__main__":
    main()
