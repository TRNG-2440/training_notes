from datetime import datetime

from airflow.sdk import dag, task


# Configuration used to generate multiple DAGs
RETAIL_STORES = {
    "chennai": {
        "store_name": "Chennai Retail Store",
        "target_table": "chennai_daily_sales",
    },
    "bangalore": {
        "store_name": "Bangalore Retail Store",
        "target_table": "bangalore_daily_sales",
    },
    "hyderabad": {
        "store_name": "Hyderabad Retail Store",
        "target_table": "hyderabad_daily_sales",
    },
}


# Loop through every store configuration
for store_code, store_config in RETAIL_STORES.items():

    dynamic_dag_id = f"retail_sales_{store_code}_dag"

    @dag(
        dag_id=dynamic_dag_id,
        description=f"Retail sales ETL for {store_config['store_name']}",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["retail", "dynamic-dag", store_code],
    )
    def create_retail_sales_dag():

        @task
        def extract_sales(store_name):
            print(f"Extracting sales data for {store_name}")

        @task
        def transform_sales(store_name):
            print(f"Transforming sales data for {store_name}")

        @task
        def load_sales(store_name, target_table):
            print(f"Loading sales data for {store_name}")
            print(f"Target table: {target_table}")

        extract_task = extract_sales(
            store_name=store_config["store_name"]
        )

        transform_task = transform_sales(
            store_name=store_config["store_name"]
        )

        load_task = load_sales(
            store_name=store_config["store_name"],
            target_table=store_config["target_table"],
        )

        extract_task >> transform_task >> load_task

    # Create and register one DAG for the current store
    create_retail_sales_dag()