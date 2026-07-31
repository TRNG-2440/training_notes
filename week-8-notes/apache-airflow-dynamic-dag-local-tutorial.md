# Apache Airflow DAG Tutorial on Ubuntu

This tutorial explains:

* What a DAG is
* How to create tasks
* How to define dependencies
* Meaning of `dag_id`, `schedule`, `start_date`, `catchup`, tags and other arguments
* How to install and run Airflow locally on Ubuntu
* How to create a simple static DAG
* How to create a parameterized DAG
* How to generate dynamic DAGs
* Difference between dynamic DAG generation and dynamic task mapping

Apache Airflow represents a workflow as a **Directed Acyclic Graph**, containing tasks connected through dependencies. Airflow is designed to programmatically author, schedule and monitor workflows. ([Apache Airflow][1])

---

# 1. What is a DAG?

**DAG** means:

```text
Directed Acyclic Graph
```

## Directed

The workflow moves in a defined direction.

```text
Extract → Transform → Load
```

## Acyclic

The workflow must not create an endless circular dependency.

This is valid:

```text
Task A → Task B → Task C
```

This is invalid:

```text
Task A → Task B → Task C
   ↑                 ↓
   └─────────────────┘
```

## Graph

A graph contains:

* Nodes
* Connections between nodes

In Airflow:

| Graph concept  | Airflow concept |
| -------------- | --------------- |
| Node           | Task            |
| Connection     | Dependency      |
| Complete graph | DAG             |
| One execution  | DAG Run         |
| Task execution | Task Instance   |

---

# 2. Real-world example

Consider a retail company that receives a sales CSV every day.

The workflow is:

```text
Check input file
      ↓
Extract sales data
      ↓
Validate records
      ↓
Transform sales
      ↓
Generate summary
      ↓
Load output
      ↓
Send completion message
```

Each box is a task.

The arrows represent dependencies.

---

# 3. Why use Airflow?

Without Airflow, you might manually run:

```bash
python extract.py
python validate.py
python transform.py
python load.py
```

Problems:

* The scripts must be run in the correct order.
* Failures must be checked manually.
* Scheduling must be handled separately.
* Retry logic must be written manually.
* Monitoring is difficult.
* Logs are spread across different programs.

With Airflow, you define the workflow once:

```text
extract → validate → transform → load
```

Airflow handles:

* Scheduling
* Task ordering
* Dependencies
* Retries
* Failure tracking
* Logging
* Monitoring
* Manual reruns
* Backfills
* Runtime parameters

---

# 4. Airflow architecture for a local demo

A simple local installation contains:

```text
DAG Python files
       ↓
DAG Processor
       ↓
Airflow metadata database
       ↓
Scheduler
       ↓
Task execution
       ↓
Airflow Web UI
```

## Main components

### DAG file

A Python file defining the workflow.

### Scheduler

Checks which DAGs and tasks are ready to run.

### DAG Processor

Reads Python DAG files and loads the DAG definitions.

### Executor

Determines how task instances are executed.

For a basic local setup, tasks run on the same Ubuntu machine.

### Metadata database

Stores:

* DAG runs
* Task states
* Users
* Variables
* Connections
* Logs and execution metadata

### API server and UI

Provides the Airflow web interface and API.

---

# 5. Install Airflow locally on Ubuntu

The current stable Airflow documentation supports local standalone setup using Python. Airflow’s officially supported Python installation uses `pip` or `uv`, and the constraints file provides a tested combination of dependencies. ([Apache Airflow][2])

## Step 1: Update Ubuntu

Open Ubuntu Terminal:

```bash
sudo apt update
sudo apt upgrade -y
```

---

## Step 2: Install Python prerequisites

```bash
sudo apt install python3 python3-pip python3-venv -y
```

Verify:

```bash
python3 --version
```

Airflow 3.3 supports Python 3.10 through Python 3.14. ([Apache Airflow][2])

For a stable beginner environment, Python 3.11 or 3.12 is a practical choice.

---

## Step 3: Create a project folder

```bash
mkdir -p ~/airflow-local-demo
cd ~/airflow-local-demo
```

---

## Step 4: Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Your terminal should show:

```text
(.venv)
```

---

## Step 5: Define `AIRFLOW_HOME`

Set Airflow’s home directory inside the project:

```bash
export AIRFLOW_HOME=~/airflow-local-demo/airflow
```

