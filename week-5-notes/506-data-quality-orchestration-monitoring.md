# Data Quality, Orchestration & Monitoring

> Day 5 · Note 506 · refreshes W4 `c207` (data quality) + `c208` (orchestration) + `c209` (monitoring/logging) + `c210` (best practices)

## Learning Objectives

- Define the data-quality dimensions and write basic validation checks
- Explain orchestration concepts (DAG, task, dependency, schedule) and name the common tools
- Instrument a pipeline with structured logging and the right monitoring levels
- Apply ETL/ELT best practices: idempotency, atomicity, modularity, observability

## Why This Matters

A pipeline that moves data is only half the job. The other half is **trusting** the output and **operating** it in production — catching bad data before it reaches a dashboard, running the stages in the right order, and knowing when something broke. This note covers the operational discipline that separates a script from a pipeline. It's the last conceptual piece before the Day 5 capstone.

## Concept Explanation

### Data Quality Checks

Six dimensions to check every load against:

| Dimension | Question | Example check |
|-----------|----------|---------------|
| **Completeness** | Anything missing? | NULL count below threshold |
| **Accuracy** | Are values correct? | email matches a regex |
| **Consistency** | Do sources reconcile? | line-item totals = order total |
| **Timeliness** | Is data current? | max(load_time) within 24h |
| **Uniqueness** | Any duplicates? | distinct keys = row count |
| **Validity** | In allowed range/set? | status in ('A','I','P') |

```python
import pandas as pd

def validate(df: pd.DataFrame, key: str = "id") -> list[dict]:
    checks = []
    # Completeness
    for col, n in df.isnull().sum().items():
        if n:
            checks.append({"check": "completeness", "column": col,
                           "status": "fail" if n >= 10 else "warn",
                           "detail": f"{n} nulls"})
    # Uniqueness
    dups = df[key].duplicated().sum()
    if dups:
        checks.append({"check": "uniqueness", "column": key,
                       "status": "fail", "detail": f"{dups} duplicates"})
    # Validity (example)
    if "amount" in df and (df["amount"] < 0).any():
        checks.append({"check": "validity", "column": "amount",
                       "status": "fail", "detail": "negative amounts"})
    return checks

def gate(checks: list[dict]) -> None:
    """Fail the pipeline (don't publish) if any hard check failed."""
    if any(c["status"] == "fail" for c in checks):
        raise ValueError(f"Data quality gate failed: {checks}")
```

Put checks at two spots: **on landing** (source sanity) and **before publish** (mart correctness). A failing hard check should stop the pipeline, not silently publish bad numbers.

### Orchestration

Orchestration runs the tasks of a workflow in the right order, on a schedule, with retries.

```
DAG — Daily Sales Pipeline (a Directed Acyclic Graph of tasks):

  extract_orders    --> transform_orders    --+
  extract_products  --> transform_products   --+--> load_warehouse --> quality_gate --> send_report
  extract_customers --> transform_customers  --+
```

| Concept | Meaning |
|---------|---------|
| **DAG** | Directed Acyclic Graph of tasks (no cycles) |
| **Task** | One unit of work |
| **Dependency** | Task B runs only after Task A succeeds |
| **Schedule** | When the DAG runs (cron-like) |
| **Trigger** | What kicks it off (schedule, event, manual) |

Common tools (know the landscape; you are not expected to deploy one this week):

| Tool | Type | Best for |
|------|------|----------|
| **Apache Airflow** | Open-source | Complex, general workflows |
| Prefect / Dagster | Open-source | Python-native / data-asset-centric |
| **dbt** | Transform framework | SQL transformations + tests (ELT `T`) |
| Cloud Composer | GCP-managed Airflow | GCP ecosystem |
| **Dataflow** | GCP | Streaming/batch (Apache Beam) |

```python
# Airflow sketch — the shape, not a deployable DAG
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG("daily_sales", schedule="0 6 * * *",
         start_date=datetime(2025, 1, 1), catchup=False) as dag:
    extract   = PythonOperator(task_id="extract",   python_callable=do_extract)
    transform = PythonOperator(task_id="transform", python_callable=do_transform)
    load      = PythonOperator(task_id="load",      python_callable=do_load)
    quality   = PythonOperator(task_id="quality",   python_callable=do_quality_gate)
    extract >> transform >> load >> quality   # dependency chain
```

### Monitoring & Logging

Monitor at four levels:

| Level | Watch |
|-------|-------|
| Infrastructure | CPU, memory, disk |
| Pipeline | run status, duration, retries |
| Data | row counts, quality results, freshness |
| Business | SLA compliance |

Prefer **structured (JSON) logs** — they're queryable, unlike free-text prints.

```python
import json, logging
from datetime import datetime, timezone

class PipelineLogger:
    def __init__(self, pipeline: str):
        self.pipeline = pipeline
        self.log = logging.getLogger(pipeline)

    def event(self, event: str, **ctx):
        self.log.info(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "pipeline": self.pipeline, "event": event, **ctx}))

log = PipelineLogger("daily_sales")
log.event("task_start", task="extract")
log.event("task_complete", task="extract", rows=10_432, seconds=4.1)
```

### ETL/ELT Best Practices

| Principle | Meaning |
|-----------|---------|
| **Idempotency** | Re-running yields the same result (delete-then-insert a partition; merge on key) |
| **Atomicity** | All-or-nothing — a failed run leaves no half-written state (use transactions) |
| **Modularity** | Small, focused, independently-retryable tasks |
| **Observability** | Structured logs + metrics + row counts for every run |
| **Documentation** | Grain, sources, schedule, owners kept current |

```python
def idempotent_load(con, df, partition_date):
    """Safe to re-run: clear the partition, then insert."""
    con.execute("BEGIN")                                # atomicity
    con.execute("DELETE FROM fact_sales WHERE date_key = ?", [partition_date])
    con.register("stg", df)
    con.execute("INSERT INTO fact_sales SELECT * FROM stg")
    con.execute("COMMIT")

def robust(func):
    """Retry-friendly error handling for a task."""
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except Exception as e:
            log.event("task_error", task=func.__name__, error=str(e))
            raise           # let the orchestrator retry / alert
    return wrapper
```

## Code Example

Quality gate + logging wired into a load (the pattern the capstone uses):

```python
log = PipelineLogger("capstone_etl")

checks = validate(df, key="order_id")
log.event("quality_checked", results=checks)
gate(checks)                       # raises -> pipeline stops before publish

idempotent_load(con, df, partition_date=20250115)
log.event("load_complete", rows=len(df), partition=20250115)
```

## Key Takeaways

- Validate against six dimensions (completeness, accuracy, consistency, timeliness, uniqueness, validity) and **gate** on hard failures.
- Orchestration = tasks as a **DAG** with dependencies + schedule; Airflow/dbt/Dataflow are the tools to name.
- Use **structured (JSON) logging**; monitor at infra / pipeline / data / business levels.
- Build for **idempotency, atomicity, modularity, observability** — re-runs must be safe.

## Resources

- Airflow: <https://airflow.apache.org/> · dbt: <https://www.getdbt.com/> · Dataflow: <https://cloud.google.com/dataflow>
- Great Expectations (data QA): <https://greatexpectations.io/>
- Applied in: `exercises/502-capstone-etl-pipeline.md` and `demos/502-mini-etl-pipeline/`.
