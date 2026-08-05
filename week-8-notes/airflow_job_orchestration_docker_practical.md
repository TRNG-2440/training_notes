# Job Orchestration with Apache Airflow Using Docker

## Simple Step-by-Step Practical for Students

This practical builds the following workflow:

```text
Start
  ↓
Prepare environment
  ↓
Validate CSV file
  ↓
Transform student marks
  ↓
Create summary report
  ↓
Demonstrate automatic retry
  ↓
End
```

It demonstrates Docker-based Airflow setup, DAG creation, task dependencies, validation, transformation, XCom, retries, logs, monitoring, output generation, failure handling, and recovery.

---

## 1. Prerequisites

Install:

1. Docker Desktop
2. Docker Compose
3. Visual Studio Code or another editor
4. A web browser

Verify Docker from PowerShell:

```powershell
docker --version
docker compose version
```

---

## 2. Create the Project Folder

```powershell
cd C:\
mkdir AirflowDockerLab
cd AirflowDockerLab
```

Project path:

```text
C:\AirflowDockerLab
```

---

## 3. Download the Airflow Docker Compose File

```powershell
curl.exe -LfO "https://airflow.apache.org/docs/apache-airflow/3.3.0/docker-compose.yaml"
```

Verify:

```powershell
dir
```

You should see:

```text
docker-compose.yaml
```

---

## 4. Create Required Folders

```powershell
mkdir dags
mkdir logs
mkdir plugins
mkdir config
mkdir dags\data
mkdir dags\output
```

Expected structure:

```text
C:\AirflowDockerLab
│
├── docker-compose.yaml
├── dags
│   ├── data
│   └── output
├── logs
├── plugins
└── config
```

---

## 5. Create the `.env` File

```powershell
"AIRFLOW_UID=50000" | Set-Content .env
```

Verify:

```powershell
Get-Content .env
```

Expected:

```text
AIRFLOW_UID=50000
```

---

## 6. Create the Input CSV

Create:

```text
C:\AirflowDockerLab\dags\data\student_marks.csv
```

Open it:

```powershell
notepad .\dags\data\student_marks.csv
```

Paste:

```csv
student_id,student_name,maths,science,english
S001,Aarav,78,82,75
S002,Diya,91,88,93
S003,Vikram,35,42,38
S004,Meera,67,71,69
S005,Arjun,45,28,51
S006,Ishita,88,92,86
S007,Rahul,56,61,59
S008,Ananya,32,39,41
S009,Karthik,74,77,72
S010,Priya,95,94,96
```

Verify:

```powershell
Get-Content .\dags\data\student_marks.csv
```

---

## 7. Create the Airflow DAG

Create:

```text
C:\AirflowDockerLab\dags\student_result_orchestration.py
```

Open it:

```powershell
notepad .\dags\student_result_orchestration.py
```

Paste the following code:

