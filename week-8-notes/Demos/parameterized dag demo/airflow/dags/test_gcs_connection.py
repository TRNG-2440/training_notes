from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook


BUCKET_NAME = "azctsdemo1bucket"
OBJECT_NAME = "input/customers.csv"
CONNECTION_ID = "google_cloud_default"


def test_gcs_connection() -> None:
    hook = GCSHook(gcp_conn_id=CONNECTION_ID)

    print(f"Checking bucket: {BUCKET_NAME}")
    print(f"Checking object: {OBJECT_NAME}")

    exists = hook.exists(
        bucket_name=BUCKET_NAME,
        object_name=OBJECT_NAME,
    )

    if not exists:
        print(
            f"Connection succeeded, but the object was not found: "
            f"gs://{BUCKET_NAME}/{OBJECT_NAME}"
        )

        objects = hook.list(bucket_name=BUCKET_NAME)

        print("Available objects:")

        if not objects:
            print("The bucket is empty.")
        else:
            for object_name in objects:
                print(object_name)

        return

    content = hook.download(
        bucket_name=BUCKET_NAME,
        object_name=OBJECT_NAME,
    )

    text = content.decode("utf-8")

    print("GCS connection successful")
    print(f"Object found: gs://{BUCKET_NAME}/{OBJECT_NAME}")
    print("First 1000 characters:")
    print(text[:1000])


with DAG(
    dag_id="test_gcs_connection",
    description="Test Google Cloud Storage connection from Airflow",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["gcp", "gcs"],
) as dag:

    test_connection = PythonOperator(
        task_id="test_gcs_connection",
        python_callable=test_gcs_connection,
    )