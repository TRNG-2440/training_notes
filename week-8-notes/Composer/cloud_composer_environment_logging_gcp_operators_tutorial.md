# Cloud Composer Tutorial: Environment Setup, Cloud Logging Monitoring, and GCP-Native Operators

> **Current product name:** Google now presents Cloud Composer as **Managed Service for Apache Airflow** in parts of the Google Cloud Console and documentation. It is still commonly called Cloud Composer. It is a managed Apache Airflow service used to create, schedule, execute, and monitor workflows without manually maintaining Airflow infrastructure. ([Google Cloud Composer documentation](https://docs.cloud.google.com/composer/docs))

---

# 1. What You Will Build

In this tutorial, you will:

1. Create a Google Cloud project.
2. Enable the required APIs.
3. Create a service account for Composer.
4. Assign permissions.
5. Create a Cloud Composer environment.
6. Upload an Airflow DAG.
7. Execute the DAG from the Google Cloud Console.
8. Inspect DAG and task logs using Cloud Logging.
9. Use GCP-native Airflow operators.
10. Run a practical workflow using Cloud Storage and BigQuery.

The example workflow will perform this process:

```text
Start
  |
  v
Check whether a file exists in Cloud Storage
  |
  v
Create a BigQuery dataset
  |
  v
Create a BigQuery table using SQL
  |
  v
Run an aggregation query
  |
  v
Display the result
```

---

# 2. Cloud Composer Architecture

```text
                       Google Cloud Project
                                |
              +-----------------+-----------------+
              |                                   |
              v                                   v
      Cloud Composer Environment           Google Cloud Services
              |                                   |
    +---------+----------+              +---------+----------+
    |                    |              |                    |
    v                    v              v                    v
Airflow Scheduler   Airflow Workers   Cloud Storage       BigQuery
    |                    |
    |                    |
    +---------+----------+
              |
              v
        Airflow DAG Tasks
              |
              v
        Cloud Logging
              |
              v
      Logs Explorer / Alerts
```

When you upload a Python DAG file to the environment's `dags` folder, Composer synchronizes it with the Airflow components. Composer environments contain managed Airflow schedulers, workers, triggerers, monitoring components, networking, and storage integration. ([Environment architecture](https://docs.cloud.google.com/composer/docs/composer-3/environment-architecture))

---

# Part 1: Cloud Composer Environment Setup

# 3. Prerequisites

You need:

- A Google Cloud account
- An active Google Cloud project
- Billing enabled
- Permission to enable APIs
- Permission to create service accounts
- Permission to create Composer environments
- Permission to assign IAM roles

Cloud Composer creates billable resources. Delete the environment after completing the lab when it is no longer required.

---

# 4. Create or Select a Google Cloud Project

## Step 1: Open Google Cloud Console

Open the Google Cloud Console and sign in.

## Step 2: Select a project

At the top of the console:

```text
Project selector
→ Select an existing project
```

Or create one:

```text
Project selector
→ New Project
```

Example values:

| Property | Example |
|---|---|
| Project name | `composer-training-project` |
| Project ID | `composer-training-12345` |
| Organization | Select the appropriate organization |
| Location | Select the appropriate folder or organization |

Record your actual project ID. You will use it inside the DAG.

Example:

```python
PROJECT_ID = "composer-training-12345"
```

---

# 5. Enable Billing

Open:

```text
Navigation menu
→ Billing
```

Associate the project with an active billing account.

Composer environment creation will fail when billing is not enabled.

---

# 6. Enable the Required APIs

Open:

```text
Navigation menu
→ APIs & Services
→ Library
```

Search for and enable the following APIs:

| API | Purpose |
|---|---|
| Cloud Composer API | Creates and manages Composer environments |
| Compute Engine API | Supports environment compute resources |
| Kubernetes Engine API | Supports the managed environment infrastructure |
| Cloud Storage API | Stores DAGs, data and environment files |
| Cloud Logging API | Collects environment and task logs |
| Cloud Monitoring API | Collects metrics and health information |
| BigQuery API | Required for the BigQuery operator example |
| IAM API | Supports permissions and service accounts |

For the practical example, enable at least:

```text
Cloud Composer API
Cloud Storage API
BigQuery API
Cloud Logging API
Cloud Monitoring API
```

---

# 7. Create the Composer Service Account

Cloud Composer runs DAG tasks using an environment service account. This account needs the Composer Worker role plus permissions for the Google Cloud services used by the DAG. Google recommends granting extra resource permissions to this service account rather than embedding a JSON key in the DAG. ([Create environments](https://docs.cloud.google.com/composer/docs/composer-3/create-environments))

Open:

```text
Navigation menu
→ IAM & Admin
→ Service Accounts
```

Click:

```text
Create service account
```

Enter:

| Property | Value |
|---|---|
| Service account name | `composer-training-sa` |
| Service account ID | `composer-training-sa` |
| Description | `Service account used by Cloud Composer training environment` |

Click **Create and continue**.

The generated email resembles:

```text
composer-training-sa@PROJECT_ID.iam.gserviceaccount.com
```

---

# 8. Assign Permissions to the Composer Service Account

Assign these roles for the lab:

| Role | Why it is needed |
|---|---|
| Composer Worker | Required for the environment service account |
| Storage Object Admin | Allows the DAG to inspect and manage lab objects |
| BigQuery Job User | Allows execution of BigQuery jobs |
| BigQuery Data Editor | Allows creation and modification of datasets and tables |
| Logs Writer | Allows supported workloads to write logs |

The required base role for the environment service account is **Composer Worker**. Additional roles are required when DAGs access resources such as BigQuery, Cloud Storage or services in another project. ([Creating environments](https://docs.cloud.google.com/composer/docs/how-to/managing/creating))

For a training project, project-level roles are simpler. In production, use narrower permissions on specific buckets and datasets.

## Console procedure

Open:

```text
IAM & Admin
→ IAM
→ Grant access
```

In **New principals**, enter:

```text
composer-training-sa@PROJECT_ID.iam.gserviceaccount.com
```

Add the required roles one at a time, and then click **Save**.

---

# 9. Ensure Your User Can Use the Service Account

The user creating the environment generally needs:

- Permission to create Composer environments
- `iam.serviceAccounts.actAs` on the selected service account

A commonly used role for the second requirement is:

```text
Service Account User
```

The Composer environment creation permission includes `composer.environments.create`, while using the environment service account requires permission to act as that account. ([Access control](https://docs.cloud.google.com/composer/docs/composer-3/access-control))

Open:

```text
IAM & Admin
→ IAM
→ Grant access
```

Select your own Google account and add the appropriate Composer and service-account permissions according to your organization's security policy.

---

# 10. Create the Cloud Composer Environment

Google's current documentation describes Managed Airflow Gen 3 as the current managed environment option. The exact labels shown in the console can vary as Google updates the interface. ([Create environments](https://docs.cloud.google.com/composer/docs/composer-3/create-environments))

Open:

```text
Navigation menu
→ Composer
```

The page may appear as:

```text
Managed Service for Apache Airflow
```

Click:

```text
Create environment
```

Select the currently available managed environment generation, preferably **Gen 3** when available for your project and region.

---

# 11. Basic Environment Configuration

Use values similar to these:

| Property | Example |
|---|---|
| Environment name | `composer-training-env` |
| Region | `asia-south1` |
| Service account | `composer-training-sa@PROJECT_ID.iam.gserviceaccount.com` |
| Environment size | Smallest suitable training option |
| Network | Default |
| Subnetwork | Default |
| Web server access | Allow access according to your lab policy |

## Environment name rules

Use:

- lowercase letters
- numbers
- hyphens

Example:

```text
composer-training-env
```

Avoid spaces and underscores.

---

# 12. Select the Region Carefully

Create related resources in the same or a compatible location.

Example training setup:

```text
Composer region: asia-south1
Cloud Storage bucket region: asia-south1
BigQuery dataset location: asia-south1
```

A BigQuery dataset location is significant. Jobs can fail when the source, destination or job location is inconsistent.

For simplicity, this tutorial uses:

```python
REGION = "asia-south1"
BQ_LOCATION = "asia-south1"
```

Replace these values when the selected region differs.

---

# 13. Environment Sizing

For a basic training environment:

- Use the smallest available environment preset.
- Keep worker minimums low.
- Avoid unnecessarily large schedulers and workers.
- Do not enable extra features unless needed.

A Composer environment may continue generating charges while it exists, even when DAGs are not running.

Click:

```text
Create
```

Environment provisioning can take several minutes.

Wait until the status becomes:

```text
Running
```

---

# 14. Examine the Environment Details

Open:

```text
Composer
→ Environments
→ composer-training-env
```

You should see options such as:

- DAGs
- DAG UI
- Airflow UI
- Logs
- Monitoring
- Environment configuration
- PyPI packages
- Environment variables
- DAGs folder or bucket

The environment page provides access to Airflow information, logs, monitoring and the environment's Cloud Storage location. ([Environment architecture](https://docs.cloud.google.com/composer/docs/composer-3/environment-architecture))

---

# 15. Composer Environment Bucket

Composer uses a Cloud Storage bucket containing folders similar to:

```text
dags/
data/
logs/
plugins/
```

## Folder purposes

| Folder | Purpose |
|---|---|
| `dags/` | Stores Airflow Python DAG files |
| `data/` | Stores data or supporting files |
| `plugins/` | Stores custom Airflow plugins |
| `logs/` | May contain Airflow task log copies depending on configuration |

Composer schedules DAGs found in the environment's `/dags` folder. Uploaded files are synchronized and parsed with a small delay, commonly around one or two minutes. ([Manage DAGs](https://docs.cloud.google.com/composer/docs/composer-3/manage-dags))

---

# 16. Upload a Basic DAG

Create a file named:

```text
composer_basic_dag.py
```

Use this code:

```python
import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


def print_composer_message():
    print("Cloud Composer DAG is running successfully")


default_args = {
    "owner": "training",
    "start_date": datetime.datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=2),
}


with DAG(
    dag_id="composer_basic_dag",
    default_args=default_args,
    description="Basic Cloud Composer training DAG",
    schedule=None,
    catchup=False,
    tags=["composer", "training"],
) as dag:

    start_task = BashOperator(
        task_id="start_task",
        bash_command='echo "Starting Cloud Composer workflow"',
    )

    python_task = PythonOperator(
        task_id="python_task",
        python_callable=print_composer_message,
    )

    end_task = BashOperator(
        task_id="end_task",
        bash_command='echo "Cloud Composer workflow completed"',
    )

    start_task >> python_task >> end_task
```

---

# 17. Upload the DAG Through the Console

Open:

```text
Composer
→ Environments
```

Locate your environment.

In the **DAGs folder** column, click the folder link.

You will be taken to:

```text
Cloud Storage
→ Environment bucket
→ dags
```

Click:

```text
Upload files
```

Select:

```text
composer_basic_dag.py
```

Composer automatically synchronizes the file and reparses the DAG. Allow approximately one or two minutes for it to appear. ([Manage DAGs](https://docs.cloud.google.com/composer/docs/composer-3/manage-dags))

---

# 18. Run the DAG

Return to:

```text
Composer
→ Environments
→ composer-training-env
→ DAGs
```

Find:

```text
composer_basic_dag
```

Unpause or enable the DAG when required.

Click:

```text
Trigger DAG
```

Open the DAG and select:

```text
Grid
```

or:

```text
Graph
```

Expected dependency:

```text
start_task
    |
    v
python_task
    |
    v
end_task
```

Successful tasks normally appear green.

---

# Part 2: Monitoring Composer Through Cloud Logging

# 19. What Is Cloud Logging?

Cloud Logging collects log entries generated by:

- Airflow tasks
- Airflow scheduler
- Airflow workers
- Airflow triggerers
- DAG processors
- Web server components
- Environment infrastructure
- Composer agents
- Audit activities

Cloud Composer provides streaming Airflow task and component logs, while Cloud Monitoring collects health and performance metrics for the environment. ([View logs](https://docs.cloud.google.com/composer/docs/composer-3/view-logs))

---

# 20. Three Places to View Composer Logs

## Method 1: DAG task log

Open:

```text
Composer
→ Environments
→ DAGs
→ composer_basic_dag
→ Grid
```

Select a task, for example:

```text
python_task
```

Then click:

```text
Logs
```

You should find:

```text
Cloud Composer DAG is running successfully
```

This is the easiest method for checking one task execution.

## Method 2: Environment Logs tab

Open:

```text
Composer
→ Environments
→ composer-training-env
→ Logs
```

This shows logs associated with the selected environment.

You can filter by:

- severity
- DAG ID
- task ID
- scheduler
- worker
- time range
- log message

## Method 3: Logs Explorer

Open:

```text
Navigation menu
→ Logging
→ Logs Explorer
```

Logs Explorer is best for:

- searching across many DAG runs
- searching errors
- filtering by environment
- creating log-based metrics
- creating alerts
- sharing saved queries

---

# 21. Search for Errors in Logs Explorer

In the query editor, start with:

```text
severity>=ERROR
```

Click:

```text
Run query
```

This displays errors across the selected project.

To narrow the results:

1. Select the Composer or managed Airflow resource from the resource selector.
2. Select the environment.
3. Choose the appropriate time range.
4. Add the DAG or task name.

A practical message filter is:

```text
severity>=ERROR
"composer_basic_dag"
```

Another example:

```text
"python_task"
```

Because log field names can differ between environment versions and resource types, use the query builder to select an actual log entry and then choose **Show matching entries** or **Add field to query**.

---

# 22. Find a Particular DAG Run

Run the DAG manually.

Then open:

```text
Logging
→ Logs Explorer
```

Search:

```text
"composer_basic_dag"
```

Set the time range to:

```text
Last 1 hour
```

Expand a matching entry and inspect:

- timestamp
- severity
- DAG ID
- task ID
- try number
- execution date
- log message
- worker or scheduler component

---

# 23. Generate a Controlled Failure

Create a file named:

```text
composer_failure_demo.py
```

```python
import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def generate_error():
    raise ValueError("Training failure: customer input file was not found")


with DAG(
    dag_id="composer_failure_demo",
    start_date=datetime.datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["composer", "logging", "failure-demo"],
) as dag:

    fail_task = PythonOperator(
        task_id="generate_failure",
        python_callable=generate_error,
    )
```

Upload it to the Composer `dags` folder and trigger it.

Expected result:

```text
composer_failure_demo
└── generate_failure: FAILED
```

In Logs Explorer, search:

```text
"Training failure: customer input file was not found"
```

This demonstrates how application-specific messages make troubleshooting easier.

---

# 24. Useful Logging Statements in Python Tasks

Use Python's logging module rather than relying only on `print()`:

```python
import logging


def process_orders():
    logging.info("Order processing started")

    total_orders = 100
    successful_orders = 96
    failed_orders = 4

    logging.info("Total orders: %s", total_orders)
    logging.info("Successful orders: %s", successful_orders)

    if failed_orders > 0:
        logging.warning("Failed orders found: %s", failed_orders)

    logging.info("Order processing completed")
```

Levels:

| Level | Meaning |
|---|---|
| `DEBUG` | Detailed development information |
| `INFO` | Normal process progress |
| `WARNING` | Unexpected condition but task may continue |
| `ERROR` | Operation failed |
| `CRITICAL` | Severe system-level failure |

---

# 25. Composer Monitoring Dashboard

Open:

```text
Composer
→ Environments
→ composer-training-env
→ Monitoring
```

The dashboard can show metrics and trends for:

- successful and failed DAG runs
- task execution
- queued tasks
- scheduler health
- worker performance
- database health
- resource utilization
- Airflow components

The managed monitoring dashboard is designed to identify DAG-run trends and problems with Airflow components and environment resources. ([Monitoring dashboard](https://docs.cloud.google.com/composer/docs/composer-3/use-monitoring-dashboard))

---

# 26. Create a Log-Based Alert

A useful production alert is:

```text
Notify the support team when Composer task failures are logged.
```

## Step 1: Create a Logs Explorer query

Open:

```text
Logging
→ Logs Explorer
```

Use a query that finds your failure:

```text
severity>=ERROR
"composer_failure_demo"
```

Confirm that matching entries appear.

## Step 2: Create an alert

Click:

```text
Create alert
```

Depending on the console version, it may appear as:

```text
Actions
→ Create log alert
```

## Step 3: Configure the condition

Example:

| Property | Value |
|---|---|
| Alert name | `Composer DAG Failure Alert` |
| Condition | At least one matching log entry |
| Evaluation window | 5 minutes |
| Auto-close | According to operational policy |

## Step 4: Add notification channel

Possible channels include:

- email
- SMS where supported
- Slack through an integration
- webhook
- Pub/Sub
- incident-management integration

## Step 5: Test

Trigger `composer_failure_demo`.

Confirm that:

1. the task fails;
2. the log appears;
3. the alert condition opens;
4. the notification is delivered.

---

# Part 3: GCP-Native Airflow Operators

# 27. What Is a GCP-Native Operator?

An Airflow operator defines the work performed by one task.

GCP-native operators are operators from the Google Airflow provider that communicate directly with Google Cloud services.

Examples include:

| Google Cloud service | Example operator |
|---|---|
| BigQuery | `BigQueryInsertJobOperator` |
| Cloud Storage | `GCSObjectExistenceSensor` |
| Pub/Sub | `PubSubPublishMessageOperator` |
| Dataproc | `DataprocSubmitJobOperator` |
| Dataflow | Dataflow operators |
| Cloud Run | Cloud Run job operators |
| Vertex AI | Vertex AI operators |
| GKE | `GKEStartPodOperator` |
| Dataform | Dataform operators |

Google recommends using Google Cloud Airflow operators when a DAG needs to operate on Google Cloud products. For example, BigQuery operators execute queries and process BigQuery data. ([Write DAGs](https://docs.cloud.google.com/composer/docs/composer-3/write-dags))

---

# 28. Operator vs Hook vs Sensor

| Component | Purpose | Example |
|---|---|---|
| Operator | Performs an action | Run a BigQuery query |
| Sensor | Waits for a condition | Wait until a GCS object exists |
| Hook | Provides a lower-level API connection | Connect to BigQuery from Python |
| Transfer operator | Moves data between systems | GCS to BigQuery |
| Deferrable operator | Waits without occupying a worker continuously | Long-running cloud job sensor |

## Example comparison

```text
Operator:
Create a BigQuery table

Sensor:
Wait until orders.csv arrives

Hook:
Run custom BigQuery logic inside Python

Transfer:
Load orders.csv from GCS into BigQuery
```

Deferrable operators can reduce worker-slot usage while waiting for long-running external operations, provided support is enabled in the environment and operator. ([Deferrable operators](https://docs.cloud.google.com/composer/docs/composer-3/use-deferrable-operators))

---

# 29. Authentication in Cloud Composer

Inside Composer, you normally do not upload or reference a service-account JSON key.

The operator uses:

```text
google_cloud_default
```

and the Composer environment service account.

Conceptually:

```text
Airflow task
   |
   v
Google Cloud connection
   |
   v
Composer environment service account
   |
   v
IAM roles
   |
   v
GCS / BigQuery / Pub/Sub / Dataproc
```

This is why the Composer service account must have permission to use each target service.

---

# Part 4: Practical GCP-Native Operator Example

# 30. Example Requirement

Create an Airflow pipeline that:

1. waits for `input/employees.csv` in Cloud Storage;
2. creates a BigQuery dataset;
3. creates an employee table;
4. inserts sample records;
5. creates a department summary table;
6. verifies the output.

---

# 31. Create a Cloud Storage Bucket

Open:

```text
Navigation menu
→ Cloud Storage
→ Buckets
→ Create
```

Use:

| Property | Example |
|---|---|
| Bucket name | `PROJECT_ID-composer-training-data` |
| Location type | Region |
| Region | Same or compatible region as Composer |
| Storage class | Standard |
| Public access prevention | Enabled |
| Access control | Uniform |

Example bucket:

```text
composer-training-12345-composer-training-data
```

Bucket names are globally unique.

---

# 32. Create the Input CSV File

Create a local file named:

```text
employees.csv
```

```csv
employee_id,employee_name,department,salary
101,Anitha,Engineering,75000
102,Rajesh,Sales,62000
103,Meena,Engineering,81000
104,David,Finance,70000
105,Priya,Sales,66000
106,Arun,Finance,72000
```

---

# 33. Upload the CSV to Cloud Storage

Open:

```text
Cloud Storage
→ Buckets
→ YOUR_DATA_BUCKET
```

Create a folder:

```text
input
```

Open the folder and click:

```text
Upload files
```

Upload:

```text
employees.csv
```

Final object path:

```text
gs://YOUR_DATA_BUCKET/input/employees.csv
```

---

# 34. GCP-Native Operator DAG

Create:

```text
gcp_native_operator_demo.py
```

Replace these three values:

```python
PROJECT_ID = "YOUR_PROJECT_ID"
DATA_BUCKET = "YOUR_BUCKET_NAME"
BQ_LOCATION = "YOUR_BIGQUERY_LOCATION"
```

Use this code:

```python
import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryInsertJobOperator,
)


PROJECT_ID = "YOUR_PROJECT_ID"
DATA_BUCKET = "YOUR_BUCKET_NAME"
BQ_DATASET = "composer_training"
BQ_LOCATION = "asia-south1"


default_args = {
    "owner": "training",
    "start_date": datetime.datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=2),
}


with DAG(
    dag_id="gcp_native_operator_demo",
    default_args=default_args,
    description="Demonstrates GCS sensor and BigQuery operators",
    schedule=None,
    catchup=False,
    tags=["composer", "gcp", "gcs", "bigquery"],
) as dag:

    start = EmptyOperator(
        task_id="start",
    )

    wait_for_employee_file = GCSObjectExistenceSensor(
        task_id="wait_for_employee_file",
        bucket=DATA_BUCKET,
        object="input/employees.csv",
        google_cloud_conn_id="google_cloud_default",
        poke_interval=30,
        timeout=600,
        mode="reschedule",
    )

    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset",
        project_id=PROJECT_ID,
        dataset_id=BQ_DATASET,
        location=BQ_LOCATION,
        exists_ok=True,
        gcp_conn_id="google_cloud_default",
    )

    create_external_table = BigQueryInsertJobOperator(
        task_id="create_external_table",
        location=BQ_LOCATION,
        gcp_conn_id="google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE EXTERNAL TABLE
                    `{PROJECT_ID}.{BQ_DATASET}.employees_external`
                    (
                        employee_id INT64,
                        employee_name STRING,
                        department STRING,
                        salary NUMERIC
                    )
                    OPTIONS (
                        format = 'CSV',
                        uris = ['gs://{DATA_BUCKET}/input/employees.csv'],
                        skip_leading_rows = 1
                    )
                """,
                "useLegacySql": False,
            }
        },
    )

    create_department_summary = BigQueryInsertJobOperator(
        task_id="create_department_summary",
        location=BQ_LOCATION,
        gcp_conn_id="google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE
                    `{PROJECT_ID}.{BQ_DATASET}.department_salary_summary`
                    AS
                    SELECT
                        department,
                        COUNT(*) AS employee_count,
                        SUM(salary) AS total_salary,
                        ROUND(AVG(salary), 2) AS average_salary,
                        MAX(salary) AS maximum_salary,
                        MIN(salary) AS minimum_salary
                    FROM
                        `{PROJECT_ID}.{BQ_DATASET}.employees_external`
                    GROUP BY
                        department
                """,
                "useLegacySql": False,
            }
        },
    )

    validate_summary = BigQueryInsertJobOperator(
        task_id="validate_summary",
        location=BQ_LOCATION,
        gcp_conn_id="google_cloud_default",
        configuration={
            "query": {
                "query": f"""
                    SELECT
                        department,
                        employee_count,
                        total_salary,
                        average_salary
                    FROM
                        `{PROJECT_ID}.{BQ_DATASET}.department_salary_summary`
                    ORDER BY
                        department
                """,
                "useLegacySql": False,
            }
        },
    )

    end = EmptyOperator(
        task_id="end",
    )

    (
        start
        >> wait_for_employee_file
        >> create_dataset
        >> create_external_table
        >> create_department_summary
        >> validate_summary
        >> end
    )
```

---

# 35. Workflow Diagram

```text
start
  |
  v
wait_for_employee_file
GCSObjectExistenceSensor
  |
  v
create_dataset
BigQueryCreateEmptyDatasetOperator
  |
  v
create_external_table
BigQueryInsertJobOperator
  |
  v
create_department_summary
BigQueryInsertJobOperator
  |
  v
validate_summary
BigQueryInsertJobOperator
  |
  v
end
```

---

# 36. Explanation of the Operators

## `GCSObjectExistenceSensor`

```python
wait_for_employee_file = GCSObjectExistenceSensor(
    task_id="wait_for_employee_file",
    bucket=DATA_BUCKET,
    object="input/employees.csv",
)
```

Purpose:

```text
Wait until employees.csv exists in the bucket.
```

Without this sensor, the query might run before the input file arrives.

### Important options

| Option | Meaning |
|---|---|
| `bucket` | Bucket name without `gs://` |
| `object` | Path inside the bucket |
| `poke_interval` | Seconds between checks |
| `timeout` | Maximum waiting time |
| `mode="reschedule"` | Releases the worker between checks |

## `BigQueryCreateEmptyDatasetOperator`

```python
create_dataset = BigQueryCreateEmptyDatasetOperator(
    project_id=PROJECT_ID,
    dataset_id=BQ_DATASET,
    location=BQ_LOCATION,
    exists_ok=True,
)
```

Purpose:

```text
Create the BigQuery dataset when it does not already exist.
```

`exists_ok=True` prevents failure when the dataset already exists.

## `BigQueryInsertJobOperator`

```python
BigQueryInsertJobOperator(
    configuration={
        "query": {
            "query": "SELECT ...",
            "useLegacySql": False,
        }
    }
)
```

Purpose:

```text
Submit a BigQuery job.
```

It can execute:

- `SELECT`
- `CREATE TABLE`
- `CREATE OR REPLACE TABLE`
- `INSERT`
- `UPDATE`
- `DELETE`
- `MERGE`
- stored procedures

---

# 37. Upload and Execute the DAG

Upload:

```text
gcp_native_operator_demo.py
```

to:

```text
Composer
→ Environments
→ DAGs folder
→ Upload files
```

Wait for synchronization.

Then open:

```text
Composer
→ Environments
→ DAGs
→ gcp_native_operator_demo
```

Click:

```text
Trigger DAG
```

Follow task execution using:

```text
Grid
```

or:

```text
Graph
```

---

# 38. Verify the BigQuery Output

Open:

```text
Navigation menu
→ BigQuery
```

In Explorer, expand:

```text
YOUR_PROJECT_ID
└── composer_training
    ├── employees_external
    └── department_salary_summary
```

Open:

```text
department_salary_summary
→ Preview
```

Expected output:

| department | employee_count | total_salary | average_salary |
|---|---:|---:|---:|
| Engineering | 2 | 156000 | 78000 |
| Finance | 2 | 142000 | 71000 |
| Sales | 2 | 128000 | 64000 |

---

# 39. Monitor the GCP-Native DAG in Cloud Logging

Open:

```text
Logging
→ Logs Explorer
```

Search:

```text
"gcp_native_operator_demo"
```

To focus on errors:

```text
severity>=ERROR
"gcp_native_operator_demo"
```

To inspect one task:

```text
"create_department_summary"
```

Check for messages such as:

- BigQuery job submitted
- BigQuery job ID
- query completed
- permission denied
- dataset not found
- bucket object not found
- location mismatch
- task retry

---

# Part 5: Other Useful GCP-Native Operators

# 40. Cloud Storage Operators

Common examples:

```python
from airflow.providers.google.cloud.operators.gcs import (
    GCSCreateBucketOperator,
    GCSDeleteObjectsOperator,
    GCSListObjectsOperator,
)
```

Typical uses:

```text
Create a bucket
List objects
Delete processed files
Copy or move objects
Check file arrival
```

The Google provider includes dedicated Cloud Storage operators and transfer operators for GCS-related workflows. ([Cloud Storage operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/gcs.html))

---

# 41. Pub/Sub Operator

A Pub/Sub operator can publish a pipeline-completion event.

Example:

```python
from airflow.providers.google.cloud.operators.pubsub import (
    PubSubPublishMessageOperator,
)


publish_message = PubSubPublishMessageOperator(
    task_id="publish_message",
    project_id=PROJECT_ID,
    topic="pipeline-events",
    messages=[
        {
            "data": b"Employee pipeline completed successfully",
            "attributes": {
                "pipeline": "employee-processing",
                "status": "success",
            },
        }
    ],
)
```

Possible use:

```text
BigQuery processing completes
        |
        v
Publish completion event to Pub/Sub
        |
        v
Subscriber receives event
        |
        v
Send notification or start another system
```

The Composer service account needs permission to publish messages to the topic.

---

# 42. Dataproc Operator

A Dataproc operator can create a cluster or submit a Spark job.

Example import:

```python
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocSubmitJobOperator,
)
```

Typical flow:

```text
Input data in GCS
   |
   v
Composer starts Dataproc Spark job
   |
   v
Spark transforms data
   |
   v
Output saved to GCS or BigQuery
```

Dataproc operators can create managed clusters and submit jobs while waiting for the Google Cloud operation to complete. ([Dataproc operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/_api/airflow/providers/google/cloud/operators/dataproc/index.html))

---

# 43. Dataflow Operator

A Dataflow operator can launch Apache Beam pipelines.

Typical workflow:

```text
File arrives in Cloud Storage
   |
   v
Composer starts Dataflow pipeline
   |
   v
Dataflow transforms data
   |
   v
Output written to BigQuery
```

Google provides Composer guidance for launching Dataflow pipelines using managed Airflow DAGs. ([Launch Dataflow pipelines](https://docs.cloud.google.com/composer/docs/composer-3/launch-dataflow-pipelines))

---

# 44. Cloud Run Job Operator

Cloud Run operators can manage and execute Cloud Run jobs.

Typical use:

```text
Composer DAG
   |
   v
Execute containerized Cloud Run Job
   |
   v
Job performs Python or Java processing
   |
   v
Return execution status to Airflow
```

Cloud Run operator parameters commonly include:

- project ID
- region
- job name
- overrides
- timeout
- connection ID

The current Google provider includes operators for creating and managing Cloud Run jobs. ([Cloud Run operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/_api/airflow/providers/google/cloud/operators/cloud_run/index.html))

---

# Part 6: PyPI Packages and Environment Variables

# 45. Install an Additional Python Package

Some packages are already installed with Composer. Do not install another version of the Google Airflow provider without checking compatibility.

Open:

```text
Composer
→ Environments
→ composer-training-env
→ PyPI packages
```

Click:

```text
Edit
```

Add:

| Package | Version |
|---|---|
| `pandas` | A version compatible with the environment |

Save the environment update.

Package installation updates the environment and may take several minutes. Only users with the relevant environment-update permission can change PyPI packages, and package conflicts can cause update failures. ([Install Python dependencies](https://docs.cloud.google.com/composer/docs/composer-3/install-python-dependencies))

---

# 46. Add Environment Variables

Open:

```text
Composer
→ Environments
→ composer-training-env
→ Environment variables
→ Edit
```

Example:

| Name | Value |
|---|---|
| `TRAINING_BUCKET` | `your-bucket-name` |
| `BQ_DATASET` | `composer_training` |

Read them in a DAG:

```python
import os

TRAINING_BUCKET = os.environ.get("TRAINING_BUCKET")
BQ_DATASET = os.environ.get("BQ_DATASET", "composer_training")
```

Do not store passwords or private keys in plain environment variables. Use Secret Manager for secrets.

---

# Part 7: Troubleshooting

# 47. DAG Does Not Appear

Check:

1. The file has a `.py` extension.
2. It is uploaded directly under the environment's `dags/` folder.
3. The Python file contains a valid DAG object.
4. The DAG ID is unique.
5. Imports are compatible with the installed Airflow/provider version.
6. Wait at least one or two minutes.
7. Check environment logs for import errors.

Recommended imports:

```python
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
```

Avoid older imports such as:

```python
from airflow import BashOperator
from airflow.operators import PythonOperator
```

---

# 48. Broken DAG or Import Error

Open:

```text
Composer
→ Environments
→ DAGs
```

Look for:

```text
Import errors
```

Or use Logs Explorer:

```text
severity>=ERROR
"Broken DAG"
```

Common causes:

- missing Python package
- wrong import path
- syntax error
- undefined variable
- unsupported provider class
- indentation error
- duplicate task ID
- invalid dependency syntax

---

# 49. Permission Denied

Example error:

```text
403 Permission denied
```

Check:

```text
IAM & Admin
→ IAM
```

Confirm the Composer environment service account has the required role.

Examples:

| Operation | Required permission category |
|---|---|
| Run BigQuery query | BigQuery Job User |
| Create or update tables | BigQuery Data Editor |
| Read a GCS file | Storage Object Viewer |
| Write a GCS file | Storage Object Creator or Admin |
| Publish Pub/Sub message | Pub/Sub Publisher |
| Run Dataproc job | Dataproc permissions |
| Execute Cloud Run job | Cloud Run permissions |

Do not grant `Owner` only to solve a permission error. Identify the missing permission and apply the narrowest suitable role.

---

# 50. BigQuery Location Error

Example:

```text
Not found: Dataset was not found in location
```

Check:

```python
BQ_LOCATION = "asia-south1"
```

The operator location and dataset location must match.

Open:

```text
BigQuery
→ Dataset
→ Details
→ Data location
```

Use that exact value in the DAG.

---

# 51. GCS Sensor Keeps Waiting

Check:

```python
bucket=DATA_BUCKET
object="input/employees.csv"
```

The bucket must not include:

```text
gs://
```

Correct:

```python
bucket="my-training-bucket"
```

Incorrect:

```python
bucket="gs://my-training-bucket"
```

Also confirm capitalization and folder names. Cloud Storage object paths are case-sensitive.

---

# 52. Task Remains Queued

Possible causes:

- no worker capacity
- environment resources are too small
- many parallel tasks
- pool limits
- concurrency settings
- worker startup delay
- scheduler issue

Check:

```text
Composer
→ Environment
→ Monitoring
```

Review:

- queued tasks
- running tasks
- worker utilization
- scheduler health
- task duration

---

# 53. Environment Creation Fails

Check:

- Composer API is enabled.
- Billing is enabled.
- The selected region supports the environment.
- Your account can create environments.
- Your account can act as the environment service account.
- The service account has Composer Worker.
- Organization policies permit the required network and service resources.

Google's troubleshooting guidance highlights missing user and service-account permissions as a frequent environment-creation problem. ([Troubleshooting environment creation](https://docs.cloud.google.com/composer/docs/composer-3/troubleshooting-environment-creation))

---

# Part 8: Best Practices

## Security

- Use a dedicated Composer service account.
- Avoid service-account key files.
- Use least-privilege IAM roles.
- Use Secret Manager for passwords and tokens.
- Restrict Airflow web-server access.
- Separate development and production environments.

## DAG development

- Keep DAG files lightweight.
- Do not perform API calls while the DAG file is being imported.
- Use operators for cloud operations.
- Make task IDs meaningful.
- Add retries only for recoverable failures.
- Avoid hard-coding project IDs where configuration is preferable.
- Log important business checkpoints.

## Reliability

- Use sensors for external dependencies.
- Use `mode="reschedule"` or deferrable sensors when appropriate.
- Set execution timeouts.
- Configure retry delays.
- Design tasks to be idempotent.
- Validate data before publishing downstream output.

## Cost control

- Use the smallest appropriate environment.
- Delete training environments after use.
- Avoid unnecessary polling.
- Avoid keeping temporary Dataproc clusters running.
- Use BigQuery partitioning for large datasets.
- Review Cloud Billing reports and budgets.

---

# 54. Complete Real-World Scenario

## Requirement

A retail organization receives a daily sales file.

```text
sales_2026_08_05.csv
```

The required pipeline is:

```text
1. Wait for the sales file in GCS
2. Validate that the file exists
3. Load data into BigQuery
4. Transform and aggregate city-wise sales
5. Run a data-quality query
6. Publish a Pub/Sub completion event
7. Monitor failures through Cloud Logging
8. Notify support through an alert
```

## Suitable Airflow components

| Requirement | Component |
|---|---|
| Wait for file | `GCSObjectExistenceSensor` |
| Load to BigQuery | GCS-to-BigQuery transfer operator |
| Transform | `BigQueryInsertJobOperator` |
| Data quality | BigQuery check operator |
| Publish event | `PubSubPublishMessageOperator` |
| Error inspection | Cloud Logging |
| Health monitoring | Cloud Monitoring |
| Notification | Log-based alert |

---

# 55. Final Checklist

## Environment setup

```text
[ ] Google Cloud project selected
[ ] Billing enabled
[ ] Composer API enabled
[ ] BigQuery API enabled
[ ] Cloud Storage API enabled
[ ] Service account created
[ ] Composer Worker assigned
[ ] BigQuery permissions assigned
[ ] Storage permissions assigned
[ ] Composer environment running
```

## DAG deployment

```text
[ ] Python DAG file created
[ ] Modern Airflow imports used
[ ] Project ID replaced
[ ] Bucket name replaced
[ ] BigQuery location checked
[ ] DAG uploaded to /dags
[ ] DAG visible in the console
[ ] DAG triggered
[ ] Tasks completed successfully
```

## Monitoring

```text
[ ] Task logs inspected
[ ] Environment logs inspected
[ ] Logs Explorer query tested
[ ] Failure demo executed
[ ] Monitoring dashboard reviewed
[ ] Log-based alert created
```

# Summary

**Cloud Composer environment setup** creates a managed Apache Airflow platform, including schedulers, workers, a DAG bucket, logging and monitoring integrations.

**Cloud Logging** helps diagnose task failures, scheduler issues, permission problems, import errors and environment problems.

**GCP-native operators** allow Airflow tasks to interact directly with BigQuery, Cloud Storage, Pub/Sub, Dataproc, Dataflow, Cloud Run, GKE and other Google Cloud services using the Composer environment service account.
