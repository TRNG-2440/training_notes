# Spark, PySpark, RDD, EMR and Dataproc Interview Questions with Answers

## Based on the Attached Weekly Topics

**Audience:** Spark / PySpark / Data Engineering cohorts  
**Interview Type:** One-on-one technical interview  
**Suggested Duration:** 30–40 minutes per participant

## Topics Covered

- Spark ecosystem
- Hadoop versus Spark
- Spark setup
- Introduction to Spark and PySpark
- Local versus cluster mode
- RDD fundamentals
- Transformations and actions
- Shared variables and accumulators
- RDD loading and saving
- Pair RDDs
- Spark cluster manager
- Driver and executor configuration
- `spark-submit`
- AWS EMR
- GCP Dataproc
- Cloud Storage
- IAM roles

---

# 1. Spark Fundamentals

## 1. What is Apache Spark?

### Answer

Apache Spark is a distributed data-processing engine used to process large datasets across multiple machines. It supports batch processing, Spark SQL, streaming, machine learning and graph processing. Spark divides data into partitions and processes them in parallel using tasks.

## 2. What are the major components of the Spark ecosystem?

### Answer

| Component | Purpose |
|---|---|
| Spark Core | Basic execution engine and RDD API |
| Spark SQL | DataFrame, SQL and structured-data processing |
| Structured Streaming | Stream-processing API |
| MLlib | Machine-learning library |
| GraphX | Graph-processing library for Scala |
| PySpark | Python API for Spark |

## 3. What is PySpark?

### Answer

PySpark is the Python API for Apache Spark. It allows developers to write Spark applications using Python while Spark’s main execution engine runs on the JVM.

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("PySparkExample")
    .master("local[*]")
    .getOrCreate()
)
```

## 4. What is the difference between Spark and PySpark?

### Answer

Spark is the complete distributed-processing engine. PySpark is the Python interface used to communicate with Spark.

```text
Python program
     ↓
PySpark API
     ↓
Py4J
     ↓
Spark JVM execution engine
```

## 5. What is Spark Core?

### Answer

Spark Core is the fundamental execution layer of Spark. It provides RDDs, task scheduling, memory management, fault recovery, input/output operations and communication with cluster managers.

---

# 2. Hadoop versus Spark

## 6. What is Hadoop?

### Answer

Hadoop is an ecosystem for distributed storage and processing. Important components include HDFS, YARN and MapReduce.

## 7. What is the difference between Hadoop MapReduce and Spark?

### Answer

| Feature | Hadoop MapReduce | Spark |
|---|---|---|
| Processing | Disk-oriented | Can process in memory |
| Execution model | Map and Reduce stages | DAG-based execution |
| Iterative processing | Slower | More efficient |
| APIs | Primarily Java | Python, Scala, Java and R |
| Streaming | Separate tools | Structured Streaming |
| SQL | Hive often used | Spark SQL |
| Machine learning | External libraries | MLlib |

## 8. Is Spark a replacement for Hadoop?

### Answer

Not completely. Spark can replace Hadoop MapReduce as the processing engine, but it can still use HDFS, YARN and Hadoop-compatible input formats.

## 9. Can Spark work without Hadoop?

### Answer

Yes. Spark can run locally, in standalone mode, on Kubernetes and on cloud services. It can read local files and object storage such as S3 and Google Cloud Storage.

---

# 3. Spark Setup

## 10. What software is generally required to run PySpark locally?

### Answer

- Python
- Java
- PySpark
- An IDE such as VS Code
- A Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pyspark
```

## 11. Why is Java required for PySpark?

### Answer

Spark’s execution engine runs on the JVM. PySpark communicates with the JVM-based engine through Py4J.

## 12. What is a Python virtual environment?

### Answer

A virtual environment creates an isolated Python environment for one project and prevents dependency conflicts.

## 13. What does `master("local[*]")` mean?

### Answer

It runs Spark locally using all available logical CPU cores.

| Setting | Meaning |
|---|---|
| `local` | One thread |
| `local[2]` | Two worker threads |
| `local[4]` | Four worker threads |
| `local[*]` | All available logical cores |

---

# 4. Local Mode versus Cluster Mode

## 14. What is local mode?

### Answer

In local mode, driver and worker execution occur on the same machine and tasks run as local threads. It is suitable for development and testing.

## 15. What is cluster mode?

### Answer

In cluster mode, Spark uses multiple machines, a cluster manager allocates resources and executors run on worker nodes.

## 16. What changes when moving from local mode to cluster mode?

### Answer

- Local paths must be replaced with shared storage paths
- Resources must be configured
- Cluster permissions are required
- Executors run on separate machines
- Logging and monitoring change
- `spark-submit` is normally used

---

# 5. RDD Fundamentals

