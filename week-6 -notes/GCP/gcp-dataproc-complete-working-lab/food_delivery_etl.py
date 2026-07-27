import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)


def main() -> None:
    """Run a small food-delivery ETL job on Dataproc."""

    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: food_delivery_etl.py <input_csv_gs_uri> <output_base_gs_uri>"
        )

    input_path = sys.argv[1]
    output_base = sys.argv[2].rstrip("/")

    spark = (
        SparkSession.builder
        .appName("GCP-Dataproc-Beginner-ETL")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    schema = StructType(
        [
            StructField("order_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("restaurant_name", StringType(), True),
            StructField("city", StringType(), True),
            StructField("order_status", StringType(), True),
            StructField("order_amount", DoubleType(), True),
            StructField("order_date", StringType(), True),
        ]
    )

    print(f"Reading input from: {input_path}")

    raw_df = (
        spark.read
        .option("header", True)
        .schema(schema)
        .csv(input_path)
    )

    raw_count = raw_df.count()

    clean_df = (
        raw_df
        .withColumn("order_id", F.trim(F.col("order_id")))
        .withColumn("customer_id", F.trim(F.col("customer_id")))
        .withColumn("restaurant_name", F.trim(F.col("restaurant_name")))
        .withColumn("city", F.initcap(F.trim(F.col("city"))))
        .withColumn("order_status", F.upper(F.trim(F.col("order_status"))))
        .withColumn("order_date", F.to_date("order_date", "yyyy-MM-dd"))
        .filter(F.col("order_id").isNotNull())
        .filter(F.length(F.col("order_id")) > 0)
        .filter(F.col("city").isNotNull())
        .filter(F.length(F.col("city")) > 0)
        .filter(F.col("order_amount") > 0)
        .filter(F.col("order_status") == "COMPLETED")
        .dropDuplicates(["order_id"])
    )

    clean_count = clean_df.count()

    city_revenue_df = (
        clean_df
        .groupBy("city")
        .agg(
            F.count("*").alias("completed_orders"),
            F.round(F.sum("order_amount"), 2).alias("total_revenue"),
            F.round(F.avg("order_amount"), 2).alias("average_order_value"),
        )
        .orderBy(F.desc("total_revenue"))
    )

    clean_output = f"{output_base}/clean_orders_parquet"
    revenue_output = f"{output_base}/city_revenue_csv"

    (
        clean_df.write
        .mode("overwrite")
        .parquet(clean_output)
    )

    (
        city_revenue_df
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(revenue_output)
    )

    print(f"Raw rows:   {raw_count}")
    print(f"Clean rows: {clean_count}")
    print("City revenue result:")
    city_revenue_df.show(truncate=False)
    print(f"Clean Parquet output: {clean_output}")
    print(f"Revenue CSV output:   {revenue_output}")
    print("ETL job completed successfully.")

    spark.stop()


if __name__ == "__main__":
    main()