```python
from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta

from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import DAG, task


DATA_DIRECTORY = "/opt/airflow/dags/data"
OUTPUT_DIRECTORY = "/opt/airflow/dags/output"

INPUT_FILE = f"{DATA_DIRECTORY}/student_marks.csv"
PROCESSED_FILE = f"{OUTPUT_DIRECTORY}/processed_student_results.csv"
SUMMARY_FILE = f"{OUTPUT_DIRECTORY}/student_result_summary.txt"
RETRY_MARKER_FILE = f"{OUTPUT_DIRECTORY}/retry_marker.txt"


default_args = {
    "owner": "airflow-student",
    "retries": 1,
    "retry_delay": timedelta(seconds=10),
}


with DAG(
    dag_id="student_result_job_orchestration",
    description="Simple job orchestration practical for students",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["training", "docker", "job-orchestration"],
) as dag:

    start = EmptyOperator(task_id="start")

    @task
    def prepare_environment() -> str:
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

        if os.path.exists(RETRY_MARKER_FILE):
            os.remove(RETRY_MARKER_FILE)
            print("Old retry marker removed.")

        print(f"Output directory is ready: {OUTPUT_DIRECTORY}")
        return OUTPUT_DIRECTORY

    @task
    def validate_input_file(output_directory: str) -> str:
        print(f"Checking input file: {INPUT_FILE}")
        print(f"Output directory: {output_directory}")

        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(
                f"Input file was not found: {INPUT_FILE}"
            )

        if os.path.getsize(INPUT_FILE) == 0:
            raise ValueError(f"Input file is empty: {INPUT_FILE}")

        required_columns = {
            "student_id",
            "student_name",
            "maths",
            "science",
            "english",
        }

        with open(INPUT_FILE, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            actual_columns = set(reader.fieldnames or [])

        missing_columns = required_columns - actual_columns

        if missing_columns:
            raise ValueError(
                f"Required columns are missing: {sorted(missing_columns)}"
            )

        print("Input file validation completed successfully.")
        return INPUT_FILE

    @task
    def transform_student_results(input_file: str) -> dict:
        processed_rows = []
        pass_count = 0
        fail_count = 0

        with open(input_file, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                maths = int(row["maths"])
                science = int(row["science"])
                english = int(row["english"])

                total = maths + science + english
                average = round(total / 3, 2)

                passed = (
                    maths >= 40
                    and science >= 40
                    and english >= 40
                )

                result = "PASS" if passed else "FAIL"

                if result == "PASS":
                    pass_count += 1
                else:
                    fail_count += 1

                if average >= 90:
                    grade = "A+"
                elif average >= 80:
                    grade = "A"
                elif average >= 70:
                    grade = "B"
                elif average >= 60:
                    grade = "C"
                elif average >= 50:
                    grade = "D"
                else:
                    grade = "F"

                processed_rows.append(
                    {
                        "student_id": row["student_id"],
                        "student_name": row["student_name"],
                        "maths": maths,
                        "science": science,
                        "english": english,
                        "total": total,
                        "average": average,
                        "grade": grade,
                        "result": result,
                    }
                )

        field_names = [
            "student_id",
            "student_name",
            "maths",
            "science",
            "english",
            "total",
            "average",
            "grade",
            "result",
        ]

        with open(PROCESSED_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(processed_rows)

        summary = {
            "total_students": len(processed_rows),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "processed_file": PROCESSED_FILE,
        }

        print("Student transformation completed.")
        print(f"Processed records: {len(processed_rows)}")
        return summary

    @task
    def create_summary_report(result_summary: dict) -> str:
        total_students = result_summary["total_students"]
        pass_count = result_summary["pass_count"]
        fail_count = result_summary["fail_count"]

        pass_percentage = (
            round((pass_count / total_students) * 100, 2)
            if total_students > 0
            else 0
        )

        report_lines = [
            "STUDENT RESULT PROCESSING SUMMARY",
            "=================================",
            f"Total students : {total_students}",
            f"Passed         : {pass_count}",
            f"Failed         : {fail_count}",
            f"Pass percentage: {pass_percentage}%",
            f"Processed file : {result_summary['processed_file']}",
            f"Generated at   : {datetime.now()}",
        ]

        report_content = "\n".join(report_lines)

        with open(SUMMARY_FILE, "w", encoding="utf-8") as file:
            file.write(report_content)

        print(report_content)
        return SUMMARY_FILE

    @task(
        retries=2,
        retry_delay=timedelta(seconds=10),
    )
    def demonstrate_retry(summary_file: str) -> str:
        print(f"Summary report received: {summary_file}")

        if not os.path.exists(RETRY_MARKER_FILE):
            with open(RETRY_MARKER_FILE, "w", encoding="utf-8") as file:
                file.write("The first attempt ran.")

            print("First attempt is intentionally failing.")
            raise ConnectionError(
                "Simulated temporary service failure"
            )

        print("Retry marker found.")
        print("Retry attempt completed successfully.")
        return "Retry demonstration completed"

    end = EmptyOperator(task_id="end")

    environment = prepare_environment()
    validated_file = validate_input_file(environment)
    result_summary = transform_student_results(validated_file)
    summary_report = create_summary_report(result_summary)
    retry_result = demonstrate_retry(summary_report)

    start >> environment
    retry_result >> end
```

---

## 8. Final Project Structure