## 17. What is an RDD?

### Answer

RDD stands for Resilient Distributed Dataset. It is distributed, partitioned, immutable, lazily evaluated and fault tolerant.

## 18. Why is an RDD called resilient?

### Answer

Spark can recompute lost partitions using lineage.

## 19. What does immutable mean in RDD?

### Answer

An RDD cannot be changed after creation. Every transformation creates a new RDD.

## 20. What is an RDD partition?

### Answer

A partition is a logical portion of an RDD. Spark normally creates one task per partition during a stage.

## 21. What is lazy evaluation?

### Answer

Spark does not execute transformations immediately. Execution begins when an action such as `count()` or `collect()` runs.

---

# 6. RDD Creation

## 22. How can you create an RDD using `parallelize()`?

### Answer

```python
numbers_rdd = sc.parallelize([10, 20, 30, 40], 2)
```

## 23. What does `textFile()` do?

### Answer

It reads text data and creates an `RDD[str]`, with each element normally representing one line.

## 24. What is the difference between `textFile()` and `wholeTextFiles()`?

### Answer

`textFile()` returns one element per line. `wholeTextFiles()` returns one `(path, complete_content)` element per file.

## 25. Can you create an empty RDD with partitions?

### Answer

Yes.

```python
empty_rdd = sc.parallelize([], 4)
```

This creates zero records with four partitions.

---

# 7. Transformations

## 26. What is an RDD transformation?

### Answer

A transformation creates a new RDD from an existing RDD. Examples include `map()`, `filter()`, `flatMap()`, `distinct()`, `reduceByKey()` and `join()`.

## 27. What does `map()` do?

### Answer

It produces exactly one output for each input.

## 28. What does `filter()` do?

### Answer

It keeps only records that satisfy a Boolean condition.

## 29. What does `flatMap()` do?

### Answer

It can produce zero, one or many outputs from one input and then flattens them.

## 30. What is the difference between `map()` and `flatMap()`?

### Answer

| Method | Output per input |
|---|---|
| `map()` | Exactly one |
| `flatMap()` | Zero, one or many |

## 31. What does `distinct()` do?

### Answer

It removes duplicate values and normally causes a shuffle.

---

# 8. Actions

## 32. What is an action?

### Answer

An action triggers Spark execution. Examples include `count()`, `collect()`, `first()`, `take()`, `reduce()` and `takeOrdered()`.

## 33. What does `collect()` do?

### Answer

It returns all RDD records to the driver as a Python list.

## 34. Why can `collect()` cause driver failure?

### Answer

Because all distributed records are transferred into driver memory.

## 35. What is the difference between `take()` and `takeOrdered()`?

### Answer

`take(n)` returns the first `n` records Spark finds. `takeOrdered(n)` returns `n` records according to ordering.

## 36. How do you get the three largest values using `takeOrdered()`?

### Answer

```python
top_three = rdd.takeOrdered(3, key=lambda value: -value)
```

---

# 9. Pair RDDs

## 37. What is a Pair RDD?

### Answer

A Pair RDD contains `(key, value)` elements.

## 38. What does `reduceByKey()` do?

### Answer

It combines values for the same key.

## 39. What is the difference between `groupByKey()` and `reduceByKey()`?

### Answer

`groupByKey()` keeps all values. `reduceByKey()` produces one aggregated value and is usually better for sums and counts.

## 40. When should `groupByKey()` be used?

### Answer

Use it when the complete list of values is required.

## 41. What does `mapValues()` do?

### Answer

It changes only the value of a Pair RDD and preserves the key.

## 42. What does `sortByKey()` do?

### Answer

It sorts a Pair RDD by key.

## 43. What does `join()` do?

### Answer

It matches Pair RDD records using the same key.

---

# 10. Shared Variables

## 44. What are shared variables in Spark?

### Answer

The main shared variables are broadcast variables and accumulators.

## 45. What is a broadcast variable?

### Answer

A broadcast variable efficiently sends a read-only value to executors.

## 46. What is an accumulator?

### Answer

An accumulator is a shared counter or sum that tasks can update.

## 47. What is the difference between a broadcast variable and an accumulator?

### Answer

| Broadcast | Accumulator |
|---|---|
| Read-only on executors | Executors add values |
| Used for lookup data | Used for counters and metrics |
| Driver distributes value | Driver reads final value |

---

# 11. RDD Data Loading and Saving

## 48. How do you save an RDD as text?

### Answer

```python
result_rdd.saveAsTextFile("outputs/category_revenue")
```

## 49. Why does Spark create many part files?

### Answer

Each partition is normally written by one task.

## 50. How can you reduce the number of output files?

### Answer

```python
result_rdd.coalesce(2).saveAsTextFile("outputs/report")
```

