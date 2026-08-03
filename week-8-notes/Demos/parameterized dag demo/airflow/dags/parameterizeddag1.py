from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def print_table(**context):

    # table = context["params"]["table_name"]
    # print(f"Processing {table}")
    table = context["params"]["table"]

    year = context["params"]["year"]

    month = context["params"]["month"]
    print(f"Processing {table} for {year}-{month}")


with DAG(

    dag_id="parameterized_demo",

    start_date=datetime(2026,1,1),

    schedule=None,

    catchup=False,

    # params={
    #     "table_name":"Employee"
    # }

    params={

        "table":"Employee",

        "year":2026,

        "month":"July"

    }
) as dag:

    task1 = PythonOperator(

        task_id="print_table",

        python_callable=print_table

    )