Verify:

```bash
echo $AIRFLOW_HOME
```

To make it permanent:

```bash
echo 'export AIRFLOW_HOME=~/airflow-local-demo/airflow' >> ~/.bashrc
source ~/.bashrc
```

Airflow creates `airflow.cfg` inside `$AIRFLOW_HOME` when it initializes. ([Apache Airflow][3])

---

## Step 6: Install Apache Airflow

Set the Airflow and Python versions:

```bash
AIRFLOW_VERSION=3.3.0
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
```

Install:

```bash
python -m pip install --upgrade pip
python -m pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "${CONSTRAINT_URL}"
```

Verify:

```bash
airflow version
```

Expected:

```text
3.3.0
```

---

# 6. Start Airflow in standalone mode

Run:

```bash
airflow standalone
```

This local quick-start command initializes Airflow and starts the services needed for a standalone learning environment. ([Apache Airflow][2])

The terminal displays:

* Username
* Password
* UI address

Typically, the UI is available at:

```text
http://localhost:8080
```

Keep this terminal open.

Open another Ubuntu terminal and activate the same environment:

```bash
cd ~/airflow-local-demo
source .venv/bin/activate
export AIRFLOW_HOME=~/airflow-local-demo/airflow
```

---

# 7. Find the DAG folder

Run:

```bash
airflow config get-value core dags_folder
```

It normally returns:

```text
/home/<username>/airflow-local-demo/airflow/dags
```

Create the folder if necessary:

```bash
mkdir -p "$AIRFLOW_HOME/dags"
```

Airflow reads Python source files from its DAG folder and executes those files to discover DAG objects. ([Apache Airflow][4])

---

# 8. Create your first simple DAG

Create:

```bash
nano "$AIRFLOW_HOME/dags/simple_retail_dag.py"
```

Add:

```python
from datetime import datetime

from airflow.sdk import DAG, task


with DAG(
    dag_id="simple_retail_sales_dag",
    description="Simple retail ETL workflow",
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
    tags=["training", "retail", "beginner"],
) as dag:

    @task
    def extract_sales():
        print("Extracting sales data")

        sales = [
            {"id": 1, "city": "Chennai", "amount": 5000},
            {"id": 2, "city": "Bengaluru", "amount": 8000},
            {"id": 3, "city": "Chennai", "amount": -100},
        ]

        return sales

    @task
    def validate_sales(sales):
        print("Validating sales records")

        valid_sales = [
            row
            for row in sales
            if row["amount"] > 0
        ]

        return valid_sales

    @task
    def calculate_revenue(valid_sales):
        print("Calculating total revenue")

        total_revenue = sum(
            row["amount"]
            for row in valid_sales
        )

        return total_revenue

    @task
    def display_result(total_revenue):
        print(
            f"Total valid revenue: {total_revenue}"
        )

    extracted_data = extract_sales()
    validated_data = validate_sales(extracted_data)
    revenue = calculate_revenue(validated_data)
    display_result(revenue)
```

Save:

```text
Ctrl + O
Enter
Ctrl + X
```

---

# 9. Understanding every DAG argument

The DAG section is:

```python
with DAG(
    dag_id="simple_retail_sales_dag",
    description="Simple retail ETL workflow",
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
    tags=["training", "retail", "beginner"],
) as dag:
```

## `dag_id`

```python
dag_id="simple_retail_sales_dag"
```

The `dag_id` is the unique identifier of the DAG.

It is used by:

* Airflow UI
* Scheduler
* CLI commands
* REST API
* Logs
* DAG runs
* Task instance identification

Example CLI:

```bash
airflow dags trigger simple_retail_sales_dag
```

List it:

```bash
airflow dags list
```

### Good DAG ID

```text
retail_daily_sales_pipeline
```

### Poor DAG ID

```text
dag1
```

### Recommended naming style

```text
<domain>_<frequency>_<purpose>
```

Examples:

```text
retail_daily_sales_etl
bank_hourly_transaction_check
healthcare_monthly_claim_summary
```

A dynamically generated DAG must produce a stable and consistent DAG ID every time Airflow parses the file. ([Apache Airflow][5])

---

## `description`

```python
description="Simple retail ETL workflow"
```

Provides a human-readable explanation in the UI.

It does not control execution.

---

## `start_date`

```python
start_date=datetime(2026, 7, 1)
```