## 51. What is the difference between `repartition()` and `coalesce()`?

### Answer

`repartition()` can increase or decrease partitions and performs a shuffle. `coalesce()` is commonly used to reduce partitions with less data movement.

---

# 12. Spark Cluster Architecture

## 52. What is a Spark cluster manager?

### Answer

A cluster manager allocates CPU and memory resources to Spark applications.

## 53. What is the Spark driver?

### Answer

The driver runs the main program, builds the DAG, creates jobs and stages and schedules tasks.

## 54. What is an executor?

### Answer

An executor runs tasks, stores cached data, performs shuffle and reports status to the driver.

## 55. Explain application, job, stage and task.

### Answer

```text
Application
  └── Job
       └── Stage
            └── Task
```

## 56. What normally creates a new stage?

### Answer

A shuffle boundary. Examples include `reduceByKey()`, `groupByKey()`, `join()`, `distinct()`, `sortBy()` and `repartition()`.

---

# 13. Driver and Executor Memory

## 57. What is driver memory?

### Answer

Driver memory stores application objects, execution plans, task metadata and small collected results.

## 58. What is executor memory?

### Answer

Executor memory is used for task execution, cached data, shuffle processing and aggregations.

## 59. What can cause driver out-of-memory?

### Answer

Large `collect()`, large `collectAsMap()`, large broadcasts and excessive local objects.

## 60. What can cause executor out-of-memory?

### Answer

Very large partitions, data skew, large shuffles, excessive caching and large groupings.

---

# 14. spark-submit

## 61. What is `spark-submit`?

### Answer

It is the standard command used to submit Spark applications.

```bash
spark-submit --master local[4] src/job.py
```

## 62. How do you provide driver memory using `spark-submit`?

### Answer

```bash
spark-submit --driver-memory 2g src/job.py
```

## 63. How do you configure executor resources?

### Answer

```bash
spark-submit \
  --executor-memory 4g \
  --executor-cores 2 \
  --num-executors 3 \
  src/job.py
```

## 64. What is the difference between client mode and cluster mode?

### Answer

In client mode, the driver runs where `spark-submit` is launched. In cluster mode, the driver runs inside the cluster.

---

# 15. AWS EMR

## 65. What is AWS EMR?

### Answer

Amazon EMR is a managed big-data service for running Spark on AWS infrastructure.

## 66. What are the main EMR node types?

### Answer

| Node type | Purpose |
|---|---|
| Primary node | Coordinates the cluster |
| Core node | Runs tasks and can store HDFS data |
| Task node | Runs tasks without permanent HDFS storage |

## 67. What storage is commonly used with EMR Spark jobs?

### Answer

Amazon S3.

## 68. What IAM roles are required for EMR?

### Answer

Commonly an EMR service role and an EC2 instance profile or node role.

## 69. Why should S3 buckets remain private?

### Answer

To prevent unauthorized public access. Use encryption, block public access and least-privilege IAM policies.

## 70. What is an EMR step?

### Answer

An EMR step is a unit of work submitted to an EMR cluster, often using `spark-submit`.

## 71. How would you run a Spark job on EMR?

### Answer

Upload code and data to S3, create the cluster, configure IAM roles, add a Spark step and write results back to S3.

---

# 16. GCP Dataproc

## 72. What is Google Cloud Dataproc?

### Answer

Dataproc is Google Cloud’s managed service for running Spark and Hadoop clusters.

## 73. What is the GCP equivalent of S3 for Spark data?

### Answer

Google Cloud Storage using `gs://` paths.

## 74. What is the difference between EMR and Dataproc?

### Answer

| AWS EMR | GCP Dataproc |
|---|---|
| AWS managed service | Google Cloud managed service |
| Common storage: S3 | Common storage: Cloud Storage |
| Uses IAM roles | Uses service accounts and IAM |
| Runs on EC2 | Runs on Compute Engine |

## 75. What is a Dataproc service account?

### Answer

It is an identity used by Dataproc cluster resources to access Cloud Storage, logging, monitoring and compute resources.

## 76. How do you submit a PySpark job to Dataproc?

### Answer

```bash
gcloud dataproc jobs submit pyspark \
  gs://bucket/jobs/job.py \
  --cluster=my-cluster \
  --region=my-region
```

---

# 17. Scenario-Based Questions

## 77. A participant uses `collect()` on 100 million records. What happens?

### Answer

All records move to the driver and may cause driver out-of-memory.

## 78. Revenue must be calculated per category. Which operation should be used?

### Answer

Use `map()` to create `(category, amount)` pairs and `reduceByKey()` to aggregate them.

## 79. All order IDs must be displayed per category. Which operation should be used?

### Answer

Use `groupByKey()` because all original values are required.

