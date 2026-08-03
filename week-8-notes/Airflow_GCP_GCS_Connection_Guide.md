# Apache Airflow to Google Cloud Storage (GCS) — Step-by-Step Guide

You can connect your **local Apache Airflow running in Docker** to this GCP bucket:

```text
Bucket: azctsdemo1bucket
Object: input/customers.csv
GCS URI: gs://azctsdemo1bucket/input/customers.csv
```

Because the object is marked **Not public**, Airflow must authenticate using a GCP service account. The “Public URL” shown in the screenshot will not work without authenticated access.

---

## Overall Flow

```text
GCP Cloud Storage
azctsdemo1bucket/input/customers.csv
              │
              │ Service-account authentication
              ▼
Airflow Docker container
Google Cloud connection: google_cloud_default
              │
              ▼
GCSHook downloads CSV
              │
              ▼
Airflow task reads and prints records
```

---

# Part 1 — Complete the GCP-Side Settings

## Step 1: Confirm the Correct Google Cloud Project

In the Google Cloud Console:

1. Click the project selector at the top.
2. Select the project containing:
   - `azctsdemo1bucket`
   - `airflow-gcs-service-account`
3. Go to **IAM & Admin → Settings**.
4. Copy the **Project ID**.

Do not use the project name shown as **BigQuery Optimization Lab** unless that is also the actual Project ID.

Project names can contain spaces, but a Project ID normally looks like:

```text
bigquery-optimization-lab-123456
```

Keep this value. We will use it in Airflow.

---

## Step 2: Enable the Cloud Storage API

In the GCP Console:

1. Open the navigation menu.
2. Select **APIs & Services → Library**.
3. Search for:

```text
Cloud Storage API
```

4. Open it.
5. Click **Enable** if it is not already enabled.

For this particular DAG, you do not need BigQuery API, Compute Engine API, or Cloud Composer.

---

## Step 3: Find the Service-Account Email

You already created a service account named:

```text
airflow-gcs-service-account
```

Now:

1. Go to **IAM & Admin → Service Accounts**.
2. Click `airflow-gcs-service-account`.
3. Open the **Details** tab.
4. Copy the service-account email.

It will look similar to:

```text
airflow-gcs-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

The numeric value visible in your screenshot is a unique service-account ID. Airflow normally needs the Project ID and JSON key, not that numeric ID.

---

## Step 4: Grant Access Only to Your Bucket

For reading the CSV, the recommended minimum predefined role is:

```text
Storage Object Viewer
roles/storage.objectViewer
```

This role permits reading object data and listing objects. It can be assigned directly at bucket level, which is safer than granting access to every bucket in the project.

In the GCP Console:

1. Go to **Cloud Storage → Buckets**.
2. Click:

```text
azctsdemo1bucket
```

3. Open the **Permissions** tab.
4. Click **Grant access**.
5. Under **New principals**, enter the service-account email:

```text
airflow-gcs-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

6. Under **Select a role**, search for:

```text
Storage Object Viewer
```

7. Select:

```text
Cloud Storage → Storage Object Viewer
```

8. Click **Save**.

You do not need these broader roles:

```text
Owner
Editor
Storage Admin
Storage Object Admin
```

`Storage Object Viewer` is sufficient for listing and reading the CSV.

---

## Step 5: Obtain a JSON Key

Your screenshot shows that the service account already has an active key. However, Google does not allow the private JSON key to be downloaded again after its initial creation.

First, check your Windows **Downloads** folder for a file similar to:

```text
bigquery-optimization-lab-xxxxxx.json
```

Open it carefully in VS Code. A valid service-account JSON file contains fields similar to:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "airflow-gcs-service-account@your-project-id.iam.gserviceaccount.com",
  "client_id": "...",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

Do not paste this content into chat, GitHub, email, screenshots, or your DAG.

### If You Do Not Have the Original JSON

Create a new key:

1. Go to **IAM & Admin → Service Accounts**.
2. Click `airflow-gcs-service-account`.
3. Open **Keys**.
4. Click **Add key**.
5. Select **Create new key**.
6. Choose **JSON**.
7. Click **Create**.

The JSON file will download once.

After confirming the new key works, delete unused older keys to reduce risk.

---

# Part 2 — Prepare the Airflow Docker Project

Your current project is:

```text
C:\AirflowDockerSqlServer
```

You currently have:

```text
config
dags
logs
plugins
sql_bridge
.env
docker-compose.yaml
Dockerfile
requirements.txt
```

Create one additional folder named:

```text
gcp_credentials
```

Your project should become:

