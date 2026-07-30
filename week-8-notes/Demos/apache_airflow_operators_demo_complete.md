# Simple Apache Airflow Operators Demo

This example demonstrates how different Airflow operators work together in one small **bank transaction validation pipeline**.

Airflow tasks are commonly created from operators. An operator is a reusable task template: `BashOperator` executes Bash commands, `PythonOperator` executes Python functions, `BranchPythonOperator` selects one downstream path, and `EmptyOperator` provides logical start, join, or end points.

## Pipeline flow

```text
                   ┌────────────────────────────┐
                   │       start_pipeline       │
                   │       EmptyOperator        │
                   └─────────────┬──────────────┘
                                 │
                                 ▼
                   ┌────────────────────────────┐
                   │     create_input_file      │
                   │       BashOperator         │
                   └─────────────┬──────────────┘
                                 │
                                 ▼
                   ┌────────────────────────────┐
                   │   validate_transactions    │
                   │      PythonOperator        │
                   └─────────────┬──────────────┘
                                 │
                                 ▼
                   ┌────────────────────────────┐
                   │       choose_path          │
                   │  BranchPythonOperator      │
                   └───────────┬───────┬────────┘
                               │       │
               No invalid data │       │ Invalid data found
                               ▼       ▼
              ┌──────────────────┐   ┌──────────────────┐
              │ process_valid    │   │ quarantine_data  │
              │ PythonOperator   │   │ BashOperator     │
              └────────┬─────────┘   └────────┬─────────┘
                       │                      │
                       └──────────┬───────────┘
                                  ▼
                    ┌────────────────────────┐
                    │      join_branches     │
                    │     EmptyOperator      │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │     finish_pipeline    │
                    │      BashOperator      │
                    └────────────────────────┘
```

---

# 1. Operators demonstrated

| Operator | What it does | Use in this example |
|---|---|---|
| `EmptyOperator` | Performs no business processing | Marks the start and joins branches |
| `BashOperator` | Runs a Linux Bash command | Creates the CSV and writes a rejection report |
| `PythonOperator` | Executes a Python function | Validates and processes transactions |
| `BranchPythonOperator` | Selects one downstream path | Chooses processing or quarantine |
| Trigger rule | Controls when a task may run | Allows the branches to rejoin |

A DAG contains tasks and their dependencies; the dependencies determine their execution order.

---

# 2. Open the Airflow DAG folder in VS Code

Open Ubuntu.

Run:

```bash
code /home/geetha/airflow/dags
```

The bottom-left corner of VS Code should show:

```text
WSL: Ubuntu
```

Create a new file:

```text
operator_demo_bank_pipeline.py
```

The full location should be:

```text
/home/geetha/airflow/dags/operator_demo_bank_pipeline.py
```

---

# 3. Complete DAG code

Paste the following code:

```python
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
TXN-1004,John,900.00,FAILED
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
```

Save the file:

```text
Ctrl + S
```

---

# 4. What the sample input contains

The `BashOperator` creates:

```csv
transaction_id,customer_name,amount,status
TXN-1001,Asha,1500.00,SUCCESS
TXN-1002,Rahul,2200.00,SUCCESS
TXN-1003,Meena,-250.00,SUCCESS
TXN-1004,John,900.00,FAILED
```

Validation rules:

```text
amount must be greater than zero
status must be SUCCESS
```

Expected classification:

| Transaction | Amount | Status | Result |
|---|---:|---|---|
| `TXN-1001` | 1500 | SUCCESS | Valid |
| `TXN-1002` | 2200 | SUCCESS | Valid |
| `TXN-1003` | -250 | SUCCESS | Invalid |
| `TXN-1004` | 900 | FAILED | Invalid |

Therefore, the first run selects:

```text
quarantine_invalid_data
```

The task:

```text
process_valid_transactions
```

will appear as **skipped**. Branch operators mark unselected downstream paths as skipped.

---

# 5. Validate the Python file

Open a VS Code Ubuntu terminal.

Activate your Airflow environment:

```bash
cd ~/projects/airflow-lab

source .venv/bin/activate

export AIRFLOW_HOME=$HOME/airflow
```

Check the Python syntax:

```bash
python -m py_compile     ~/airflow/dags/operator_demo_bank_pipeline.py
```

No output means the Python syntax is valid.

---

# 6. Check whether Airflow found the DAG

Run:

```bash
airflow dags list | grep operator_demo
```

Expected:

```text
operator_demo_bank_pipeline
```

Check import errors:

```bash
airflow dags list-import-errors
```

Expected:

```text
No data found
```

List the tasks:

```bash
airflow tasks list     operator_demo_bank_pipeline
```

Expected:

```text
start_pipeline
create_input_file
validate_transactions
choose_path
process_valid_transactions
quarantine_invalid_data
join_branches
finish_pipeline
```

Show the task hierarchy:

```bash
airflow tasks list     operator_demo_bank_pipeline     --tree
```

---

# 7. Start Airflow

In VS Code Terminal 1 or Ubuntu Terminal 1:

```bash
cd ~/projects/airflow-lab

source .venv/bin/activate

export AIRFLOW_HOME=$HOME/airflow

airflow standalone
```

Keep this terminal open.

Open the UI:

```text
http://localhost:8080
```

---

# 8. Execute the DAG in the UI

Open:

```text
Dags
→ Search: operator_demo_bank_pipeline
→ Open the DAG
→ Unpause/enable it
→ Trigger
→ Single Run
```

Open **Graph View**.

Expected graph:

