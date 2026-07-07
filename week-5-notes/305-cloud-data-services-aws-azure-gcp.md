# Cloud Data Services: AWS vs Azure vs GCP

## Learning Objectives
- Map the key data services across AWS, Azure, and GCP by category.
- Match a data need (object storage, warehouse, streaming, managed RDBMS, batch ETL) to the right service on each provider.
- Summarize each provider's strengths for data workloads.
- Understand where BigQuery sits in the landscape — setting up Day 4.
- Use service-equivalency tables to work fluently regardless of provider.

## Why This Matters
Clients and employers standardize on different clouds, and you will move between them. The good news: the *categories* are the same everywhere — every provider has object storage, a data warehouse, a streaming service, managed databases, and batch processing. Learn the categories once and you only have to translate names. This note is your translation table, and it ends by placing **BigQuery**, the warehouse you use hands-on for the rest of the week.

## Concept Explanation

### The Big Picture
Three hyperscalers dominate: **AWS** (largest, broadest catalog), **Azure** (strong in enterprise / Microsoft shops), **GCP** (analytics- and ML-first, home of BigQuery). For any data need, ask "which category?" then look up the provider's name for it.

```
              AWS              Azure                GCP
Object store  S3               Blob Storage         Cloud Storage
Warehouse     Redshift         Synapse Analytics    BigQuery
Streaming     Kinesis          Event Hubs /         Pub/Sub
                               Stream Analytics
Batch/ETL     Glue / EMR       Data Factory         Dataflow / Dataproc
Managed RDBMS RDS / Aurora     Azure SQL / DB       Cloud SQL
Compute (VM)  EC2              Virtual Machines     Compute Engine
```

### Service-Equivalency Tables

**Compute & object storage** — the foundation.

| Category | AWS | Azure | GCP |
|----------|-----|-------|-----|
| Virtual machines (IaaS) | EC2 | Virtual Machines | Compute Engine |
| Object storage | S3 | Blob Storage | Cloud Storage |
| Data lake | S3 + Lake Formation | Data Lake Storage Gen2 | Cloud Storage + Dataplex |
| Archive tier | S3 Glacier / Deep Archive | Archive tier | Archive class |
| Block storage | EBS | Managed Disks | Persistent Disk |

**Data warehouse** — the analytics engine (deep dive on BigQuery is Day 4).

| Feature | AWS Redshift | Azure Synapse | GCP BigQuery |
|---------|--------------|---------------|--------------|
| Architecture | Cluster-based (RA3 separates compute/storage) | Dedicated or serverless SQL pools | Fully serverless |
| Scaling | Resize / concurrency scaling | Pause & scale pools | Automatic, invisible |
| Pricing | Per-node (or serverless) | Per-DWU or per-query | Per-TB scanned or slots |
| Query external data | Redshift Spectrum (on S3) | Serverless SQL pool | Federated queries |
| Ops burden | Manage cluster | Manage pools | None (serverless) |

**Streaming & batch processing** — moving and transforming data.

| Category | AWS | Azure | GCP |
|----------|-----|-------|-----|
| Streaming ingestion | Kinesis Data Streams | Event Hubs | Pub/Sub |
| Stream processing | Kinesis Data Analytics | Stream Analytics | Dataflow (streaming) |
| Batch ETL | Glue | Data Factory | Dataflow / Dataproc |
| Managed Spark/Hadoop | EMR | HDInsight / Databricks | Dataproc |
| Orchestration | Step Functions / MWAA (Airflow) | Data Factory | Cloud Composer (Airflow) |
| Serverless functions | Lambda | Functions | Cloud Functions |

**Managed databases** — operational stores.

| Type | AWS | Azure | GCP |
|------|-----|-------|-----|
| Managed PostgreSQL | RDS / Aurora PostgreSQL | Azure Database for PostgreSQL | Cloud SQL |
| Managed MySQL | RDS / Aurora MySQL | Azure Database for MySQL | Cloud SQL |
| Document / NoSQL | DynamoDB, DocumentDB | Cosmos DB | Firestore |
| Wide-column / key-value | DynamoDB, Keyspaces | Cosmos DB (Cassandra API) | Bigtable |
| Globally-distributed SQL | Aurora Global / DynamoDB Global | Cosmos DB | Cloud Spanner |
| Governance / catalog | Glue Data Catalog, Lake Formation | Microsoft Purview | Dataplex / Data Catalog |

