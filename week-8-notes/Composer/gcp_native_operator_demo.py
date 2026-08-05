import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryInsertJobOperator,
)


PROJECT_ID = "bigquery-optimization-lab"
DATA_BUCKET = "us-east1-test-composer-fb62e521-bucket"
BQ_DATASET = "composer_training"
BQ_LOCATION = "asia-south1"


default_args = {
    "owner": "training",
    "start_date": datetime.datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=2),
}


with DAG(
    dag_id="gcp_native_operator_demo",
    default_args=default_args,
    description="Demonstrates GCS sensor and BigQuery operators",
    schedule=None,
    catchup=False,
    tags=["composer", "gcp", "gcs", "bigquery"],
) as dag:

    start = EmptyOperator(
        task_id="start",
    )

    wait_for_employee_file = GCSObjectExistenceSensor(
        task_id="wait_for_employee_file",
        bucket=DATA_BUCKET,
        object="input/employees.csv",
        google_cloud_conn_id="google_cloud_default",
        poke_interval=30,
        timeout=600,
        mode="reschedule",
    )

    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset",
        project_id=PROJECT_ID,
        dataset_id=BQ_DATASET,
        location=BQ_LOCATION,
        exists_ok=True,
        gcp_conn_id="google_cloud_default",
    )

    create_external_table = BigQueryInsertJobOperator(
        task_id="create_external_table",
        location=BQ_LOCATION,
        gcp_conn_id="google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE EXTERNAL TABLE
                    `{PROJECT_ID}.{BQ_DATASET}.employees_external`
                    (
                        employee_id INT64,
                        employee_name STRING,
                        department STRING,
                        salary NUMERIC
                    )
                    OPTIONS (
                        format = 'CSV',
                        uris = ['gs://{DATA_BUCKET}/input/employees.csv'],
                        skip_leading_rows = 1
                    )
                """,
                "useLegacySql": False,
            }
        },
    )

    create_department_summary = BigQueryInsertJobOperator(
        task_id="create_department_summary",
        location=BQ_LOCATION,
        gcp_conn_id="google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE
                    `{PROJECT_ID}.{BQ_DATASET}.department_salary_summary`
                    AS
                    SELECT
                        department,
                        COUNT(*) AS employee_count,
                        SUM(salary) AS total_salary,
                        ROUND(AVG(salary), 2) AS average_salary,
                        MAX(salary) AS maximum_salary,
                        MIN(salary) AS minimum_salary
                    FROM
                        `{PROJECT_ID}.{BQ_DATASET}.employees_external`
                    GROUP BY
                        department
                """,
                "useLegacySql": False,
            }
        },
    )

    validate_summary = BigQueryInsertJobOperator(
        task_id="validate_summary",
        location=BQ_LOCATION,
        gcp_conn_id="google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                    SELECT
                        department,
                        employee_count,
                        total_salary,
                        average_salary
                    FROM
                        `{PROJECT_ID}.{BQ_DATASET}.department_salary_summary`
                    ORDER BY
                        department
                """,
                "useLegacySql": False,
            }
        },
    )

    end = EmptyOperator(
        task_id="end",
    )

    (
        start
        >> wait_for_employee_file
        >> create_dataset
        >> create_external_table
        >> create_department_summary
        >> validate_summary
        >> end
    )