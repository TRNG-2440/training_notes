import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def hello_world1():
    print("Dag Started with task 1")


def hello_world2():
    print("Dag Started with task 2")


def hello_world3():
    print("Dag Started with task 3")


default_args = {
    "start_date": datetime.datetime(2000, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}


dag = DAG(
    dag_id="sample_dag",
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


python_operator1 = PythonOperator(
    task_id="task-2-1",
    python_callable=hello_world1,
    dag=dag,
)


python_operator2 = PythonOperator(
    task_id="task-2-2",
    python_callable=hello_world2,
    dag=dag,
)


python_operator3 = PythonOperator(
    task_id="task-3",
    python_callable=hello_world3,
    dag=dag,
)


bash_operator >> [python_operator1, python_operator2] >> python_operator3