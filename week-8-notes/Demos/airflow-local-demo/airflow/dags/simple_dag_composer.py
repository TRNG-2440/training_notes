from datetime import datetime

from airflow import DAG
from airflow.decorators import task


with DAG(
    dag_id="simple_retail_sales_dag",
    description="Simple retail sales ETL workflow",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["retail", "sales", "training"],
) as dag:

    @task
    def extract_sales():
        """Simulate extracting retail sales data."""
        print("Extracting sales data")

    @task
    def transform_sales():
        """Simulate transforming retail sales data."""
        print("Transforming sales data")

    @task
    def load_sales():
        """Simulate loading retail sales data."""
        print("Loading sales data")

    extract_task = extract_sales()
    transform_task = transform_sales()
    load_task = load_sales()

    extract_task >> transform_task >> load_task