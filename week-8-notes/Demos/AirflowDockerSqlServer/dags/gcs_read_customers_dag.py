from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any

from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.sdk import dag, task


BUCKET_NAME = "azctsdemo1bucket"
OBJECT_NAME = "input/customers.csv"
GCP_CONNECTION_ID = "google_cloud_default"


@dag(
    dag_id="gcs_read_customers",
    description="Read customers.csv from Google Cloud Storage",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=["gcp", "gcs", "csv"],
)
def gcs_read_customers_dag():

    @task
    def check_and_list_objects() -> list[str]:
        """
        Connect to GCS and list files under the input folder.
        """

        hook = GCSHook(
            gcp_conn_id=GCP_CONNECTION_ID
        )

        objects = hook.list(
            bucket_name=BUCKET_NAME,
            prefix="input/",
        )

        # GCS may return a folder placeholder such as "input/".
        files = [
            object_name
            for object_name in objects
            if not object_name.endswith("/")
        ]

        if not files:
            raise FileNotFoundError(
                f"No files were found under "
                f"gs://{BUCKET_NAME}/input/"
            )

        logging.info("=" * 70)
        logging.info("FILES FOUND IN GOOGLE CLOUD STORAGE")
        logging.info("=" * 70)

        for object_name in files:
            logging.info(
                "gs://%s/%s",
                BUCKET_NAME,
                object_name,
            )

        logging.info("Total files found: %s", len(files))

        return files

    @task
    def read_customers_csv(
        objects: list[str],
    ) -> dict[str, Any]:
        """
        Download customers.csv into memory and read its records.
        """

        if OBJECT_NAME not in objects:
            raise FileNotFoundError(
                f"Expected object "
                f"gs://{BUCKET_NAME}/{OBJECT_NAME} "
                f"was not found."
            )

        hook = GCSHook(
            gcp_conn_id=GCP_CONNECTION_ID
        )

        file_bytes = hook.download(
            bucket_name=BUCKET_NAME,
            object_name=OBJECT_NAME,
        )

        csv_text = file_bytes.decode("utf-8-sig")

        reader = csv.DictReader(
            io.StringIO(csv_text)
        )

        records = list(reader)

        if not records:
            raise ValueError(
                "The CSV file exists, but it contains no data records."
            )

        columns = reader.fieldnames or []

        logging.info("=" * 70)
        logging.info("CUSTOMERS CSV DETAILS")
        logging.info("=" * 70)
        logging.info(
            "Source: gs://%s/%s",
            BUCKET_NAME,
            OBJECT_NAME,
        )
        logging.info("Columns: %s", columns)
        logging.info(
            "Total customer records: %s",
            len(records),
        )

        # Print only the first 10 rows.
        for row_number, record in enumerate(
            records[:10],
            start=1,
        ):
            logging.info(
                "Record %s: %s",
                row_number,
                record,
            )

        return {
            "bucket": BUCKET_NAME,
            "object": OBJECT_NAME,
            "record_count": len(records),
            "columns": columns,
            "preview": records[:5],
        }

    @task
    def print_summary(
        summary: dict[str, Any],
    ) -> None:
        """
        Print a final summary.
        """

        logging.info("=" * 70)
        logging.info("GCS READ COMPLETED SUCCESSFULLY")
        logging.info("=" * 70)
        logging.info(
            "Source: gs://%s/%s",
            summary["bucket"],
            summary["object"],
        )
        logging.info(
            "Record count: %s",
            summary["record_count"],
        )
        logging.info(
            "Columns: %s",
            summary["columns"],
        )
        logging.info(
            "First five records: %s",
            summary["preview"],
        )

    object_list = check_and_list_objects()

    result = read_customers_csv(
        object_list
    )

    print_summary(
        result
    )


gcs_read_customers_dag()