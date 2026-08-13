import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def callable_hello_world():
    print("Hello World")


default_args = {
    "start_date": datetime.datetime(2009, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}


dag = DAG(
    dag_id="basic_dag_with_dependency",
    default_args=default_args,
    description="Basic Dag",
    schedule="*/10 * * * *",
    max_active_runs=2,
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=10),
)


bash_operator = BashOperator(
    task_id="task-1",
    bash_command="echo test",
    dag=dag,
)


python_operator = PythonOperator(
    task_id="task-2",
    python_callable=callable_hello_world,
    dag=dag,
)


bash_operator >> python_operator