Defines the earliest date from which Airflow can create scheduled runs.

It does **not** mean:

> Run immediately when the DAG file is created.

The actual scheduling behavior depends on:

* `start_date`
* `schedule`
* `catchup`

Airflow uses these values together to determine DAG runs and data intervals. ([Apache Airflow][6])

Use a fixed start date.

Good:

```python
start_date=datetime(2026, 7, 1)
```

Avoid:

```python
start_date=datetime.now()
```

A continuously changing start date can create confusing scheduling behavior.

---

## `schedule`

```python
schedule=None
```

Defines when Airflow should automatically create DAG runs.

### Manual-only DAG

```python
schedule=None
```

The DAG runs only when triggered manually or through an API.

### Daily DAG

```python
schedule="@daily"
```

### Hourly DAG

```python
schedule="@hourly"
```

### Cron schedule

```python
schedule="0 6 * * *"
```

Meaning:

```text
Run every day at 6:00 AM
```

Other examples:

| Requirement              | Schedule      |
| ------------------------ | ------------- |
| Every hour               | `"0 * * * *"` |
| Every day at midnight    | `"0 0 * * *"` |
| Every day at 6 AM        | `"0 6 * * *"` |
| Every Monday at 9 AM     | `"0 9 * * 1"` |
| First day of every month | `"0 0 1 * *"` |

---

## `catchup`

The user’s word “catcher” most likely refers to **`catchup`**.

```python
catchup=False
```

Catchup determines whether Airflow creates historical scheduled runs between the DAG’s start date and the current date.

Suppose:

```python
start_date=datetime(2026, 7, 1)
schedule="@daily"
```

and the DAG is enabled on July 10.

### `catchup=True`

Airflow may create runs for:

```text
July 1
July 2
July 3
...
July 9
```

### `catchup=False`

Airflow skips the missed historical intervals and schedules only the latest/current run.

Airflow defines catchup as creating DAG runs for schedule intervals that were not previously run. ([Apache Airflow][7])

For beginner demonstrations, use:

```python
catchup=False
```

For historical data processing or backfills, you may use:

```python
catchup=True
```

---

## `tags`

```python
tags=["training", "retail", "beginner"]
```

Tags help filter DAGs in the Airflow UI. ([Apache Airflow][8])

Examples:

```python
tags=["finance", "production"]
```

```python
tags=["data-quality", "hourly"]
```

Tags do not control dependencies or execution.

---

# 10. Understanding tasks

A task is the smallest unit of work in an Airflow workflow. Airflow supports operators, sensors and TaskFlow tasks. ([Apache Airflow][9])

Example:

```python
@task
def extract_sales():
    print("Extracting sales data")
```

Calling it creates a task:

```python
extracted_data = extract_sales()
```

The Python function defines what the task should do.

The task call adds the task to the DAG.

---

# 11. Understanding task IDs

When using the TaskFlow API:

```python
@task
def extract_sales():
    ...
```

Airflow automatically creates a task ID:

```text
extract_sales
```

You can assign a custom ID:

```python
@task(task_id="extract_retail_sales")
def extract_sales():
    ...
```

Task IDs must be unique inside one DAG.

A complete task instance is identified using values such as:

```text
dag_id
task_id
dag_run
map_index
```

Example:

```text
DAG ID: retail_daily_sales_etl
Task ID: validate_sales
Run: scheduled__2026-07-31
```

---

# 12. How dependencies are created

A dependency means:

> One task must complete before another task can start.

Airflow refers to tasks before another task as **upstream**, and tasks after it as **downstream**.

---

## Method 1: Data dependency using TaskFlow

```python
extracted_data = extract_sales()
validated_data = validate_sales(extracted_data)
revenue = calculate_revenue(validated_data)
display_result(revenue)
```

Because the output of one task is passed to the next task, Airflow automatically creates dependencies:

```text
extract_sales
      ↓
validate_sales
      ↓
calculate_revenue
      ↓
display_result
```

This is the cleanest approach when data moves between Python tasks.

---

## Method 2: Bitshift operator

```python
task_a >> task_b
```

Means:

```text
task_a runs before task_b
```

The reverse form:

```python
task_b << task_a
```

means the same thing.

Example:

```python
extract >> validate >> transform >> load
```

---

## Method 3: `set_downstream`

```python
extract.set_downstream(validate)
```

Equivalent to:

