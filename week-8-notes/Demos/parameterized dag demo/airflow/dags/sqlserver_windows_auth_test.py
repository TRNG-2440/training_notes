from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.odbc.hooks.odbc import OdbcHook


def test_sqlserver_connection():
    hook = OdbcHook(
        odbc_conn_id="sqlserver_windows_auth",
        driver="ODBC Driver 18 for SQL Server",
    )

    with hook.get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                SYSTEM_USER AS system_user,
                ORIGINAL_LOGIN() AS original_login,
                DB_NAME() AS database_name,
                @@SERVERNAME AS server_name
            """
        )

        row = cursor.fetchone()

        print("SQL Server connection succeeded")
        print(f"SYSTEM_USER    : {row[0]}")
        print(f"ORIGINAL_LOGIN : {row[1]}")
        print(f"DATABASE       : {row[2]}")
        print(f"SERVER         : {row[3]}")


with DAG(
    dag_id="sqlserver_windows_auth_test",
    description="Test SQL Server connection using ODBC",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["sql-server", "odbc"],
) as dag:

    test_connection = PythonOperator(
        task_id="test_windows_auth",
        python_callable=test_sqlserver_connection,
    )