```text
C:\AirflowDockerSqlServer
│
├── config
├── dags
├── gcp_credentials
│   └── airflow-gcs-key.json
├── logs
├── plugins
├── sql_bridge
├── .env
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

---

## Step 6: Copy and Rename the JSON File

Copy the downloaded JSON key into:

```text
C:\AirflowDockerSqlServer\gcp_credentials
```

Rename it to:

```text
airflow-gcs-key.json
```

Final Windows path:

```text
C:\AirflowDockerSqlServer\gcp_credentials\airflow-gcs-key.json
```

---

## Step 7: Protect the Credentials Folder from Git

Create or update:

```text
C:\AirflowDockerSqlServer\.gitignore
```

Add:

```gitignore
logs/
__pycache__/
*.pyc

gcp_credentials/
*.json

.env
```

Do not copy the JSON key into the `dags` directory.

---

# Part 3 — Install the Google Provider in Airflow

Airflow communicates with GCP through:

```text
apache-airflow-providers-google
```

## Step 8: Update `requirements.txt`

Open:

```text
C:\AirflowDockerSqlServer\requirements.txt
```

Keep your existing packages and add:

```text
apache-airflow-providers-google
```

Example:

```text
apache-airflow-providers-microsoft-mssql
apache-airflow-providers-common-sql
apache-airflow-providers-google
pyodbc
pandas
```

---

## Step 9: Check the Dockerfile

Your `Dockerfile` should install `requirements.txt`:

```dockerfile
FROM apache/airflow:3.0.3

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
```

Retain the exact Airflow image version currently used by your project.

---

# Part 4 — Mount the JSON File Inside Airflow Containers

## Step 10: Update `docker-compose.yaml`

Add this volume to the shared Airflow configuration:

```yaml
- ${AIRFLOW_PROJ_DIR:-.}/gcp_credentials:/opt/airflow/gcp_credentials:ro
```

Example:

```yaml
volumes:
  - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
  - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
  - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
  - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
  - ${AIRFLOW_PROJ_DIR:-.}/gcp_credentials:/opt/airflow/gcp_credentials:ro
```

If there is no shared `x-airflow-common` section, add the volume to every Airflow service that parses or runs DAGs.

---

## Step 11: Rebuild and Restart Airflow

Open PowerShell in:

```text
C:\AirflowDockerSqlServer
```

Run:

```powershell
docker compose down
docker compose build --no-cache
docker compose up airflow-init
docker compose up -d
docker compose ps
```

Check logs:

```powershell
docker compose logs --tail=100 airflow-scheduler
```

---

## Step 12: Verify the Google Provider

```powershell
docker compose exec airflow-scheduler airflow providers list
```

Look for:

```text
apache-airflow-providers-google
```

Test the import:

```powershell
docker compose exec airflow-scheduler python -c "from airflow.providers.google.cloud.hooks.gcs import GCSHook; print('Google provider installed successfully')"
```

---

## Step 13: Verify the JSON Mount

```powershell
docker compose exec airflow-scheduler ls -l /opt/airflow/gcp_credentials
```

Expected:

```text
airflow-gcs-key.json
```

Check from Python:

```powershell
docker compose exec airflow-scheduler python -c "import os; print(os.path.exists('/opt/airflow/gcp_credentials/airflow-gcs-key.json'))"
```

Expected:

```text
True
```

---

# Part 5 — Create the GCP Connection in Airflow

## Step 14: Open Airflow

Open:

```text
http://localhost:8080
```

Go to:

```text
Admin → Connections
```

Click **Add Connection**.

---

## Step 15: Enter the Connection Values

| Field | Value |
|---|---|
| Connection Id | `google_cloud_default` |
| Connection Type | `Google Cloud` |
| Project Id | Your real GCP Project ID |
| Keyfile Path | `/opt/airflow/gcp_credentials/airflow-gcs-key.json` |
| Scopes | Leave blank |
| Keyfile JSON | Leave blank |
| Number of Retries | Optional, for example `3` |

Do not use the Windows path inside Airflow. Use the path inside the container:

```text
/opt/airflow/gcp_credentials/airflow-gcs-key.json
```

---

# Part 6 — Create the GCS DAG

Create:

```text
C:\AirflowDockerSqlServer\dags\gcs_read_customers_dag.py
```

```python
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime

from airflow.sdk import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook


BUCKET_NAME = "azctsdemo1bucket"
OBJECT_NAME = "input/customers.csv"
GCP_CONNECTION_ID = "google_cloud_default"