```python
extract >> validate
```

---

## Method 4: `set_upstream`

```python
validate.set_upstream(extract)
```

Equivalent to:

```python
extract >> validate
```

The `>>` and `<<` syntax is generally easier to read.

---

# 13. Sequential dependency example

```python
task_a >> task_b >> task_c
```

Graph:

```text
Task A
   ↓
Task B
   ↓
Task C
```

---

# 14. Parallel dependency example

```python
extract >> [validate_sales, validate_customers]
```

Graph:

```text
                 ┌→ Validate Sales
Extract Data ────┤
                 └→ Validate Customers
```

Both validation tasks can run after extraction.

---

# 15. Join dependency example

```python
[validate_sales, validate_customers] >> load_data
```

Graph:

```text
Validate Sales ───────┐
                      ├→ Load Data
Validate Customers ───┘
```

`load_data` waits for both validation tasks.

---

# 16. Complete dependency example using operators

Create:

```bash
nano "$AIRFLOW_HOME/dags/dependency_demo_dag.py"
```

Add:

```python
from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator


def extract_function():
    print("Extracting data")


def validate_sales_function():
    print("Validating sales")


def validate_customer_function():
    print("Validating customers")


def transform_function():
    print("Transforming data")


def load_function():
    print("Loading data")


with DAG(
    dag_id="dependency_demo_dag",
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
    tags=["dependencies"],
) as dag:

    start = EmptyOperator(
        task_id="start"
    )

    extract = PythonOperator(
        task_id="extract_data",
        python_callable=extract_function,
    )

    validate_sales = PythonOperator(
        task_id="validate_sales",
        python_callable=validate_sales_function,
    )

    validate_customers = PythonOperator(
        task_id="validate_customers",
        python_callable=validate_customer_function,
    )

    transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_function,
    )

    load = PythonOperator(
        task_id="load_data",
        python_callable=load_function,
    )

    end = EmptyOperator(
        task_id="end"
    )

    start >> extract

    extract >> [
        validate_sales,
        validate_customers,
    ]

    [
        validate_sales,
        validate_customers,
    ] >> transform

    transform >> load >> end
```

Result:

```text
Start
  ↓
Extract
  ↓
  ├───────────────┐
  ↓               ↓
Validate Sales   Validate Customers
  └───────────────┘
          ↓
      Transform
          ↓
        Load
          ↓
         End
```

---

# 17. Important task arguments

Example:

```python
extract = PythonOperator(
    task_id="extract_data",
    python_callable=extract_function,
    retries=2,
    retry_delay=timedelta(minutes=1),
)
```

## `task_id`

Unique task name inside the DAG.

```python
task_id="extract_data"
```

---

## `python_callable`

The Python function the operator should execute.

```python
python_callable=extract_function
```

Do not call the function here.

Correct:

```python
python_callable=extract_function
```

Incorrect:

```python
python_callable=extract_function()
```

---

## `retries`

Number of times Airflow retries a failed task.

```python
retries=2
```

This means:

```text
Initial attempt + up to 2 retries
```

---

## `retry_delay`

Delay between retries.

```python
retry_delay=timedelta(minutes=1)
```

---

## `execution_timeout`

Maximum allowed execution time:

```python
execution_timeout=timedelta(minutes=10)
```

---

## `owner`

Descriptive owner:

```python
owner="data-engineering-team"
```

This is useful for identification and operational ownership.

---

# 18. Using `default_args`

Common arguments can be placed once:

```python
from datetime import datetime, timedelta

default_args = {
    "owner": "data-engineering-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}
```

Then:

```python
with DAG(
    dag_id="retail_etl_dag",
    default_args=default_args,
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
) as dag:
```

Tasks inherit these defaults unless they override them.

Example:

```python
special_task = PythonOperator(
    task_id="special_task",
    python_callable=special_function,
    retries=5,
)
```

This task uses five retries instead of the default two.

---

# 19. Validate that Airflow loaded the DAG

Run:

```bash
airflow dags list
```

Filter:

```bash
airflow dags list | grep simple_retail_sales_dag
```

Check for import errors:

```bash
airflow dags list-import-errors
```

You can also test the Python file directly:

```bash
python "$AIRFLOW_HOME/dags/simple_retail_dag.py"
```

Airflow recommends treating DAGs as production code and testing them. ([Apache Airflow][10])

