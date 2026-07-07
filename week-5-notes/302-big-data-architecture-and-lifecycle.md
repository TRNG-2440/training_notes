# Big Data Architecture and the Data Lifecycle

## Learning Objectives
- Trace the reference big-data flow: ingestion → storage → processing → serving.
- Distinguish batch from stream processing and know when each fits.
- Explain Lambda, Kappa, and modern Lakehouse / Medallion patterns at a high level.
- Walk data through its lifecycle stages, from creation to destruction.
- Connect storage tiers and lifecycle policies to cost control.

## Why This Matters
`301` gave you the *layers* of a big-data system. This note gives you the *flow* through those layers and the *timeline* of a single piece of data. Architecture decisions here — batch vs stream, where the serving layer lives, when data moves to cold storage — determine your system's latency, cost, and how much of your life you spend maintaining it. When you load a table into BigQuery on Day 4 and build an ETL pipeline on Day 5, you are implementing a slice of exactly these patterns.

## Concept Explanation

### The Reference Data Flow
Nearly every big-data platform, regardless of vendor, is some arrangement of four stages:

```
  SOURCES        INGESTION         STORAGE          PROCESSING        SERVING
 (apps, DBs,   (batch loads,   (data lake +     (batch + stream    (warehouse,
  logs, IoT,    streaming,      warehouse +      transforms,        BI, APIs,
  partners)     CDC)            operational DB)   ETL/ELT)           ML models)
     |              |                |                 |                 |
     +----> ingest ---> land raw ------> transform ------> aggregate ------> serve
```

- **Ingestion** — how data enters: scheduled batch loads (files, DB extracts), streaming (Kafka, Pub/Sub, Kinesis), or Change Data Capture (CDC) that replicates DB changes as they happen.
- **Storage** — where it lives: a **data lake** (raw, any format, cheap object storage), a **data warehouse** (cleaned, structured, query-optimized), and **operational databases** (live transactional data). See table below.
- **Processing** — where it gets useful: batch or stream transforms, ETL/ELT (Day 5).
- **Serving** — where consumers read: the warehouse for BI/SQL, feature stores for ML, APIs (the FastAPI you built on Day 1) for applications.

| Storage type | Schema | Speed | Cost | Best for |
|--------------|--------|-------|------|----------|
| Data lake | Flexible (schema-on-read) | Variable | Low | Raw data, ML, cheap retention |
| Data warehouse | Fixed (schema-on-write) | Fast | Medium | Analytics, BI, SQL |
| RDBMS (operational) | Fixed | Fast | Higher | Transactions (OLTP) |
| NoSQL | Flexible | Fast | Medium | High-scale application data |

### Batch vs Stream Processing
The single biggest architectural fork. Batch answers Volume; streaming answers Velocity.

| Aspect | Batch | Stream |
|--------|-------|--------|
| Data boundary | Bounded (finite chunk) | Unbounded (never-ending) |
| Latency | Minutes to hours | Milliseconds to seconds |
| Throughput | Very high | High |
| Completeness | Complete data | Partial / windowed |
| Complexity | Lower | Higher |
| Typical use | Nightly reports, ML training | Alerts, live dashboards, fraud |

Most real systems do **both**: nightly batch jobs for accurate history, plus a streaming path for "right now." That combination is what the next patterns formalize.

### Architecture Patterns

**Lambda architecture** — run batch and stream *in parallel*, then merge.
```
                +--------+
                | Source |
                +---+----+
          +---------+---------+
          v                   v
    +-----------+       +-----------+
    |  Batch    |       |  Speed    |
    |  layer    |       |  layer    |
    +-----+-----+       +-----+-----+
          |                   |
          +---------+---------+
                    v
              +-----------+
              |  Serving  |  <- query merges complete (batch)
              |  layer    |     + fresh (speed) views
              +-----------+
```
- Batch layer: reprocesses all history into accurate, complete views.
- Speed layer: handles just-arrived data for low latency.
- Serving layer: merges the two for queries.
- Trade-off: powerful and fault-tolerant, but you maintain **two codebases** doing the same logic.

**Kappa architecture** — treat *everything* as a stream; history is just old events replayed. One codebase, simpler to reason about, but requires robust streaming infrastructure and event retention. Reprocessing means replaying the stream.

**Modern hybrids** you will hear about constantly:
- **Lakehouse** (Delta Lake, Apache Iceberg): one storage layer with data-lake flexibility *and* warehouse-style ACID transactions. Removes the lake-vs-warehouse split.
- **Medallion**: organize data by quality tier as it flows through the platform.
```
Source --> Bronze --> Silver --> Gold --> Analytics / ML
          (raw)     (cleaned)  (business
                              aggregates)
```
Bronze = raw ingested, Silver = cleaned & conformed, Gold = aggregated business-level. This maps almost one-to-one onto the ETL you build on Day 5.

**Choosing a pattern:**