@dag(
    dag_id="gcs_read_customers",
    description="Read customers.csv from Google Cloud Storage",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=["gcp", "gcs", "csv"],
)
def gcs_read_customers_dag():

    @task
    def check_and_list_objects() -> list[str]:
        hook = GCSHook(gcp_conn_id=GCP_CONNECTION_ID)

        objects = hook.list(
            bucket_name=BUCKET_NAME,
            prefix="input/",
        )

        if not objects:
            raise FileNotFoundError(
                f"No objects were found under gs://{BUCKET_NAME}/input/"
            )

        for object_name in objects:
            logging.info("gs://%s/%s", BUCKET_NAME, object_name)

        return objects

    @task
    def read_customers_csv(objects: list[str]) -> dict:
        if OBJECT_NAME not in objects:
            raise FileNotFoundError(
                f"Expected object gs://{BUCKET_NAME}/{OBJECT_NAME} was not found."
            )

        hook = GCSHook(gcp_conn_id=GCP_CONNECTION_ID)

        file_bytes = hook.download(
            bucket_name=BUCKET_NAME,
            object_name=OBJECT_NAME,
        )

        csv_text = file_bytes.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(csv_text))
        records = list(reader)

        if not records:
            raise ValueError("The CSV exists, but it contains no data records.")

        logging.info("CSV columns: %s", reader.fieldnames)
        logging.info("Total customer records: %s", len(records))

        for row_number, record in enumerate(records[:10], start=1):
            logging.info("Record %s: %s", row_number, record)

        return {
            "bucket": BUCKET_NAME,
            "object": OBJECT_NAME,
            "record_count": len(records),
            "columns": reader.fieldnames or [],
            "preview": records[:5],
        }

    @task
    def print_summary(summary: dict) -> None:
        logging.info("GCS read completed successfully.")
        logging.info(
            "Source: gs://%s/%s",
            summary["bucket"],
            summary["object"],
        )
        logging.info("Record count: %s", summary["record_count"])
        logging.info("Columns: %s", summary["columns"])
        logging.info("First five records: %s", summary["preview"])

    object_list = check_and_list_objects()
    result = read_customers_csv(object_list)
    print_summary(result)


gcs_read_customers_dag()
```

For older Airflow versions, replace:

```python
from airflow.sdk import dag, task
```

with:

```python
from airflow.decorators import dag, task
```

---

# Part 7 — Trigger the DAG

## Step 17: Confirm the DAG Is Detected

Search for:

```text
gcs_read_customers
```

Check import errors if necessary:

```powershell
docker compose exec airflow-scheduler airflow dags list-import-errors
```

---

## Step 18: Trigger It

1. Open `gcs_read_customers`.
2. Enable or unpause it.
3. Click **Trigger DAG**.
4. Open the DAG run.

Task order:

```text
check_and_list_objects
          ↓
read_customers_csv
          ↓
print_summary
```

---

## Step 19: View the Records

Open the log for:

```text
read_customers_csv
```

Expected output:

```text
CSV columns: [...]
Total customer records: 100
Record 1: {...}
Record 2: {...}
```

---

# Connection-Only Test

```powershell
docker compose exec airflow-scheduler python -c "from airflow.providers.google.cloud.hooks.gcs import GCSHook; h=GCSHook(gcp_conn_id='google_cloud_default'); print(h.list(bucket_name='azctsdemo1bucket', prefix='input/'))"
```

Expected:

```text
['input/customers.csv']
```

---

# Common Errors

## `403 Forbidden`

Grant the service account:

```text
Storage Object Viewer
```

on:

```text
azctsdemo1bucket
```

## `404 Not Found`

Confirm the exact case-sensitive object path:

```text
input/customers.csv
```

## Key File Missing

```powershell
docker compose exec airflow-scheduler ls -l /opt/airflow/gcp_credentials
```

## Google Provider Missing

```text
apache-airflow-providers-google
```

Then rebuild the image.

## Invalid JWT Signature

Check that:

- The JSON key is active.
- The mounted file is correct.
- Windows date and time are synchronized.
- The Airflow connection points to the correct file.

---

# Final Checklist

```text
[ ] Cloud Storage API enabled
[ ] Service-account email copied
[ ] Storage Object Viewer assigned at bucket level
[ ] JSON key downloaded
[ ] Key copied to gcp_credentials/airflow-gcs-key.json
[ ] Credentials folder added to .gitignore
[ ] Google Airflow provider added
[ ] Docker image rebuilt
[ ] Credentials folder mounted read-only
[ ] google_cloud_default connection created
[ ] gcs_read_customers_dag.py created
[ ] DAG triggered
[ ] Customer records visible in task logs
```