## 80. A Spark output directory contains 500 small files. What should you do?

### Answer

Use `coalesce()` to reduce output partitions before saving.

## 81. One Spark task runs much longer than all others. What may be happening?

### Answer

Data skew. Consider repartitioning, key salting, filtering earlier or using a better key.

## 82. A small tax-rate dictionary is required for every order. What should you use?

### Answer

A broadcast variable.

## 83. Invalid rows must be counted during processing. What should you use?

### Answer

An accumulator for monitoring.

## 84. A local Windows path works locally but fails on EMR. Why?

### Answer

The path exists only on the local machine. Use an S3 path.

## 85. A local path works locally but fails on Dataproc. Why?

### Answer

Use a Google Cloud Storage path instead.

## 86. A job reads the same cleaned RDD five times. How can recomputation be reduced?

### Answer

Cache or persist the RDD and call an action to materialize it.

## 87. An RDD has two partitions, but the computer has eight cores. How many tasks run?

### Answer

Approximately two tasks because task count is based primarily on partition count.

## 88. `reduceByKey()` produces two stages. Why?

### Answer

It causes a shuffle boundary between local aggregation and final aggregation.

## 89. The Spark UI Storage tab is empty after calling `cache()`. Why?

### Answer

`cache()` is lazy. An action such as `count()` must materialize it.

## 90. An EMR cluster cannot read an S3 bucket. What should be checked?

### Answer

IAM permissions, bucket policy, prefix, region, encryption permissions and the S3 URI.

## 91. A Dataproc job cannot access a Cloud Storage bucket. What should be checked?

### Answer

Service account permissions, object path, bucket location, cluster region and the `gs://` URI.

---

# 18. Code-Reading Questions

## 92. Explain this code

```python
city_revenue_rdd = (
    completed_orders_rdd
    .map(lambda order: (order["city"], order["net_amount"]))
    .reduceByKey(lambda left, right: left + right)
    .sortBy(lambda pair: pair[1], ascending=False)
)
```

### Answer

It creates city/amount pairs, totals revenue per city and sorts cities by total revenue descending.

## 93. What is inefficient in this code?

```python
totals = category_amount_rdd.groupByKey().mapValues(sum)
```

### Answer

It shuffles all values. `reduceByKey()` is more efficient for totals.

## 94. Predict the output

```python
rdd = sc.parallelize(["Spark SQL", "RDD Spark"])
result = rdd.flatMap(lambda line: line.split()).collect()
```

### Answer

```python
["Spark", "SQL", "RDD", "Spark"]
```

## 95. Predict the output

```python
empty_rdd = sc.parallelize([], 3)
print(empty_rdd.count())
print(empty_rdd.getNumPartitions())
print(empty_rdd.collect())
```

### Answer

```text
0
3
[]
```

---

# 19. Recommended 30-Minute Interview Set

## Fundamentals

1. What is Spark?
2. What is PySpark?
3. What is an RDD?
4. What is a partition?
5. Explain transformation versus action.
6. Explain lazy evaluation.

## Operations

7. `map()` versus `flatMap()`
8. `groupByKey()` versus `reduceByKey()`
9. `repartition()` versus `coalesce()`
10. `take()` versus `takeOrdered()`

## Architecture

11. Explain driver and executor.
12. Explain job, stage and task.
13. What creates a shuffle?
14. What does the Spark UI show?

## Cloud

15. What is AWS EMR?
16. What is GCP Dataproc?
17. Why use S3 or Cloud Storage?
18. What is an IAM role or service account?

## Scenario

19. Driver crashes after `collect()`
20. Too many output files
21. One slow partition
22. Local path fails on cloud
23. Small lookup dataset
24. Repeated RDD computation

---

# 20. Evaluation Rubric

| Score | Assessment |
|---:|---|
| 85–100% | Strong conceptual and practical understanding |
| 70–84% | Good understanding with minor gaps |
| 55–69% | Understands syntax but needs support with distributed execution |
| 40–54% | Mostly memorized knowledge |
| Below 40% | Requires remediation |

## Strong Participant Indicators

- Explains lazy evaluation clearly
- Selects `reduceByKey()` for aggregation
- Avoids unnecessary `collect()`
- Understands partition-to-task relationship
- Identifies shuffle operations
- Understands caching
- Explains driver and executor roles
- Can compare local and cluster execution
- Understands S3 and Cloud Storage paths
- Can describe IAM roles or service accounts

## Warning Signs

- Thinks transformations execute immediately
- Uses `groupByKey()` for every aggregation
- Thinks `local[*]` is a distributed cluster
- Uses local paths in cloud jobs
- Cannot explain partitions and tasks
- Uses `collect()` for large data
- Cannot identify driver versus executor
- Assumes `cache()` immediately stores data
