"""Read CSV and JSON, transform with Spark SQL, and save report files."""

from __future__ import annotations

import shutil

from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from common import DATA_DIR, OUTPUT_DIR, create_spark_session


def main() -> None:
    spark = create_spark_session()

    try:
        print("=" * 80)
        print("LOCAL SPARK SQL: MULTI-FORMAT SUPPORT TICKET REPORT")
        print("=" * 80)
        print("Spark version:", spark.version)
        print("Spark UI:", spark.sparkContext.uiWebUrl)

        # ------------------------------------------------------------------
        # STEP 1: Define a schema for the CSV file.
        # ------------------------------------------------------------------
        ticket_schema = StructType(
            [
                StructField("ticket_id", StringType(), False),
                StructField("created_date", StringType(), False),
                StructField("agent_id", StringType(), False),
                StructField("category", StringType(), False),
                StructField("priority", StringType(), False),
                StructField("status", StringType(), False),
                StructField("resolution_hours", DoubleType(), True),
                StructField("customer_rating", IntegerType(), True),
            ]
        )

        # ------------------------------------------------------------------
        # STEP 2: Read the CSV file.
        # ------------------------------------------------------------------
        tickets_df = (
            spark.read
            .option("header", True)
            .schema(ticket_schema)
            .csv(str(DATA_DIR / "support_tickets.csv"))
        )

        # ------------------------------------------------------------------
        # STEP 3: Read the JSON file.
        # Each line in agents.json is one JSON record.
        # ------------------------------------------------------------------
        agents_df = spark.read.json(str(DATA_DIR / "agents.json"))

        print("\nTickets schema:")
        tickets_df.printSchema()

        print("\nAgents schema:")
        agents_df.printSchema()

        print("\nTicket input:")
        tickets_df.show(truncate=False)

        print("\nAgent input:")
        agents_df.show(truncate=False)

        # ------------------------------------------------------------------
        # STEP 4: Clean and enrich ticket data.
        # - Convert date text into DateType.
        # - Normalize text to uppercase.
        # - Add a priority score.
        # - Add an SLA target.
        # ------------------------------------------------------------------
        prepared_tickets_df = (
            tickets_df
            .withColumn("created_date", F.to_date("created_date", "yyyy-MM-dd"))
            .withColumn("status", F.upper(F.trim("status")))
            .withColumn("priority", F.upper(F.trim("priority")))
            .withColumn(
                "priority_score",
                F.when(F.col("priority") == "CRITICAL", 4)
                .when(F.col("priority") == "HIGH", 3)
                .when(F.col("priority") == "MEDIUM", 2)
                .otherwise(1),
            )
            .withColumn(
                "sla_target_hours",
                F.when(F.col("priority") == "CRITICAL", 4.0)
                .when(F.col("priority") == "HIGH", 6.0)
                .when(F.col("priority") == "MEDIUM", 12.0)
                .otherwise(24.0),
            )
        )

        # ------------------------------------------------------------------
        # STEP 5: Filter tickets completed with a measurable resolution time.
        # ------------------------------------------------------------------
        resolved_tickets_df = prepared_tickets_df.filter(
            (F.col("status").isin("RESOLVED", "CLOSED"))
            & F.col("resolution_hours").isNotNull()
        )

        # ------------------------------------------------------------------
        # STEP 6: Join CSV ticket data with JSON agent data.
        # ------------------------------------------------------------------
        detailed_df = (
            resolved_tickets_df
            .join(agents_df, on="agent_id", how="left")
            .withColumn(
                "sla_status",
                F.when(
                    F.col("resolution_hours") <= F.col("sla_target_hours"),
                    F.lit("WITHIN SLA"),
                ).otherwise(F.lit("SLA BREACHED")),
            )
        )

        print("\nResolved ticket details after the join:")
        detailed_df.show(truncate=False)

        # ------------------------------------------------------------------
        # STEP 7: Register a temporary view and use Spark SQL.
        # ------------------------------------------------------------------
        detailed_df.createOrReplaceTempView("resolved_ticket_details")

        report_df = spark.sql(
            """
            SELECT
                team,
                location,
                COUNT(*) AS resolved_ticket_count,
                ROUND(AVG(resolution_hours), 2) AS average_resolution_hours,
                ROUND(AVG(customer_rating), 2) AS average_customer_rating,
                SUM(CASE WHEN sla_status = 'WITHIN SLA' THEN 1 ELSE 0 END)
                    AS within_sla_count,
                SUM(CASE WHEN sla_status = 'SLA BREACHED' THEN 1 ELSE 0 END)
                    AS sla_breach_count,
                ROUND(
                    100.0 * SUM(CASE WHEN sla_status = 'WITHIN SLA' THEN 1 ELSE 0 END)
                    / COUNT(*),
                    2
                ) AS sla_compliance_pct
            FROM resolved_ticket_details
            GROUP BY team, location
            ORDER BY sla_compliance_pct DESC, resolved_ticket_count DESC
            """
        )

        print("\nReport-ready result:")
        report_df.show(truncate=False)

        print("\nPhysical execution plan:")
        report_df.explain(mode="formatted")

        # ------------------------------------------------------------------
        # STEP 8: Prepare output folders.
        # ------------------------------------------------------------------
        parquet_output = OUTPUT_DIR / "support_team_report_parquet"
        csv_output = OUTPUT_DIR / "support_team_report_csv"

        for path in (parquet_output, csv_output):
            if path.exists():
                shutil.rmtree(path)

        # ------------------------------------------------------------------
        # STEP 9: Save in Parquet for analytics/reporting tools.
        # Parquet preserves schema and is columnar.
        # ------------------------------------------------------------------
        (
            report_df.write
            .mode("overwrite")
            .parquet(str(parquet_output))
        )

        # ------------------------------------------------------------------
        # STEP 10: Also save a single CSV folder for easy inspection.
        # coalesce(1) is acceptable only for this small demonstration.
        # ------------------------------------------------------------------
        (
            report_df
            .coalesce(1)
            .write
            .mode("overwrite")
            .option("header", True)
            .csv(str(csv_output))
        )

        # ------------------------------------------------------------------
        # STEP 11: Read the Parquet output back and validate it.
        # ------------------------------------------------------------------
        validated_df = spark.read.parquet(str(parquet_output))

        print("\nValidated Parquet report:")
        validated_df.show(truncate=False)

        print("\nOutput locations:")
        print("Parquet:", parquet_output)
        print("CSV:", csv_output)

        input(
            "\nOpen http://localhost:4040 to inspect Jobs, SQL/DataFrame, "
            "Stages and Executors. Press Enter to stop Spark..."
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
