# Big Data Fundamentals

## Learning Objectives
- Define what makes data "Big Data" and why the label is about capability, not just size.
- Explain the 5 V's — Volume, Velocity, Variety, Veracity, Value — with concrete examples.
- Describe why a single-machine RDBMS approach breaks down at scale.
- Name the main building blocks of a big-data system (storage, processing, analytics).
- Recognize real-world big-data use cases across industries.

## Why This Matters
For most of this week you have moved data through APIs and pandas on one machine. That works right up until it does not: the file no longer fits in RAM, the query that took seconds now takes hours, or data arrives faster than you can load it. **Big Data** is the name for the moment your familiar tools stop scaling — and for the technologies (distributed storage, distributed compute, cloud warehouses like the BigQuery you meet on Day 4) built to push past that wall. Understanding the 5 V's gives you a shared vocabulary for *diagnosing* which wall you have hit and *choosing* the right tool, instead of just throwing a bigger machine at the problem.

## Concept Explanation

### What Is Big Data?
Big Data refers to datasets that are too **large**, too **fast**, or too **complex** for traditional single-machine data processing. The label covers not only the data but the technologies, practices, and skills required to extract value from it. A useful working definition: *if the problem forces you off one machine and onto a cluster (or a serverless service that runs a cluster for you), you are in big-data territory.*

Note that "big" is relative to your tooling. 50 GB is trivial for BigQuery but will crash a naive `pd.read_csv`. The interesting question is never "how many bytes?" — it is "which V is hurting me?"

### The 5 V's of Big Data
Big Data is characterized along five dimensions. The first three (Volume, Velocity, Variety) describe the *problem*; Veracity and Value describe what you must protect and what you are chasing.

| V | Question it answers | Example | What it forces |
|---|---------------------|---------|----------------|
| **Volume** | How much data? | Facebook ingests 4+ PB/day | Distributed / object storage |
| **Velocity** | How fast does it arrive? | 500M+ tweets/day; millions of trades/sec | Streaming or micro-batch |
| **Variety** | How many shapes? | JSON, XML, images, video, logs, tables | Flexible schemas, schema-on-read |
| **Veracity** | Can I trust it? | Dupes, nulls, "USA" vs "United States" | Validation, cleansing, monitoring |
| **Value** | Is it worth it? | A model that cuts fraud losses 25% | A use case that pays for the pipeline |

#### 1. Volume — the amount of data
| Source | Volume generated |
|--------|------------------|
| Facebook | 4+ petabytes of new data daily |
| Google | 20+ petabytes processed daily |
| NYSE | 1+ terabyte of trade data daily |
| Global IoT | ~79+ zettabytes annually (2025 estimate) |

**Implication:** past a certain point one machine cannot hold or scan the data. You move to distributed storage (HDFS), cloud object storage (S3, GCS, Azure Blob), or a serverless warehouse that separates storage from compute.

#### 2. Velocity — the speed of arrival and processing
- Stock trades: millions per second.
- IoT sensors: continuous streams, thousands of events/second per fleet.
- E-commerce: thousands of transactions per minute at peak.

Three processing paradigms answer velocity (covered in depth in `302-big-data-architecture-and-lifecycle`):
- **Batch** — process accumulated data on a schedule.
- **Streaming / real-time** — process each event as it arrives.
- **Near-real-time / micro-batch** — tiny batches with seconds of delay.

#### 3. Variety — the shapes of data
```
+------------------+     +------------------+     +------------------+
|   Structured     |     | Semi-Structured  |     |  Unstructured    |
+------------------+     +------------------+     +------------------+
| Relational DBs   |     | JSON             |     | Text documents   |
| Spreadsheets     |     | XML              |     | Images           |
| CSV files        |     | Log files        |     | Video / audio    |
| Fixed schemas    |     | Key-value stores |     | Free text        |
+------------------+     +------------------+     +------------------+
      ~10%                     ~10%                     ~80%
```
Roughly 80% of enterprise data is unstructured. Integrating across these formats is the core challenge of Variety and is exactly what `exercises/302-data-classification-challenge` drills.

#### 4. Veracity — the trustworthiness of data
Common quality problems: inconsistent formats (dates, addresses), missing values, duplicate records, stale information, measurement error, and outright fraud. The rule is unchanged from your SQL days — **garbage in, garbage out** — but at big-data scale the garbage is harder to see and more expensive to clean. Veracity is the reason pipelines carry validation and monitoring, not just transforms.

#### 5. Value — the business worth
Data has *no* value until it is analyzed and acted upon. Value shows up as predictive analytics, personalization, operational efficiency, risk/fraud management, and new data products. If you cannot name the value, you cannot justify the pipeline — a theme continued in `303-big-data-benefits-and-challenges`.

### Why Traditional Approaches Fail
A classic single-node RDBMS is superb at what it was built for — transactional, row-by-row, strongly-consistent workloads. It struggles when the workload becomes big-data analytics:

