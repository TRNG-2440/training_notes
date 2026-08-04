from pathlib import Path
import json
import os
import time

import requests
from google.cloud import pubsub_v1


PROJECT_ID = "bigquery-optimization-lab"
TOPIC_ID = "demo-topic"

# Find the credentials folder relative to publisher.py.
SCRIPT_DIRECTORY = Path(__file__).resolve().parent

CREDENTIALS_PATH = (
    SCRIPT_DIRECTORY
    / "credentials"
    / "bigquery-optimization-lab-03e672767b37.json"
)

# Stop with a clear message when the file is missing.
if not CREDENTIALS_PATH.is_file():
    raise FileNotFoundError(
        "Service-account JSON file was not found.\n"
        f"Expected location: {CREDENTIALS_PATH}\n"
        "Copy the JSON file into the credentials folder or correct the filename."
    )

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)

publisher = pubsub_v1.PublisherClient()

# Build the official topic resource path.
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

API_URL = "https://official-joke-api.appspot.com/random_joke"


def get_activity() -> dict:
    """Retrieve one activity from the external API."""

    response = requests.get(
        API_URL,
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def publish_activity(activity: dict) -> None:
    """Publish one JSON message and wait for confirmation."""

    message_data = json.dumps(activity).encode("utf-8")

    publish_future = publisher.publish(
        topic_path,
        data=message_data,
        source="bored-api",
        message_type="activity",
    )

    # Waiting for result exposes authentication, topic and IAM errors.
    message_id = publish_future.result(timeout=30)

    print(f"Published message ID: {message_id}")
    print(f"Activity: {activity}")


def main() -> None:
    print(f"Credentials: {CREDENTIALS_PATH}")
    print(f"Topic: {topic_path}")
    print("Publisher started. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                activity = get_activity()
                publish_activity(activity)
            except requests.RequestException as error:
                print(f"External API error: {error}")
            except Exception as error:
                print(f"Publishing error: {type(error).__name__}: {error}")

            time.sleep(20)

    except KeyboardInterrupt:
        print("\nPublisher stopped.")


if __name__ == "__main__":
    main()