"""Demonstrate commonly used Apache Airflow operators."""

from __future__ import annotations

import csv
from pathlib import Path

import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import (
    BranchPythonOperator,
    PythonOperator,
)


# ------------------------------------------------------------
# File locations
# ------------------------------------------------------------

DEMO_DIRECTORY = Path("/home/geetha/airflow/operator_demo")

TRANSACTION_FILE = (
    DEMO_DIRECTORY / "bank_transactions.csv"
)

SUMMARY_FILE = (
    DEMO_DIRECTORY / "transaction_summary.txt"
)

REJECTED_FILE = (
    DEMO_DIRECTORY / "rejected_transactions.txt"
)


# ------------------------------------------------------------
# Python function used by PythonOperator
# ------------------------------------------------------------

def validate_transactions() -> dict:
    """Validate transaction amount and status."""

    valid_count = 0
    invalid_count = 0
    total_valid_amount = 0.0

    print(f"Reading file: {TRANSACTION_FILE}")

    with TRANSACTION_FILE.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for transaction in reader:
            transaction_id = transaction["transaction_id"]
            amount = float(transaction["amount"])
            status = transaction["status"]

            is_valid = (
                amount > 0
                and status == "SUCCESS"
            )

            if is_valid:
                valid_count += 1
                total_valid_amount += amount

                print(
                    f"VALID: {transaction_id}, "
                    f"amount={amount}"
                )
            else:
                invalid_count += 1

                print(
                    f"INVALID: {transaction_id}, "
                    f"amount={amount}, "
                    f"status={status}"
                )

    validation_result = {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total_valid_amount": round(
            total_valid_amount,
            2,
        ),
    }

    print(f"Validation result: {validation_result}")

    # PythonOperator automatically stores this return value
    # as an XCom value.
    return validation_result


# ------------------------------------------------------------
# Python function used by BranchPythonOperator
# ------------------------------------------------------------

def choose_processing_path(ti) -> str:
    """Choose the processing path based on validation output."""

    validation_result = ti.xcom_pull(
        task_ids="validate_transactions"
    )

    invalid_count = validation_result[
        "invalid_count"
    ]

    print(f"Invalid transaction count: {invalid_count}")

    if invalid_count > 0:
        print("Selected path: quarantine_invalid_data")

        return "quarantine_invalid_data"

    print("Selected path: process_valid_transactions")

    return "process_valid_transactions"


# ------------------------------------------------------------
# Python function used by another PythonOperator
# ------------------------------------------------------------

def process_valid_transactions(ti) -> None:
    """Create a summary for valid transactions."""

    validation_result = ti.xcom_pull(
        task_ids="validate_transactions"
    )

    report = (
        "BANK TRANSACTION PROCESSING SUMMARY\n"
        "===================================\n"
        f"Valid transactions : "
        f"{validation_result['valid_count']}\n"
        f"Invalid transactions: "
        f"{validation_result['invalid_count']}\n"
        f"Valid total amount : "
        f"{validation_result['total_valid_amount']}\n"
    )

    SUMMARY_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(report)
    print(f"Summary created: {SUMMARY_FILE}")


# ------------------------------------------------------------
# DAG definition
# ------------------------------------------------------------

with DAG(
    dag_id="operator_demo_bank_pipeline",
    description=(
        "Simple demonstration of different "
        "Apache Airflow operators"
    ),
    schedule=None,
    start_date=pendulum.datetime(
        2026,
        7,
        1,
        tz="Asia/Kolkata",
    ),
    catchup=False,
    tags=[
        "operators",
        "banking",
        "beginner",
    ],
) as dag:

    # --------------------------------------------------------
    # 1. EmptyOperator
    # --------------------------------------------------------

    start_pipeline = EmptyOperator(
        task_id="start_pipeline",
    )

    # --------------------------------------------------------
    # 2. BashOperator
    # --------------------------------------------------------

    create_input_file = BashOperator(
        task_id="create_input_file",
        bash_command=f"""
        set -e

        mkdir -p "{DEMO_DIRECTORY}"

        cat > "{TRANSACTION_FILE}" << 'EOF'
transaction_id,customer_name,amount,status
TXN-1001,Asha,1500.00,SUCCESS
TXN-1002,Rahul,2200.00,SUCCESS
TXN-1003,Meena,-250.00,SUCCESS
EOF

        echo "Input transaction file created."
        echo "File location: {TRANSACTION_FILE}"
        echo
        cat "{TRANSACTION_FILE}"
        """,
    )

    # --------------------------------------------------------
    # 3. PythonOperator
    # --------------------------------------------------------

    validate_data = PythonOperator(
        task_id="validate_transactions",
        python_callable=validate_transactions,
    )

    # --------------------------------------------------------
    # 4. BranchPythonOperator
    # --------------------------------------------------------

    select_path = BranchPythonOperator(
        task_id="choose_path",
        python_callable=choose_processing_path,
    )

    # --------------------------------------------------------
    # 5. PythonOperator for valid records
    # --------------------------------------------------------

    process_valid = PythonOperator(
        task_id="process_valid_transactions",
        python_callable=process_valid_transactions,
    )

    # --------------------------------------------------------
    # 6. BashOperator for invalid records
    # --------------------------------------------------------

    quarantine_invalid = BashOperator(
        task_id="quarantine_invalid_data",
        bash_command=f"""
        set -e

        echo "Invalid transactions were detected." \
            > "{REJECTED_FILE}"

        echo "Review the validation task logs." \
            >> "{REJECTED_FILE}"

        echo "Rejected-data report created:"
        cat "{REJECTED_FILE}"
        """,
    )

    # --------------------------------------------------------
    # 7. EmptyOperator used to join branches
    # --------------------------------------------------------

    join_branches = EmptyOperator(
        task_id="join_branches",

        # One branch succeeds and the other branch is skipped.
        # Therefore, the join must accept at least one success.
        trigger_rule="none_failed_min_one_success",
    )

    # --------------------------------------------------------
    # 8. Final BashOperator
    # --------------------------------------------------------

    finish_pipeline = BashOperator(
        task_id="finish_pipeline",
        bash_command="""
        echo "================================"
        echo "Bank transaction DAG completed."
        echo "================================"
        """,
    )

    # --------------------------------------------------------
    # Task dependencies
    # --------------------------------------------------------

    (
        start_pipeline
        >> create_input_file
        >> validate_data
        >> select_path
    )

    select_path >> [
        process_valid,
        quarantine_invalid,
    ]

    [
        process_valid,
        quarantine_invalid,
    ] >> join_branches

    join_branches >> finish_pipeline