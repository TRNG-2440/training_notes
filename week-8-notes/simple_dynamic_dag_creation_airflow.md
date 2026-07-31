# Simple Dynamic DAG Creation in Apache Airflow

Below is a simple continuation of the retail-sales example. This version dynamically creates **multiple DAGs from one Python file**.

One configuration creates one DAG:

```text
chennai configuration  → retail_sales_chennai_dag
bangalore configuration → retail_sales_bangalore_dag
hyderabad configuration → retail_sales_hyderabad_dag
```

Airflow supports generating DAGs through normal Python loops and automatically registers DAGs created using the `@dag` decorator.

---

# Step 1: Create the Dynamic DAG File

Inside VS Code, create this file:

```text
~/airflow-local-demo/airflow/dags/dynamic_retail_sales_dags.py
```

---

# Step 2: Copy and Paste This Complete Code

```python
from datetime import datetime

from airflow.sdk import dag, task


# Configuration used to generate multiple DAGs
RETAIL_STORES = {
    "chennai": {
        "store_name": "Chennai Retail Store",
        "target_table": "chennai_daily_sales",
    },
    "bangalore": {
        "store_name": "Bangalore Retail Store",
        "target_table": "bangalore_daily_sales",
    },
    "hyderabad": {
        "store_name": "Hyderabad Retail Store",
        "target_table": "hyderabad_daily_sales",
    },
}


# Loop through every store configuration
for store_code, store_config in RETAIL_STORES.items():

    dynamic_dag_id = f"retail_sales_{store_code}_dag"

    @dag(
        dag_id=dynamic_dag_id,
        description=f"Retail sales ETL for {store_config['store_name']}",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["retail", "dynamic-dag", store_code],
    )
    def create_retail_sales_dag():

        @task
        def extract_sales(store_name):
            print(f"Extracting sales data for {store_name}")

        @task
        def transform_sales(store_name):
            print(f"Transforming sales data for {store_name}")

        @task
        def load_sales(store_name, target_table):
            print(f"Loading sales data for {store_name}")
            print(f"Target table: {target_table}")

        extract_task = extract_sales(
            store_name=store_config["store_name"]
        )

        transform_task = transform_sales(
            store_name=store_config["store_name"]
        )

        load_task = load_sales(
            store_name=store_config["store_name"],
            target_table=store_config["target_table"],
        )

        extract_task >> transform_task >> load_task

    # Create and register one DAG for the current store
    create_retail_sales_dag()
```

Save the file using:

```text
Ctrl + S
```

---

# Step 3: Understand the Configuration

This dictionary contains the information used to generate the DAGs:

```python
RETAIL_STORES = {
    "chennai": {
        "store_name": "Chennai Retail Store",
        "target_table": "chennai_daily_sales",
    },
    "bangalore": {
        "store_name": "Bangalore Retail Store",
        "target_table": "bangalore_daily_sales",
    },
    "hyderabad": {
        "store_name": "Hyderabad Retail Store",
        "target_table": "hyderabad_daily_sales",
    },
}
```

There are three configurations, so Airflow creates three separate DAGs.

| Configuration key | Generated DAG |
|---|---|
| `chennai` | `retail_sales_chennai_dag` |
| `bangalore` | `retail_sales_bangalore_dag` |
| `hyderabad` | `retail_sales_hyderabad_dag` |

---

# Step 4: Understand the Loop

```python
for store_code, store_config in RETAIL_STORES.items():
```

The loop runs three times.

On the first iteration:

```text
store_code   = chennai
store_config = Chennai configuration
```

On the second iteration:

```text
store_code   = bangalore
store_config = Bangalore configuration
```

On the third iteration:

```text
store_code   = hyderabad
store_config = Hyderabad configuration
```

---

# Step 5: Understand the Dynamic DAG ID

```python
dynamic_dag_id = f"retail_sales_{store_code}_dag"
```

For Chennai, Python creates:

```text
retail_sales_chennai_dag
```

For Bangalore:

```text
retail_sales_bangalore_dag
```

For Hyderabad:

```text
retail_sales_hyderabad_dag
```

Each generated DAG has a unique `dag_id`. Airflow requires every DAG ID to be unique.

---

# Step 6: Understand the DAG Factory

```python
@dag(
    dag_id=dynamic_dag_id,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
)
def create_retail_sales_dag():
```

This function acts as a **DAG factory**.

A factory is code that creates similar objects repeatedly. Here, it creates a similar retail-sales DAG for each store.

The DAG structure remains the same:

```text
extract_sales
      ↓
transform_sales
      ↓
load_sales
```

Only the store information changes.

---

# Step 7: Understand the Tasks

## Extract Task