```text
C:\AirflowDockerLab
│
├── .env
├── docker-compose.yaml
│
├── dags
│   ├── student_result_orchestration.py
│   ├── data
│   │   └── student_marks.csv
│   └── output
│
├── logs
├── plugins
└── config
```

Local folder:

```text
C:\AirflowDockerLab\dags
```

Container folder:

```text
/opt/airflow/dags
```

---

## 9. Initialize Airflow

Ensure Docker Desktop is running.

From `C:\AirflowDockerLab`, run:

```powershell
docker compose up airflow-init
```

Wait for:

```text
airflow-init-1 exited with code 0
```

Check:

```powershell
docker compose ps -a
```

---

## 10. Start Airflow

```powershell
docker compose up -d
```

Check services:

```powershell
docker compose ps
```

Expected services may include:

```text
airflow-api-server
airflow-dag-processor
airflow-scheduler
airflow-triggerer
airflow-worker
postgres
redis
```

---

## 11. Open the Airflow UI

Open:

```text
http://localhost:8080
```

Login:

```text
Username: airflow
Password: airflow
```

---

## 12. Find the DAG

Search for:

```text
student_result_job_orchestration
```

Expected flow:

```text
start
  ↓
prepare_environment
  ↓
validate_input_file
  ↓
transform_student_results
  ↓
create_summary_report
  ↓
demonstrate_retry
  ↓
end
```

---

## 13. Check DAG Import Errors

If the DAG is not visible:

```powershell
docker compose exec airflow-worker airflow dags list-import-errors
```

List DAGs:

```powershell
docker compose exec airflow-worker airflow dags list
```

Validate the Python file:

```powershell
docker compose exec airflow-worker python /opt/airflow/dags/student_result_orchestration.py
```

---

## 14. Trigger the DAG

In the Airflow UI:

1. Open `student_result_job_orchestration`.
2. Click the trigger button.
3. Confirm.
4. Open Grid or Graph view.

---

## 15. Observe the Retry Demonstration

The `demonstrate_retry` task intentionally fails once.

First attempt:

```text
ConnectionError: Simulated temporary service failure
```

Task state:

```text
up_for_retry
```

After about ten seconds, Airflow retries it.

Expected retry log:

```text
Retry marker found.
Retry attempt completed successfully.
```

Final state:

```text
success
```

---

## 16. Check Generated Output

Open:

```text
C:\AirflowDockerLab\dags\output
```

Expected files:

```text
processed_student_results.csv
student_result_summary.txt
retry_marker.txt
```

View processed output:

```powershell
Get-Content .\dags\output\processed_student_results.csv
```

View summary:

```powershell
Get-Content .\dags\output\student_result_summary.txt
```

Expected summary:

```text
STUDENT RESULT PROCESSING SUMMARY
=================================
Total students : 10
Passed         : 7
Failed         : 3
Pass percentage: 70.0%
```

---

## 17. View Task Logs

In the UI:

```text
DAG
→ Grid view
→ Select task
→ Logs
```

Important tasks:

- `validate_input_file`
- `transform_student_results`
- `create_summary_report`
- `demonstrate_retry`

---

## 18. XCom in This Example

TaskFlow automatically passes return values between tasks.

Examples:

```python
return INPUT_FILE
```

and:

```python
return {
    "total_students": 10,
    "pass_count": 7,
    "fail_count": 3,
    "processed_file": "...",
}
```

Use XCom for small values only:

- File paths
- Counts
- IDs
- Dates
- Status values
- Small dictionaries

Store large datasets externally and pass only their location.

---

## 19. Deliberate Input Failure Test

Rename the input file:

```powershell
Rename-Item `
  .\dags\data\student_marks.csv `
  student_marks_backup.csv
```

Trigger the DAG again.

Expected states:

```text
prepare_environment          success
validate_input_file          failed
transform_student_results    upstream_failed
create_summary_report        upstream_failed
demonstrate_retry            upstream_failed
end                          upstream_failed
```

Expected error:

```text
FileNotFoundError:
Input file was not found:
/opt/airflow/dags/data/student_marks.csv
```

---

## 20. Fix and Rerun

Restore the file:

