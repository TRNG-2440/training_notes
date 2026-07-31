from datetime import datetime

from airflow.sdk import DAG, task


with DAG(
    dag_id="simple_retail_sales_dag",
    description="Simple retail sales ETL workflow",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["retail", "sales", "beginner"],
) as dag:

    @task
    def extract_sales():
        print("Extracting sales data")

    @task
    def transform_sales():
        print("Transforming sales data")

    @task
    def load_sales():
        print("Loading sales data")

    extract_task = extract_sales()
    transform_task = transform_sales()
    load_task = load_sales()


    #extract_task >>transform_task >> load_task
    #load_task << transform_task <<  extract_task
    extract_task.set_downstream(transform_task)
    transform_task.set_downstream(load_task)
   