```python
@task
def extract_sales(store_name):
    print(f"Extracting sales data for {store_name}")
```

For Chennai, its log will show:

```text
Extracting sales data for Chennai Retail Store
```

## Transform Task

```python
@task
def transform_sales(store_name):
    print(f"Transforming sales data for {store_name}")
```

For Chennai:

```text
Transforming sales data for Chennai Retail Store
```

## Load Task

```python
@task
def load_sales(store_name, target_table):
    print(f"Loading sales data for {store_name}")
    print(f"Target table: {target_table}")
```

For Chennai:

```text
Loading sales data for Chennai Retail Store
Target table: chennai_daily_sales
```

---

# Step 8: Understand DAG Registration

The following line is essential:

```python
create_retail_sales_dag()
```

It calls the decorated function during each loop iteration.

That causes Airflow to create and register one DAG for every configuration.

---

# Step 9: Check the Python File

Open the VS Code terminal and run:

```bash
cd ~/airflow-local-demo

source .venv/bin/activate

export AIRFLOW_HOME=$HOME/airflow-local-demo/airflow
```

Test the file:

```bash
python "$AIRFLOW_HOME/dags/dynamic_retail_sales_dags.py"
```

Expected result:

```text
No output
No error
```

This checks whether the file can be parsed. It does not execute the tasks.

---

# Step 10: Check for Import Errors

Run:

```bash
airflow dags list-import-errors --local
```

Expected result:

```text
No data found
```

Any indentation, syntax, or import problem will be displayed by this command.

---

# Step 11: Confirm That the Dynamic DAGs Were Created

Run:

```bash
airflow dags list --local | grep retail_sales
```

Expected output should include:

```text
retail_sales_chennai_dag
retail_sales_bangalore_dag
retail_sales_hyderabad_dag
```

One Python file has now generated three DAGs.

---

# Step 12: Start Airflow

Run:

```bash
airflow standalone
```

Keep this terminal open.

Then open:

```text
http://localhost:8080
```

Wait for the DAG processor to parse the file and refresh the browser.

---

# Step 13: Find the DAGs in the Web UI

Search for:

```text
retail_sales
```

You should see:

```text
retail_sales_chennai_dag
retail_sales_bangalore_dag
retail_sales_hyderabad_dag
```

Open any one of them and select **Graph**.

The graph should show:

```text
extract_sales
      ↓
transform_sales
      ↓
load_sales
```

---

# Step 14: Trigger One DAG

Open:

```text
retail_sales_chennai_dag
```

Then:

1. Click **Trigger DAG**.
2. Open the new DAG run.
3. Check the Graph view.
4. Wait until all three tasks turn green.
5. Open each task and select **Logs**.

The Chennai load-task log should contain:

```text
Loading sales data for Chennai Retail Store
Target table: chennai_daily_sales
```

The Bangalore DAG will use:

```text
Bangalore Retail Store
bangalore_daily_sales
```

The Hyderabad DAG will use:

```text
Hyderabad Retail Store
hyderabad_daily_sales
```

---

# Step 15: Add Another Store Dynamically

Add this entry inside `RETAIL_STORES`:

```python
"pune": {
    "store_name": "Pune Retail Store",
    "target_table": "pune_daily_sales",
},
```

The complete configuration becomes:

```python
RETAIL_STORES = {
    "chennai": {
        "store_name": "Chennai Retail Store",
        "target_table": "chennai_daily_sales",
    },
    "bangalore": {
        "store_name": "Bangalore Retail Store",
        "target_table": "bangalore_daily_sales",
    },
    "hyderabad": {
        "store_name": "Hyderabad Retail Store",
        "target_table": "hyderabad_daily_sales",
    },
    "pune": {
        "store_name": "Pune Retail Store",
        "target_table": "pune_daily_sales",
    },
}
```

Save the file and refresh the Airflow UI.

A new DAG should appear:

```text
retail_sales_pune_dag
```

You do not need to copy and rewrite the complete DAG for Pune. That is the main advantage of dynamic DAG generation.

---

# Static DAG Versus Dynamic DAG

Your previous static file created one DAG:

```text
simple_retail_sales_dag.py
        ↓
simple_retail_sales_dag
```

The new dynamic file creates multiple DAGs:

```text
dynamic_retail_sales_dags.py
        │
        ├── retail_sales_chennai_dag
        ├── retail_sales_bangalore_dag
        └── retail_sales_hyderabad_dag
```

The number of tasks inside each DAG remains fixed. The Python configuration controls how many similar DAGs are generated.

This is dynamic DAG generation. It differs from Dynamic Task Mapping, where the scheduler creates a variable number of task instances at runtime.