| Requirement | Reasonable choice |
|-------------|-------------------|
| Batch only | Simple scheduled ETL |
| Real-time only | Kappa (streaming) |
| Both, moderate complexity | Lambda |
| Both, evolving, want ACID | Lakehouse + Medallion |
| Strong consistency, structured | Data warehouse |

### The Data Lifecycle
A single record has a life. Managing that life well is how you stay compliant and control cost.

```
Create -> Ingest -> Store -> Process -> Analyze -> Archive -> Destroy
```

| Stage | What happens | Key concern |
|-------|--------------|-------------|
| **Create / collect** | Data originates (sensors, users, APIs, derived) | Ownership, quality at source, consent |
| **Ingest** | Data enters your systems (batch/stream/CDC) | Validate early, handle errors, preserve order |
| **Store** | Persisted for later use | Right storage tier, redundancy, access control |
| **Process** | Cleaned, standardized, enriched, joined | Correctness, reproducibility (ETL vs ELT) |
| **Analyze / consume** | BI, ML, reports, APIs read it | Discoverability, lineage, query cost |
| **Archive** | Rarely-accessed data moved to cheap tiers | Retrieval time vs storage cost |
| **Destroy** | Permanently deleted after retention | Legal holds, GDPR erasure, audit log |

### Storage Tiers and Lifecycle Automation
Not all data deserves fast, expensive storage forever. Access frequency drops with age, so cost should too:

```
Age 0-30d    Hot      frequent access     $$$$
Age 30-90d   Warm/Nearline               $$$
Age 90-365d  Cold/Coldline               $$
Age 1yr+     Archive  rare access         $
After retention -> Delete
```

Cloud providers automate these transitions with **lifecycle policies** so you do not move objects by hand:

```python
# GCS lifecycle: auto-tier by age, then delete. Declarative — the provider enforces it.
gcs_lifecycle = {
    "lifecycle": {"rule": [
        {"action": {"type": "SetStorageClass", "storageClass": "NEARLINE"}, "condition": {"age": 30}},
        {"action": {"type": "SetStorageClass", "storageClass": "COLDLINE"}, "condition": {"age": 90}},
        {"action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},  "condition": {"age": 365}},
        {"action": {"type": "Delete"},                                       "condition": {"age": 2555}},  # ~7 yrs
    ]}
}
```
The equivalent on AWS is an S3 Lifecycle configuration (Standard → Standard-IA → Glacier → delete); on Azure it is Blob lifecycle management (Hot → Cool → Cold → Archive). Same idea, different names — see `305-cloud-data-services-aws-azure-gcp`.

## Code Example
Batch and stream are two *shapes* of the same aggregation. This tiny example shows the structural difference — batch closes over a complete set; streaming updates running state per event.

```python
from datetime import datetime

# BATCH: given a complete day, compute one final summary.
def batch_daily_summary(sales: list[dict]) -> dict:
    return {
        "date": sales[0]["ts"][:10],
        "revenue": sum(s["amount"] for s in sales),
        "orders": len(sales),
        "customers": len({s["customer_id"] for s in sales}),
        "computed_at": datetime.now().isoformat(),
    }

# STREAM: update running totals as each event arrives; emit continuously.
class StreamAggregator:
    def __init__(self):
        self.state: dict[str, dict] = {}

    def on_event(self, event: dict) -> dict:
        day = event["ts"][:10]
        bucket = self.state.setdefault(day, {"revenue": 0, "orders": 0, "customers": set()})
        bucket["revenue"] += event["amount"]
        bucket["orders"] += 1
        bucket["customers"].add(event["customer_id"])
        # a real system pushes this to a live dashboard / warehouse
        return {"date": day, "revenue": bucket["revenue"], "orders": bucket["orders"]}

# Batch = accuracy over a bounded window. Stream = freshness over an unbounded one.
```

## Key Takeaways
- Every big-data platform is a variation on ingestion → storage → processing → serving.
- Storage splits into data lake (raw, cheap, flexible), warehouse (clean, fast, structured), and operational DBs (live transactions).
- Batch gives completeness and high throughput; streaming gives low latency. Most systems run both.
- Lambda runs batch + stream in parallel (two codebases); Kappa unifies on streaming (one codebase).
- Lakehouse and Medallion (Bronze/Silver/Gold) are today's default hybrids and map directly onto ETL/ELT design.
- Data has a lifecycle from creation to destruction; each stage has distinct concerns.
- Lifecycle policies auto-tier data by age (hot → warm → cold → archive → delete) and are a primary cost-control lever.

## Resources
- Questioning the Lambda Architecture (Kappa): <https://www.oreilly.com/radar/questioning-the-lambda-architecture/>
- Delta Lake (Lakehouse): <https://delta.io/>
- Apache Iceberg: <https://iceberg.apache.org/>
- GCP storage classes: <https://cloud.google.com/storage/docs/storage-classes>
- AWS S3 lifecycle: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html>
- Sibling notes: `301-big-data-fundamentals`, `303-big-data-benefits-and-challenges`, `305-cloud-data-services-aws-azure-gcp`
