import os
from google.cloud import pubsub_v1

credentials_path = os.path.join(
    os.path.dirname(__file__),
    "credentials",
    "bigquery-optimization-lab-03e672767b37.json"
)

if not os.path.exists(credentials_path):
    raise FileNotFoundError(
        f"Credentials file was not found: {credentials_path}"
    )

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

publisher = pubsub_v1.PublisherClient()

print("Publisher client created successfully")