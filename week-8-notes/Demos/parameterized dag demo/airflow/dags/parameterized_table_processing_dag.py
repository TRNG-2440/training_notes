from datetime import datetime

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator


def show_parameters(**context):
    """Display all parameters received by the DAG."""

    params = context["params"]

    table_name = params["table_name"]
    year = params["year"]
    month = params["month"]
    environment = params["environment"]

    print("=" * 50)
    print("Received DAG Parameters")
    print("=" * 50)
    print(f"Table       : {table_name}")
    print(f"Year        : {year}")
    print(f"Month       : {month}")
    print(f"Environment : {environment}")
    print("=" * 50)


def extract_table(**context):
    """Simulate extracting data from a source table."""

    params = context["params"]

    table_name = params["table_name"]
    year = params["year"]
    month = params["month"]

    print(
        f"Extracting data from {table_name} "
        f"for {month} {year}"
    )

    # Replace this print statement with actual extraction logic.
    # Example:
    #
    # SELECT *
    # FROM Employee
    # WHERE YEAR(created_date) = 2026
    # AND MONTH(created_date) = 8;

    print(f"Extraction completed for {table_name}")


def validate_table(**context):
    """Simulate validating the extracted data."""

    table_name = context["params"]["table_name"]

    print(f"Validating data from {table_name}")

    # Real-world validations:
    # - Check record count
    # - Check null values
    # - Check duplicate records
    # - Check invalid dates
    # - Check mandatory columns

    print("Null-value validation completed")
    print("Duplicate validation completed")
    print("Record-count validation completed")
    print(f"Validation completed for {table_name}")


def load_table(**context):
    """Simulate loading data into a target environment."""

    params = context["params"]

    table_name = params["table_name"]
    environment = params["environment"]

    print(
        f"Loading {table_name} data into "
        f"the {environment} environment"
    )

    # Replace this with actual target-loading logic.
    # Examples:
    # - Write to Snowflake
    # - Write to Azure SQL
    # - Write to BigQuery
    # - Write to ADLS
    # - Write to Amazon S3

    print(f"Load completed for {table_name}")


with DAG(
    dag_id="parameterized_table_processing",
    description="Process different database tables using parameters",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,

    params={
        "table_name": Param(
            default="Employee",
            type="string",
            enum=[
                "Employee",
                "Department",
                "Customer",
                "Product"
            ],
            description="Select the source table"
        ),

        "year": Param(
            default=2026,
            type="integer",
            minimum=2020,
            maximum=2030,
            description="Enter the processing year"
        ),

        "month": Param(
            default="August",
            type="string",
            enum=[
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ],
            description="Select the processing month"
        ),

        "environment": Param(
            default="Development",
            type="string",
            enum=[
                "Development",
                "Testing",
                "Production"
            ],
            description="Select the target environment"
        )
    },

    tags=[
        "parameterized",
        "etl",
        "training"
    ]
) as dag:

    show_parameters_task = PythonOperator(
        task_id="show_parameters",
        python_callable=show_parameters
    )

    extract_task = PythonOperator(
        task_id="extract_table",
        python_callable=extract_table
    )

    validate_task = PythonOperator(
        task_id="validate_table",
        python_callable=validate_table
    )

    load_task = PythonOperator(
        task_id="load_table",
        python_callable=load_table
    )

    show_parameters_task >> extract_task >> validate_task >> load_task