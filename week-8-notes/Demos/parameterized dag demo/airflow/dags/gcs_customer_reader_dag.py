from __future__ import annotations

import csv
import io
import logging
from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook


GCP_CONNECTION_ID = "google_cloud_default"
BUCKET_NAME = "azctsdemo1bucket"
SOURCE_OBJECT = "input/customers.csv"


@dag(
    dag_id="gcs_customer_reader_dag",
    description="Read customers.csv from Google Cloud Storage using GCSHook",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["gcs", "customers", "hooks"],
)
def gcs_customer_reader_workflow():

    @task
    def check_source_file() -> str:
        """
        Confirm that the source object exists in Google Cloud Storage.
        """
        hook = GCSHook(gcp_conn_id=GCP_CONNECTION_ID)

        file_exists = hook.exists(
            bucket_name=BUCKET_NAME,
            object_name=SOURCE_OBJECT,
        )

        if not file_exists:
            raise FileNotFoundError(
                f"Source file not found: "
                f"gs://{BUCKET_NAME}/{SOURCE_OBJECT}"
            )

        gcs_uri = f"gs://{BUCKET_NAME}/{SOURCE_OBJECT}"
        logging.info("Source file found: %s", gcs_uri)

        return gcs_uri

    @task
    def read_customer_file(_: str) -> dict:
        """
        Download the CSV through GCSHook, parse it in memory,
        and display sample rows in the Airflow task log.
        """
        hook = GCSHook(gcp_conn_id=GCP_CONNECTION_ID)

        file_bytes = hook.download(
            bucket_name=BUCKET_NAME,
            object_name=SOURCE_OBJECT,
        )

        csv_text = file_bytes.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)

        if not rows:
            raise ValueError("The customer CSV file contains no data rows.")

        logging.info("CSV columns: %s", reader.fieldnames)
        logging.info("Total customer records: %d", len(rows))

        logging.info("First five customer records:")

        for row_number, row in enumerate(rows[:5], start=1):
            logging.info("Row %d: %s", row_number, row)

        return {
            "bucket": BUCKET_NAME,
            "object": SOURCE_OBJECT,
            "record_count": len(rows),
            "columns": reader.fieldnames or [],
            "sample_rows": rows[:3],
        }

    @task
    def display_summary(file_summary: dict) -> None:
        """
        Display a compact summary in the Airflow task logs.
        """
        logging.info("GCS customer file processing completed.")
        logging.info("Bucket: %s", file_summary["bucket"])
        logging.info("Object: %s", file_summary["object"])
        logging.info("Columns: %s", file_summary["columns"])
        logging.info(
            "Number of records: %s",
            file_summary["record_count"],
        )
        logging.info(
            "Sample records: %s",
            file_summary["sample_rows"],
        )

    source_uri = check_source_file()
    summary = read_customer_file(source_uri)
    display_summary(summary)


gcs_customer_reader_workflow()