```powershell
Rename-Item `
  .\dags\data\student_marks_backup.csv `
  student_marks.csv
```

In the UI:

1. Open the failed DAG Run.
2. Select `validate_input_file`.
3. Choose **Clear task**.
4. Include downstream tasks when required.
5. Confirm.

---

## 21. Trigger from PowerShell

List DAGs:

```powershell
docker compose exec airflow-worker airflow dags list
```

Trigger:

```powershell
docker compose exec airflow-worker `
  airflow dags trigger student_result_job_orchestration
```

List runs:

```powershell
docker compose exec airflow-worker `
  airflow dags list-runs `
  -d student_result_job_orchestration
```

---

## 22. Change the Schedule

Manual only:

```python
schedule=None
```

Daily at 9:00 AM:

```python
schedule="0 9 * * *"
```

Every day at midnight:

```python
schedule="@daily"
```

Every five minutes:

```python
schedule="*/5 * * * *"
```

Keep:

```python
catchup=False
```

---

## 23. View Container Logs

```powershell
docker compose logs
```

Follow all logs:

```powershell
docker compose logs -f
```

Scheduler logs:

```powershell
docker compose logs -f airflow-scheduler
```

Worker logs:

```powershell
docker compose logs -f airflow-worker
```

Stop following with `Ctrl+C`.

---

## 24. Stop and Restart Airflow

Stop:

```powershell
docker compose stop
```

Start again:

```powershell
docker compose start
```

Or:

```powershell
docker compose up -d
```

---

## 25. Remove the Environment

Remove containers:

```powershell
docker compose down
```

Completely reset:

```powershell
docker compose down --volumes --remove-orphans
```

This removes run history, connections, variables, and XCom metadata stored in the Airflow database.

---

## 26. Common Errors

### Port 8080 Is Already Used

```powershell
netstat -ano | findstr :8080
```

Change the port mapping in `docker-compose.yaml`:

```yaml
ports:
  - "8081:8080"
```

Then open:

```text
http://localhost:8081
```

### DAG Is Not Visible

```powershell
docker compose exec airflow-worker airflow dags list-import-errors
```

Check the filename:

```powershell
Get-ChildItem .\dags | Select-Object Name
```

Correct:

```text
student_result_orchestration.py
```

Incorrect:

```text
student_result_orchestration.py.txt
```

### Output Files Are Missing

```powershell
docker compose exec airflow-worker `
  ls -la /opt/airflow/dags/output
```

Also check:

```powershell
dir .\dags\output
```

---

## 27. What Students Learn

| Concept | Demonstrated By |
|---|---|
| DAG | `student_result_job_orchestration` |
| Task | Each decorated function |
| Dependency | Passing task outputs |
| Validation | `validate_input_file` |
| Transformation | `transform_student_results` |
| XCom | File paths and summary dictionary |
| Retry | `demonstrate_retry` |
| Failure handling | Missing-file test |
| Recovery | Clear and rerun |
| Scheduling | `schedule` property |
| Docker volume | Local DAG folder mapped into container |
| Monitoring | Grid, Graph and Logs |

---

## 28. Command Summary

Run from:

```text
C:\AirflowDockerLab
```

```powershell
# Verify Docker
docker --version
docker compose version

# Initialize Airflow
docker compose up airflow-init

# Start Airflow
docker compose up -d

# Check services
docker compose ps

# List DAGs
docker compose exec airflow-worker airflow dags list

# Check import errors
docker compose exec airflow-worker airflow dags list-import-errors

# Trigger the DAG
docker compose exec airflow-worker `
  airflow dags trigger student_result_job_orchestration

# View worker logs
docker compose logs -f airflow-worker

# Stop services
docker compose stop

# Start services
docker compose start

# Remove containers
docker compose down

# Complete reset
docker compose down --volumes --remove-orphans
```

---

## 29. Final Understanding

This practical demonstrates real job orchestration.

Airflow:

- Controls task order
- Stops downstream work after upstream failure
- Transfers small values between tasks
- Retries temporary failures automatically
- Stores task-level logs
- Displays execution status
- Allows failed tasks to be corrected and rerun
- Generates repeatable output files