| Aspect | Traditional RDBMS | Big Data requirement |
|--------|-------------------|----------------------|
| Scaling | Vertical (buy a bigger box) | Horizontal (add more boxes) |
| Schema | Fixed, defined up front | Flexible, evolving |
| Data types | Structured only | Any format |
| Query profile | Optimized for transactions (OLTP) | Optimized for analytics (OLAP) |
| Cost curve | Expensive licenses, steep at scale | Open-source + pay-per-use cloud |
| Processing | Single machine | Distributed cluster |

Vertical scaling hits a hard ceiling — there is a biggest machine you can buy, and it is wildly expensive. Horizontal scaling adds commodity machines and (in the cloud) lets you rent them by the second. That shift — **scale out, not up** — is the single most important idea behind every big-data technology.

### Building Blocks of a Big Data System
A complete system is an ecosystem of layers, not one product. Each layer is expanded in `302`:

```
+-----------------------------------------------+
|   VISUALIZATION / BI  (dashboards, reports)   |
+-----------------------------------------------+
|   ANALYTICS  (SQL engines, ML, stats)         |
+-----------------------------------------------+
|   PROCESSING  (batch + stream, ETL/ELT)       |
+-----------------------------------------------+
|   STORAGE  (data lake, warehouse, databases)  |
+-----------------------------------------------+
|   INGESTION  (batch loads, streaming, CDC)    |
+-----------------------------------------------+
```

| Layer | Job | Representative tools |
|-------|-----|----------------------|
| Ingestion | Get data in | Kafka, Pub/Sub, Kinesis, Fivetran, Airbyte |
| Storage | Hold data | S3 / GCS / Azure Blob, HDFS, BigQuery, Snowflake |
| Processing | Transform data | Spark, Flink, Dataflow, dbt, Glue |
| Analytics | Extract insight | BigQuery, Trino/Presto, Spark SQL, scikit-learn |
| Visualization | Present insight | Looker, Tableau, Power BI, Superset |

### Real-World Use Cases
| Industry | Big-data use case | Which V dominates |
|----------|-------------------|-------------------|
| Retail | Recommendation engines, demand forecasting | Volume + Value |
| Finance | Real-time fraud detection | Velocity + Veracity |
| Healthcare | Genomics, medical imaging analytics | Volume + Variety |
| IoT / Manufacturing | Predictive maintenance from sensor streams | Velocity |
| Media | Personalized content (Netflix, Spotify) | Volume + Value |

## Code Example
A quick, illustrative script contrasting three scale tiers and the three approaches to the same aggregation. The chunked-vs-in-memory idea is made *runnable* in `demos/301-chunked-vs-inmemory`.

```python
# Same task ("sum value by category"), three scales of tooling.

# 1) Traditional: load everything into memory. Fine for MBs, fatal at scale.
import pandas as pd

def in_memory(path: str) -> pd.Series:
    df = pd.read_csv(path)                 # entire file must fit in RAM
    return df.groupby("category")["value"].sum()

# 2) Chunked: stream the file in pieces — a stepping stone to distributed work.
def chunked(path: str, chunk_size: int = 100_000) -> pd.Series:
    partials = []
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        partials.append(chunk.groupby("category")["value"].sum())
    return pd.concat(partials).groupby(level=0).sum()

# 3) Distributed (PySpark): the same logic across a cluster — handles PB scale.
def distributed():
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import sum as ssum
    spark = SparkSession.builder.appName("bigdata").getOrCreate()
    df = spark.read.csv("gs://bucket/massive/", header=True)   # many machines read in parallel
    return df.groupBy("category").agg(ssum("value").alias("total")).collect()

# The point: the *code* barely changes. What changes is where the work runs.
for tier, rows, size, latency in [
    ("Single machine (pandas)", 1_000_000,     "50 MB",  "seconds"),
    ("Cloud warehouse",         1_000_000_000, "50 GB",  "seconds-minutes"),
    ("Distributed cluster",     1_000_000_000_000, "50 TB+", "minutes (parallel)"),
]:
    print(f"{tier:28} {rows:>15,} rows  {size:>7}  ~{latency}")
```

## Key Takeaways
- Big Data is defined by capability limits, not a fixed byte count: it starts where one machine (or one naive tool) stops.
- The 5 V's — Volume, Velocity, Variety, Veracity, Value — are a diagnostic checklist for *which* problem you have.
- ~80% of real-world data is unstructured; Variety, not just Volume, drives tool choice.
- Traditional RDBMS scale vertically and assume fixed schemas; big data scales horizontally with flexible schemas.
- "Scale out, not up" is the core idea behind every distributed and serverless data technology.
- A big-data system is a layered ecosystem: ingestion → storage → processing → analytics → visualization.
- Value is the point — no use case, no pipeline.

## Resources
- Apache Spark documentation: <https://spark.apache.org/docs/latest/>
- Google BigQuery overview: <https://cloud.google.com/bigquery/docs/introduction>
- NIST Big Data framework: <https://www.nist.gov/programs-projects/nist-big-data-interoperability-framework>
- Sibling notes: `302-big-data-architecture-and-lifecycle`, `303-big-data-benefits-and-challenges`