### Provider Strengths at a Glance
| Provider | Data strengths | Best fit |
|----------|----------------|----------|
| **AWS** | Widest catalog, S3 is the de-facto data-lake standard, mature ecosystem | Broadest needs, existing AWS estate, custom architectures |
| **Azure** | Deep Microsoft integration (Power BI, SQL Server, M365), Synapse unified workspace, Purview governance | Microsoft-centric enterprises, hybrid, SQL Server migrations |
| **GCP** | Best-in-class analytics/ML, BigQuery simplicity & performance, competitive pricing, open-source lean | Analytics-heavy, data-first orgs, ML/AI, cost focus |

### Where BigQuery Fits — bridge to Day 4
BigQuery is GCP's **serverless data warehouse** and the tool you use hands-on for the rest of the week. Its defining traits:
- **Serverless** — no cluster to size or manage (contrast Redshift's nodes). This is the PaaS/serverless model from `304`.
- **Separation of storage and compute** — they scale independently; you pay for storage and for queries separately.
- **Standard SQL** — the SQL you already know, plus analytics extensions and built-in ML (BigQuery ML).
- **Pay-per-query** — on-demand is ~$5/TB scanned, which makes query efficiency (partitioning, clustering, selecting only needed columns) a *cost* concern, not just a speed one — a Day 4 theme.
- **Free sandbox** — 10 GB storage + 1 TB queries/month with no billing card, so everyone can practice (see the week `README.md`).

Its cross-cloud equivalents are Redshift (AWS) and Synapse dedicated/serverless pools (Azure) — same job, different operational model.

### Choosing — a quick heuristic
```
Already on a cloud?          -> stay there unless a service gap forces otherwise
Microsoft-heavy shop?        -> Azure
Analytics/ML is the point?   -> GCP (BigQuery)
Need the widest service set? -> AWS
Regulatory / avoid lock-in?  -> multi-cloud (accept the complexity)
```

## Code Example
Because the *categories* are identical, a thin abstraction lets one program target any provider's object storage. This is the practical payoff of learning categories over names.

```python
from abc import ABC, abstractmethod

class ObjectStore(ABC):
    @abstractmethod
    def upload(self, data: bytes, path: str) -> str: ...

class GCSStore(ObjectStore):
    def __init__(self, bucket: str):
        from google.cloud import storage
        self.bucket = storage.Client().bucket(bucket)
    def upload(self, data, path):
        self.bucket.blob(path).upload_from_string(data)
        return f"gs://{self.bucket.name}/{path}"

class S3Store(ObjectStore):
    def __init__(self, bucket: str):
        import boto3
        self.s3, self.bucket = boto3.client("s3"), bucket
    def upload(self, data, path):
        self.s3.put_object(Bucket=self.bucket, Key=path, Body=data)
        return f"s3://{self.bucket}/{path}"

def make_store(provider: str, bucket: str) -> ObjectStore:
    return {"gcp": GCSStore, "aws": S3Store}[provider](bucket)

# Same call, any cloud — only the factory arg changes.
store = make_store("gcp", "my-data-bucket")
print(store.upload(b"hello,world\n", "raw/greet.csv"))
```

## Key Takeaways
- Every hyperscaler offers the same data-service *categories*; you mostly translate names.
- Object storage: S3 / Blob / Cloud Storage. Warehouse: Redshift / Synapse / BigQuery. Streaming: Kinesis / Event Hubs / Pub/Sub. Batch ETL: Glue / Data Factory / Dataflow. Managed RDBMS: RDS / Azure SQL / Cloud SQL.
- AWS = breadth, Azure = Microsoft integration, GCP = analytics/ML and BigQuery.
- BigQuery is a serverless, pay-per-query warehouse that separates storage and compute — the Day 4 focus.
- Learn categories, not just brand names, and you can work on any cloud.

## Resources
- BigQuery documentation: <https://cloud.google.com/bigquery/docs>
- BigQuery sandbox (free, no card): <https://cloud.google.com/bigquery/docs/sandbox>
- Google cross-cloud service comparison: <https://cloud.google.com/docs/compare>
- AWS data services: <https://aws.amazon.com/products/databases/> and <https://aws.amazon.com/big-data/datalakes-and-analytics/>
- Azure data services: <https://azure.microsoft.com/en-us/products/#analytics>
- Sibling notes: `304-cloud-computing-and-service-models`, and Day 4 BigQuery notes (`4xx`)