---

# 20. Trigger the DAG from CLI

Run:

```bash
airflow dags trigger simple_retail_sales_dag
```

List DAG runs:

```bash
airflow dags list-runs \
  --dag-id simple_retail_sales_dag
```

---

# 21. Trigger from the Airflow UI

1. Open:

```text
http://localhost:8080
```

2. Sign in.
3. Search for:

```text
simple_retail_sales_dag
```

4. Enable the DAG if required.
5. Click **Trigger DAG**.
6. Open the DAG.
7. Select **Graph** view.
8. Observe the task dependencies.
9. Click a task.
10. Open its logs.

---

# 22. What is a parameterized DAG?

A parameterized DAG accepts values at runtime.

Example parameters:

* City
* Minimum amount
* Input file
* Processing date
* Output format
* Environment

Airflow Params provide runtime configuration to tasks. Default values can be defined in the DAG and overridden during a manual trigger; Params are validated using JSON Schema. ([Apache Airflow][11])

---

# 23. Simple parameterized DAG

Create:

```bash
nano "$AIRFLOW_HOME/dags/parameterized_retail_dag.py"
```

Add:

```python
from datetime import datetime

from airflow.sdk import DAG, Param, task


with DAG(
    dag_id="parameterized_retail_sales_dag",
    description="Retail workflow controlled by runtime parameters",
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
    params={
        "city": Param(
            default="Chennai",
            type="string",
            description="City to process",
        ),
        "minimum_amount": Param(
            default=1000,
            type="number",
            minimum=0,
            description="Minimum accepted sale amount",
        ),
        "include_invalid": Param(
            default=False,
            type="boolean",
            description="Include invalid records",
        ),
    },
    tags=["retail", "parameters"],
) as dag:

    @task
    def extract_sales():
        return [
            {
                "id": 1,
                "city": "Chennai",
                "amount": 5000,
            },
            {
                "id": 2,
                "city": "Bengaluru",
                "amount": 8000,
            },
            {
                "id": 3,
                "city": "Chennai",
                "amount": -100,
            },
            {
                "id": 4,
                "city": "Chennai",
                "amount": 600,
            },
        ]

    @task
    def filter_sales(
        sales,
        city,
        minimum_amount,
        include_invalid,
    ):
        print(f"City parameter: {city}")
        print(
            f"Minimum amount: {minimum_amount}"
        )
        print(
            f"Include invalid: {include_invalid}"
        )

        filtered = []

        for row in sales:
            if row["city"] != city:
                continue

            if not include_invalid:
                if row["amount"] <= 0:
                    continue

            if row["amount"] < minimum_amount:
                continue

            filtered.append(row)

        return filtered

    @task
    def display_sales(filtered_sales):
        print("Filtered sales:")

        for row in filtered_sales:
            print(row)

    sales = extract_sales()

    filtered = filter_sales(
        sales=sales,
        city="{{ params.city }}",
        minimum_amount="{{ params.minimum_amount }}",
        include_invalid="{{ params.include_invalid }}",
    )

    display_sales(filtered)
```

---

# 24. Trigger the parameterized DAG

From the UI:

1. Open `parameterized_retail_sales_dag`.
2. Click **Trigger DAG**.
3. Enter values such as:

```json
{
  "city": "Chennai",
  "minimum_amount": 2000,
  "include_invalid": false
}
```

Trigger it.

The DAG structure stays the same:

```text
Extract → Filter → Display
```

But the values used by the tasks change.

This is a **parameterized DAG**, not dynamic DAG generation.

---

# 25. What is a dynamic DAG?

Dynamic DAG generation means Python code creates multiple DAG definitions from configuration.

Example requirement:

Create separate DAGs for:

```text
Chennai
Bengaluru
Coimbatore
```

Without dynamic generation, you would create:

```text
chennai_sales_dag.py
bengaluru_sales_dag.py
coimbatore_sales_dag.py
```

This causes duplicate code.

With dynamic DAG generation, one Python file produces:

```text
retail_sales_chennai
retail_sales_bengaluru
retail_sales_coimbatore
```

Airflow supports dynamically creating DAGs using the `@dag` decorator or `with DAG(...)` context manager; Airflow automatically registers the resulting DAGs. ([Apache Airflow][12])

---

# 26. Create a dynamic DAG generator

Create:

