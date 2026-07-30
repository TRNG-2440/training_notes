from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="hello_airflow_training_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["training", "demo"],
)
def hello_airflow_training_dag():

    @task
    def extract():
        print("Step 1: Extracting data")
        return ["order1", "order2", "order3"]

    @task
    def transform(orders):
        print("Step 2: Transforming data")
        transformed_orders = [order.upper() for order in orders]
        return transformed_orders

    @task
    def load(transformed_orders):
        print("Step 3: Loading data")
        print("Final Output:", transformed_orders)

    orders = extract()
    transformed = transform(orders)
    load(transformed)


hello_airflow_training_dag()