```text
start_pipeline
      │
      ▼
create_input_file
      │
      ▼
validate_transactions
      │
      ▼
choose_path
   ┌──┴─────────────────────┐
   ▼                        ▼
process_valid         quarantine_invalid
transactions               data
   │                        │
   └───────────┬────────────┘
               ▼
        join_branches
               │
               ▼
        finish_pipeline
```

Open **Grid View** to see the task states. Airflow represents workflows as DAGs containing tasks and dependencies, and the UI allows the run and task states to be inspected.

---

# 9. Expected first-run states

Because two invalid transactions exist:

| Task | Expected state |
|---|---|
| `start_pipeline` | Success |
| `create_input_file` | Success |
| `validate_transactions` | Success |
| `choose_path` | Success |
| `process_valid_transactions` | Skipped |
| `quarantine_invalid_data` | Success |
| `join_branches` | Success |
| `finish_pipeline` | Success |

---

# 10. Examine the operator logs

## `create_input_file`

Open:

```text
create_input_file
→ Logs
```

Expected:

```text
Input transaction file created.
File location:
/home/geetha/airflow/operator_demo/bank_transactions.csv
```

## `validate_transactions`

Expected:

```text
VALID: TXN-1001, amount=1500.0
VALID: TXN-1002, amount=2200.0
INVALID: TXN-1003, amount=-250.0, status=SUCCESS
INVALID: TXN-1004, amount=900.0, status=FAILED

Validation result:
{
    'valid_count': 2,
    'invalid_count': 2,
    'total_valid_amount': 3700.0
}
```

## `choose_path`

Expected:

```text
Invalid transaction count: 2
Selected path: quarantine_invalid_data
```

## `quarantine_invalid_data`

Expected:

```text
Invalid transactions were detected.
Review the validation task logs.
```

---

# 11. Verify the generated files

In Terminal 2:

```bash
ls -la ~/airflow/operator_demo
```

View the transaction file:

```bash
cat   ~/airflow/operator_demo/bank_transactions.csv
```

View the rejected-data report:

```bash
cat   ~/airflow/operator_demo/rejected_transactions.txt
```

---

# 12. Run the other branch

To demonstrate the valid-processing path, change these two rows inside the DAG’s `create_input_file` task:

Current values:

```csv
TXN-1003,Meena,-250.00,SUCCESS
TXN-1004,John,900.00,FAILED
```

Change them to:

```csv
TXN-1003,Meena,250.00,SUCCESS
TXN-1004,John,900.00,SUCCESS
```

Save the DAG and trigger it again.

Expected branch:

```text
process_valid_transactions
```

Expected task states:

| Task | Expected state |
|---|---|
| `process_valid_transactions` | Success |
| `quarantine_invalid_data` | Skipped |
| `join_branches` | Success |

View the summary:

```bash
cat   ~/airflow/operator_demo/transaction_summary.txt
```

Expected:

```text
BANK TRANSACTION PROCESSING SUMMARY
===================================
Valid transactions : 4
Invalid transactions: 0
Valid total amount : 4850.0
```

---

# 13. How each operator is helpful

## EmptyOperator

```python
start_pipeline = EmptyOperator(
    task_id="start_pipeline",
)
```

It does not process data. It is helpful for:

```text
Clearly marking the beginning
Joining multiple branches
Visually organizing the DAG
Providing a common dependency point
```

`EmptyOperator` is evaluated by the Scheduler but performs no executor-side business work.

---

## BashOperator

```python
create_input_file = BashOperator(
    task_id="create_input_file",
    bash_command="...",
)
```

It is helpful for:

```text
Running shell scripts
Creating or moving files
Calling Linux commands
Starting existing command-line applications
Executing existing .sh scripts
```

`BashOperator` executes commands in a Bash shell.

Industry examples:

```text
Copy a file to an archive folder
Call a Spark submit command
Run a database backup script
Compress output files
Execute an existing batch script
```

---

## PythonOperator

```python
validate_data = PythonOperator(
    task_id="validate_transactions",
    python_callable=validate_transactions,
)
```

It is helpful for:

```text
Validation rules
Calling APIs
Transforming small datasets
Generating reports
Executing custom Python business logic
```

The callable can receive Airflow context parameters such as `ti`, and its return value can be stored through XCom.

---

## BranchPythonOperator

```python
select_path = BranchPythonOperator(
    task_id="choose_path",
    python_callable=choose_processing_path,
)
```

It is helpful when the pipeline must make a decision:

```text
Quality passed → load data
Quality failed → quarantine data

Records available → process them
No records → send “no data” message

High-risk transaction → manual review
Normal transaction → automatic processing
```

The Python function returns the `task_id` of the downstream path that should run; unselected direct downstream paths are skipped.

---

## Trigger rule

```python
trigger_rule="none_failed_min_one_success"
```

After branching, one task succeeds and another is skipped. The join task must therefore be allowed to execute when:

```text
No upstream task failed
At least one upstream task succeeded
```

Without this trigger rule, the join might be skipped because the default behavior expects all upstream tasks to succeed.

---

# 14. Easy explanation for participants

```text
Operator = type of work

Task = operator used inside a DAG

Task instance = one execution of that task

DAG = complete workflow and its dependencies

Scheduler = decides when tasks can run
```

Example:

```text
BashOperator
    ↓
A reusable operator type

create_input_file
    ↓
A task created from BashOperator

create_input_file for today's DAG run
    ↓
A task instance
```

## Final demonstration sequence

```text
1. Open the Python DAG in VS Code.
2. Explain each imported operator.
3. Start Airflow standalone.
4. Open localhost:8080.
5. Show Graph View before execution.
6. Trigger the DAG.
7. Show Grid View.
8. Open each task log.
9. Explain why one branch was skipped.
10. Correct the invalid data.
11. Trigger the DAG again.
12. Show that the other branch now runs.
```