```bash
nano "$AIRFLOW_HOME/dags/dynamic_retail_dags.py"
```

Add:

```python
from datetime import datetime

from airflow.sdk import dag, task


CITY_CONFIGS = {
    "chennai": {
        "city_name": "Chennai",
        "minimum_amount": 1000,
        "schedule": "0 6 * * *",
    },
    "bengaluru": {
        "city_name": "Bengaluru",
        "minimum_amount": 2000,
        "schedule": "0 7 * * *",
    },
    "coimbatore": {
        "city_name": "Coimbatore",
        "minimum_amount": 500,
        "schedule": "0 8 * * *",
    },
}


def create_retail_dag(
    dag_id: str,
    city_name: str,
    minimum_amount: float,
    schedule: str,
):

    @dag(
        dag_id=dag_id,
        description=(
            f"Retail pipeline for {city_name}"
        ),
        start_date=datetime(2026, 7, 1),
        schedule=schedule,
        catchup=False,
        tags=[
            "dynamic",
            "retail",
            city_name.lower(),
        ],
    )
    def retail_city_pipeline():

        @task
        def extract_sales():
            print(
                f"Extracting sales for {city_name}"
            )

            return [
                {
                    "city": "Chennai",
                    "amount": 5000,
                },
                {
                    "city": "Bengaluru",
                    "amount": 8000,
                },
                {
                    "city": "Coimbatore",
                    "amount": 700,
                },
                {
                    "city": "Coimbatore",
                    "amount": 4000,
                },
            ]

        @task
        def filter_city_sales(sales):
            result = [
                row
                for row in sales
                if (
                    row["city"] == city_name
                    and row["amount"] >=
                    minimum_amount
                )
            ]

            print(
                f"Filtered records for {city_name}:"
            )
            print(result)

            return result

        @task
        def calculate_total(filtered_sales):
            total = sum(
                row["amount"]
                for row in filtered_sales
            )

            print(
                f"{city_name} total revenue: {total}"
            )

            return total

        extracted = extract_sales()
        filtered = filter_city_sales(extracted)
        calculate_total(filtered)

    return retail_city_pipeline()


for config_key, config in sorted(
    CITY_CONFIGS.items()
):
    generated_dag_id = (
        f"retail_sales_{config_key}_dag"
    )

    globals()[generated_dag_id] = (
        create_retail_dag(
            dag_id=generated_dag_id,
            city_name=config["city_name"],
            minimum_amount=(
                config["minimum_amount"]
            ),
            schedule=config["schedule"],
        )
    )
```

---

# 27. How the dynamic DAG code works

## Configuration

```python
CITY_CONFIGS = {
    "chennai": {...},
    "bengaluru": {...},
    "coimbatore": {...},
}
```

This determines how many DAGs are generated.

Three entries produce three DAGs.

---

## Factory function

```python
def create_retail_dag(...):
```

This function creates one complete DAG using the supplied configuration.

It is called a:

```text
DAG factory
```

---

## Dynamic DAG ID

```python
generated_dag_id = (
    f"retail_sales_{config_key}_dag"
)
```

Produces:

```text
retail_sales_chennai_dag
retail_sales_bengaluru_dag
retail_sales_coimbatore_dag
```

---

## Registering generated DAGs

```python
globals()[generated_dag_id] = (
    create_retail_dag(...)
)
```

This places each generated DAG object in the Python module’s global namespace so Airflow can discover it.

Modern Airflow can also automatically register DAGs generated through supported decorator or context-manager patterns. ([Apache Airflow][12])

---

## Stable ordering

```python
for config_key, config in sorted(
    CITY_CONFIGS.items()
):
```

Using `sorted()` ensures the generation order remains stable.

Dynamic DAG generation should consistently produce stable DAG IDs and task ordering across parses. ([Apache Airflow][12])

---

# 28. Validate the generated DAGs

Run:

```bash
airflow dags list | grep retail_sales
```

Expected DAG IDs:

```text
retail_sales_chennai_dag
retail_sales_bengaluru_dag
retail_sales_coimbatore_dag
```

Check import errors:

```bash
airflow dags list-import-errors
```

Test the file repeatedly:

```bash
python "$AIRFLOW_HOME/dags/dynamic_retail_dags.py"
python "$AIRFLOW_HOME/dags/dynamic_retail_dags.py"
```

The same DAG IDs should be generated each time.

---

# 29. Trigger one generated DAG

