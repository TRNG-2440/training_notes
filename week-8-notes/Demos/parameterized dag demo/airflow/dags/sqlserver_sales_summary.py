from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook

CONN_ID = "sqlserver_lab"


def check_connection():
    hook = MsSqlHook(mssql_conn_id=CONN_ID)
    row = hook.get_first("SELECT DB_NAME(), SYSTEM_USER, GETDATE()")
    print(f"database={row[0]}, user={row[1]}, server_time={row[2]}")


def refresh_city_summary():
    hook = MsSqlHook(mssql_conn_id=CONN_ID)
    sql = """
    MERGE dbo.city_sales_summary AS target
    USING (
        SELECT city, SUM(amount) AS total_amount
        FROM dbo.sales_orders
        GROUP BY city
    ) AS source
    ON target.city = source.city
    WHEN MATCHED THEN
        UPDATE SET total_amount = source.total_amount,
                   refreshed_at = SYSDATETIME()
    WHEN NOT MATCHED THEN
        INSERT (city, total_amount, refreshed_at)
        VALUES (source.city, source.total_amount, SYSDATETIME());
    """
    hook.run(sql)


def print_summary():
    hook = MsSqlHook(mssql_conn_id=CONN_ID)
    rows = hook.get_records(
        "SELECT city, total_amount, refreshed_at "
        "FROM dbo.city_sales_summary ORDER BY total_amount DESC"
    )
    for row in rows:
        print(row)

with DAG(
    dag_id="sqlserver_sales_summary",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["sqlserver", "hooks"],
) as dag:
    t1 = PythonOperator(task_id="check_connection", python_callable=check_connection)
    t2 = PythonOperator(task_id="refresh_city_summary", python_callable=refresh_city_summary)
    t3 = PythonOperator(task_id="print_summary", python_callable=print_summary)
    t1 >> t2 >> t3