```bash
airflow dags trigger \
  retail_sales_chennai_dag
```

Trigger another:

```bash
airflow dags trigger \
  retail_sales_bengaluru_dag
```

Each generated DAG has its own:

* DAG ID
* Schedule
* Runs
* Task instances
* Logs
* UI page
* Configuration

---

# 30. Parameterized DAG vs dynamic DAG generation

## Parameterized DAG

One DAG:

```text
parameterized_retail_sales_dag
```

At trigger time, supply:

```json
{
  "city": "Chennai"
}
```

The DAG ID and task structure remain the same.

---

## Dynamic DAG generation

Configuration creates multiple DAGs:

```text
retail_sales_chennai_dag
retail_sales_bengaluru_dag
retail_sales_coimbatore_dag
```

Each is independently scheduled and monitored.

---

## Comparison

| Area            | Parameterized DAG        | Dynamic DAG generation              |
| --------------- | ------------------------ | ----------------------------------- |
| Number of DAGs  | Usually one              | Multiple                            |
| Values supplied | Runtime                  | DAG parsing time                    |
| DAG ID          | Same                     | Different for each configuration    |
| Schedule        | Usually one schedule     | Each DAG may have its own           |
| Monitoring      | Combined under one DAG   | Separate per generated DAG          |
| Main use        | Manual/configurable runs | Similar pipelines for many entities |

---

# 31. Dynamic DAG generation vs Dynamic Task Mapping

These are different.

## Dynamic DAG generation

Creates multiple DAGs during DAG-file parsing.

```text
Configuration
   ↓
DAG A
DAG B
DAG C
```

## Dynamic Task Mapping

Creates multiple task instances at runtime based on current data.

```text
One DAG
   ↓
Get list of files
   ↓
Process file 1
Process file 2
Process file 3
```

Airflow Dynamic Task Mapping lets a workflow create a runtime-determined number of task instances. ([Apache Airflow][13])

---

# 32. Simple Dynamic Task Mapping example

Create:

```bash
nano "$AIRFLOW_HOME/dags/dynamic_task_mapping_demo.py"
```

Add:

```python
from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="dynamic_task_mapping_demo",
    start_date=datetime(2026, 7, 1),
    schedule=None,
    catchup=False,
    tags=["dynamic-task-mapping"],
)
def dynamic_mapping_pipeline():

    @task
    def get_cities():
        return [
            "Chennai",
            "Bengaluru",
            "Coimbatore",
        ]

    @task
    def process_city(city: str):
        print(
            f"Processing sales for {city}"
        )

    cities = get_cities()

    process_city.expand(
        city=cities
    )


dynamic_mapping_pipeline()
```

At runtime, Airflow creates:

```text
get_cities
    ↓
process_city[0] → Chennai
process_city[1] → Bengaluru
process_city[2] → Coimbatore
```

This is one DAG with several mapped task instances.

---

# 33. Which approach should you use?

Use a **parameterized DAG** when:

* One workflow should accept different values.
* Runs should remain under one DAG ID.
* Users trigger the DAG with different input parameters.

Use **dynamic DAG generation** when:

* Each customer, region or source needs a separate schedule.
* Separate monitoring is required.
* Separate DAG IDs are useful.
* The pipelines have similar code but different configuration.

Use **Dynamic Task Mapping** when:

* The number of files or entities is known only at runtime.
* One task must run once per item.
* You want one DAG run with parallel task instances.

---

# 34. Professional recommendations

## Keep DAG parsing lightweight

Airflow repeatedly parses DAG files.

Avoid top-level code that:

* Calls a REST API
* Queries a database
* Reads a massive file
* Performs expensive calculations
* Sleeps
* Downloads data

Bad:

```python
customer_configs = requests.get(
    "https://example.com/configs"
).json()
```

at the top level of the DAG file.

Prefer:

* Environment variables
* Generated Python configuration
* Small local JSON/YAML files
* Airflow-supported configuration approaches
* Runtime API calls inside tasks

---

## Keep IDs stable

Do not generate IDs using:

```python
datetime.now()
random.random()
uuid.uuid4()
```

Bad:

```python
dag_id=f"sales_{datetime.now()}"
```

Every parse could create a different DAG ID.

Good:

```python
dag_id=f"sales_{customer_code}"
```

---

## Avoid spaces in IDs

Good:

```text
retail_daily_sales_dag
```

Avoid:

```text
Retail Daily Sales DAG
```

---

## Use clear dependency flow

Good:

```python
extract >> validate >> transform >> load
```

Avoid scattered dependencies that are difficult to understand.

---

## Make tasks idempotent

A retried task should not create duplicate or inconsistent results.

For example:

* Use `MERGE` instead of uncontrolled inserts.
* Overwrite one specific partition safely.
* Use execution date as a partition.
* Use unique business keys.
* Record batch IDs.

---

# 35. Recommended trainer demonstration order

1. Install Airflow using Ubuntu.
2. Run `airflow standalone`.
3. Open the UI.
4. Explain DAG, task and dependency.
5. Create a manual DAG with `schedule=None`.
6. Explain `dag_id`.
7. Explain `start_date`.
8. Explain `schedule`.
9. Explain `catchup`.
10. Create sequential dependencies.
11. Create parallel dependencies.
12. Trigger the DAG from the UI.
13. View Graph mode.
14. View logs.
15. Create a parameterized DAG.
16. Trigger it with JSON parameters.
17. Create dynamic city DAGs.
18. Verify three DAG IDs.
19. Trigger each generated DAG.
20. Create a Dynamic Task Mapping example.
21. Compare all three approaches.

---

# 36. Quick interview answers

## What is a DAG in Airflow?

A DAG is a Directed Acyclic Graph representing a workflow. It contains tasks and dependencies that determine their execution order.

## What is a dependency?

A dependency defines which task must complete before another task can start.

## What is `dag_id`?

`dag_id` is the unique name Airflow uses to identify a DAG in the scheduler, UI, CLI, API, runs and logs.

## What is `task_id`?

`task_id` uniquely identifies a task inside one DAG.

## What is `catchup`?

Catchup determines whether Airflow creates scheduled runs for intervals missed between the start date and the current scheduling point.

## What does `schedule=None` mean?

The DAG has no automatic schedule and must be triggered manually or programmatically.

## What is a parameterized DAG?

A parameterized DAG accepts runtime values such as city, date or minimum amount without changing its DAG structure.

## What is dynamic DAG generation?

Dynamic DAG generation uses Python configuration and loops to create multiple DAG objects from reusable code.

## What is Dynamic Task Mapping?

Dynamic Task Mapping creates multiple task instances at runtime based on data produced by an upstream task.

## Can a DAG contain a cycle?

No. Airflow DAGs must be acyclic because circular dependencies would prevent a valid task execution order.

[1]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html?utm_source=chatgpt.com "Architecture Overview — Airflow 3.3.0 Documentation"
[2]: https://airflow.apache.org/docs/apache-airflow/stable/start.html?utm_source=chatgpt.com "Quick Start — Airflow 3.3.0 Documentation - Apache Airflow"
[3]: https://airflow.apache.org/docs/apache-airflow/stable/howto/set-config.html?utm_source=chatgpt.com "Setting Configuration Options — Airflow 3.3.0 Documentation"
[4]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html?utm_source=chatgpt.com "Dags — Airflow 3.3.0 Documentation"
[5]: https://airflow.apache.org/docs/apache-airflow/stable/faq.html?utm_source=chatgpt.com "FAQ — Airflow 3.3.0 Documentation"
[6]: https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html?utm_source=chatgpt.com "Timetables — Airflow 3.3.0 Documentation"
[7]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html?utm_source=chatgpt.com "Dag Runs — Airflow 3.3.0 Documentation"
[8]: https://airflow.apache.org/docs/apache-airflow/stable/howto/add-dag-tags.html?utm_source=chatgpt.com "Add tags to Dags and use it for filtering in the UI - Apache Airflow"
[9]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html?utm_source=chatgpt.com "Tasks — Airflow 3.3.0 Documentation"
[10]: https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html?utm_source=chatgpt.com "Best Practices — Airflow 3.3.0 Documentation"
[11]: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html?utm_source=chatgpt.com "Params — Airflow 3.3.0 Documentation"
[12]: https://airflow.apache.org/docs/apache-airflow/stable/howto/dynamic-dag-generation.html?utm_source=chatgpt.com "Dynamic Dag Generation — Airflow 3.3.0 Documentation"
[13]: https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html?utm_source=chatgpt.com "Dynamic Task Mapping — Airflow 3.3.0 Documentation"
