# Local Spark SQL Example with CSV, JSON, SQL Transformations and Report Output

## 1. Objective

This example demonstrates a small but complete local data-engineering workflow in **VS Code**:

```text
CSV support-ticket data
        +
JSON agent master data
        |
        v
SparkSession
        |
        v
Schema validation and cleaning
        |
        v
Filter resolved tickets
        |
        v
Join tickets with agents
        |
        v
Spark SQL aggregation
        |
        v
Parquet report + CSV report
```

The use case is a **customer-support ticket performance report**.

The final report contains:

- Team and location
- Number of resolved tickets
- Average resolution time
- Average customer rating
- Tickets handled within SLA
- SLA breaches
- SLA compliance percentage

---

## 2. Why use multiple file formats?

Real projects rarely receive all data in one format.

In this example:

| File | Purpose |
|---|---|
| `support_tickets.csv` | Transaction-style ticket records |
| `agents.json` | Agent reference/master data |
| Parquet output | Efficient columnar output for analytics and reporting |
| CSV output | Easy manual inspection and sharing |

Spark SQL supports many data sources through the DataFrame interface. A DataFrame can be registered as a temporary view and queried using SQL.

---

## 3. Project structure

```text
spark_sql_local_multiformat_demo/
├── data/
│   ├── support_tickets.csv
│   └── agents.json
├── docs/
│   └── LOCAL_SPARK_SQL_MULTIFORMAT_NOTES.md
├── output/
├── src/
│   ├── common.py
│   └── 01_support_ticket_spark_sql_demo.py
├── requirements.txt
└── run_demo.ps1
```

---

## 4. Software requirements

Use:

- Windows 10 or Windows 11
- VS Code
- Python
- Java 17 or later
- PySpark
- VS Code Python extension

Current PySpark documentation requires Java 17 or later and a correctly configured `JAVA_HOME`.

Check the installations:

```powershell
python --version
java -version
echo $env:JAVA_HOME
```

---

## 5. Create the virtual environment

Open the project in VS Code and run:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the requirement:

```powershell
pip install -r requirements.txt
```

---

## 6. Input file 1: CSV ticket data

The CSV contains operational records.

```csv
ticket_id,created_date,agent_id,category,priority,status,resolution_hours,customer_rating
T1001,2026-07-01,A101,Login Issue,HIGH,RESOLVED,2.5,5
T1002,2026-07-01,A102,Payment Issue,CRITICAL,RESOLVED,5.0,4
```

Important columns:

| Column | Meaning |
|---|---|
| `ticket_id` | Unique ticket identifier |
| `agent_id` | Agent who handled the ticket |
| `priority` | LOW, MEDIUM, HIGH or CRITICAL |
| `status` | OPEN, IN_PROGRESS, RESOLVED or CLOSED |
| `resolution_hours` | Time required to resolve the ticket |
| `customer_rating` | Rating from 1 to 5 |

---

## 7. Input file 2: JSON agent master

Each line is one JSON record:

```json
{"agent_id":"A101","agent_name":"Ananya","team":"Identity Support","location":"Chennai"}
```

This file enriches the ticket data with:

- Agent name
- Team
- Location

---

## 8. `common.py`

### Purpose

`common.py` stores shared paths and creates the local `SparkSession`.

```python
spark = (
    SparkSession.builder
    .appName("Local-Spark-SQL-Multi-Format-Demo")
    .master("local[*]")
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.ui.enabled", "true")
    .config("spark.ui.port", "4040")
    .getOrCreate()
)
```

### Explanation

| Code | Purpose |
|---|---|
| `appName(...)` | Gives the Spark application a meaningful name |
| `master("local[*]")` | Runs locally and uses available CPU cores |
| `spark.sql.shuffle.partitions` | Uses four shuffle partitions for the small demo |
| `spark.ui.enabled` | Enables the live Spark UI |
| `spark.ui.port` | Requests port 4040 |
| `getOrCreate()` | Creates a session or returns an existing one |

The same session provides:

```python
spark.read
spark.sql(...)
spark.createDataFrame(...)
spark.catalog
spark.sparkContext
```

---

## 9. Step-by-step execution flow

### Step 1: Define the CSV schema

```python
ticket_schema = StructType(
    [
        StructField("ticket_id", StringType(), False),
        StructField("created_date", StringType(), False),
        ...
    ]
)
```

Why define a schema?

- Avoids repeated inference
- Makes expected types clear
- Detects incompatible data earlier
- Produces predictable processing

---

### Step 2: Read the CSV

```python
tickets_df = (
    spark.read
    .option("header", True)
    .schema(ticket_schema)
    .csv(str(DATA_DIR / "support_tickets.csv"))
)
```

Flow:

```text
support_tickets.csv
        |
        v
CSV reader
        |
        v
Apply ticket schema
        |
        v
tickets_df
```

The DataFrame is distributed into partitions. In local mode, the partitions are processed by threads on the local machine.

---

### Step 3: Read JSON

```python
agents_df = spark.read.json(
    str(DATA_DIR / "agents.json")
)
```

Spark infers the JSON structure and creates columns such as:

```text
agent_id
agent_name
team
location
```

---

### Step 4: Clean and enrich records

```python
prepared_tickets_df = (
    tickets_df
    .withColumn("created_date", F.to_date("created_date", "yyyy-MM-dd"))
    .withColumn("status", F.upper(F.trim("status")))
    .withColumn("priority", F.upper(F.trim("priority")))
)
```

Transformations:

| Transformation | Result |
|---|---|
| `to_date()` | Converts text to Spark DateType |
| `trim()` | Removes surrounding spaces |
| `upper()` | Standardizes text case |
| `withColumn()` | Adds or replaces a column |

Then the code assigns a priority score and SLA target:

```text
CRITICAL -> score 4 -> target 4 hours
HIGH     -> score 3 -> target 6 hours
MEDIUM   -> score 2 -> target 12 hours
LOW      -> score 1 -> target 24 hours
```

---

### Step 5: Filter resolved tickets

```python
resolved_tickets_df = prepared_tickets_df.filter(
    (F.col("status").isin("RESOLVED", "CLOSED"))
    & F.col("resolution_hours").isNotNull()
)
```

Only records suitable for resolution reporting remain.

```text
All tickets
    |
    +-- OPEN ---------------- removed
    |
    +-- IN_PROGRESS --------- removed
    |
    +-- RESOLVED/CLOSED ----- retained
```

`filter()` is a narrow transformation. Each input partition can filter its own records without first moving all records across partitions.

---

### Step 6: Join CSV and JSON data

```python
detailed_df = resolved_tickets_df.join(
    agents_df,
    on="agent_id",
    how="left",
)
```

Logical join:

```text
Resolved ticket                     Agent master
+----------+----------+             +----------+------------------+
|ticket_id |agent_id  |             |agent_id  |team              |
+----------+----------+             +----------+------------------+
|T1001     |A101      |     JOIN    |A101      |Identity Support  |
+----------+----------+             +----------+------------------+
                 |
                 v
+----------+----------+------------------+
|ticket_id |agent_id  |team              |
+----------+----------+------------------+
|T1001     |A101      |Identity Support  |
+----------+----------+------------------+
```

The code also creates an SLA status:

```python
F.when(
    F.col("resolution_hours") <= F.col("sla_target_hours"),
    "WITHIN SLA",
).otherwise("SLA BREACHED")
```

---

### Step 7: Register a temporary SQL view

```python
detailed_df.createOrReplaceTempView(
    "resolved_ticket_details"
)
```

A temporary view lets Spark SQL query the DataFrame as though it were a table:

```sql
SELECT *
FROM resolved_ticket_details
```

The view exists only for the current Spark session.

---

### Step 8: Aggregate with Spark SQL

```sql
SELECT
    team,
    location,
    COUNT(*) AS resolved_ticket_count,
    ROUND(AVG(resolution_hours), 2) AS average_resolution_hours,
    ROUND(AVG(customer_rating), 2) AS average_customer_rating
FROM resolved_ticket_details
GROUP BY team, location
```

`GROUP BY` usually introduces a shuffle.

```text
Input partitions
 P0        P1        P2
 |         |         |
 +---------+---------+
           |
           v
Shuffle by team and location
           |
     +-----+-----+
     |           |
Identity      Billing
Support       Support
     |           |
     v           v
Aggregate     Aggregate
```

Records with the same grouping key must reach the same target partition.

---

## 10. Lazy evaluation and actions

These are transformations:

```python
.withColumn(...)
.filter(...)
.join(...)
.groupBy(...)
```

They build a logical plan.

These are actions:

```python
.show()
.write.parquet(...)
.write.csv(...)
```

Actions cause Spark to execute the plan.

```text
Transformations build the plan
            |
            v
Action is called
            |
            v
Spark creates a job
            |
            v
Job is divided into stages
            |
            v
Stages create tasks for partitions
```

---

## 11. Save the report as Parquet

```python
report_df.write.mode("overwrite").parquet(
    str(parquet_output)
)
```

Parquet is selected as the main reporting output because it is:

- Columnar
- Compressed
- Schema-aware
- Efficient for selecting only required columns
- Widely supported by analytics and reporting systems

The result is a directory containing files similar to:

```text
support_team_report_parquet/
├── _SUCCESS
├── part-00000-....snappy.parquet
└── part-00001-....snappy.parquet
```

Spark writes a folder because distributed partitions can produce multiple part files.

---

## 12. Save a CSV copy

```python
(
    report_df
    .coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(str(csv_output))
)
```

The CSV copy is included for easy inspection.

`coalesce(1)` reduces the small report to one output partition. It should not be used casually for large production data because it can force all output through one task.

---

## 13. Read the Parquet report back

```python
validated_df = spark.read.parquet(
    str(parquet_output)
)
```

Reading the saved file confirms that:

- The output exists
- The schema was preserved
- The report is usable for later analytics

---

## 14. Run the demonstration

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python .\src\01_support_ticket_spark_sql_demo.py
```

Alternatively:

```powershell
.\run_demo.ps1
```

---

## 15. Spark UI

While the program is waiting at the final prompt, open:

```text
http://localhost:4040
```

Inspect:

### Jobs

Shows jobs created by actions such as:

- `show()`
- Parquet write
- CSV write
- Parquet validation read

### SQL/DataFrame

Shows:

- File scan
- Filter
- Project
- Join
- Aggregate
- Sort
- File writes

### Stages

Shows stage boundaries. Shuffle operations such as `GROUP BY` and some joins can create new stages.

### Executors

In local mode, the driver also performs local execution using multiple threads.

### Environment

Shows Spark properties such as application name, master and shuffle partitions.

---

## 16. Expected report structure

```text
+------------------+---------+---------------------+------------------------+
|team              |location |resolved_ticket_count|average_resolution_hours|
+------------------+---------+---------------------+------------------------+
|Identity Support  |Chennai  |...                  |...                     |
|Billing Support   |Bengaluru|...                  |...                     |
+------------------+---------+---------------------+------------------------+
```

The exact values are generated from the supplied data.

---

## 17. Reporting-tool usage

The Parquet output can be used by tools and platforms that can read Parquet directly or through an analytical engine.

Typical architecture:

```text
Spark SQL output
      |
      v
Parquet files
      |
      +--> Data lake query engine
      |
      +--> Data warehouse loading process
      |
      +--> Python analytics
      |
      +--> BI/reporting integration
```

For a very small manual report, use the CSV copy. For scalable analytical processing, use Parquet.

---

## 18. Important concepts demonstrated

- Local `SparkSession`
- CSV ingestion with explicit schema
- JSON ingestion
- DataFrame transformations
- Date conversion and text normalization
- Conditional columns
- Filtering
- Joining two formats
- Temporary SQL view
- SQL aggregation
- Shuffle concept
- Parquet output
- CSV output
- Output validation
- Spark UI inspection

---

## 19. Common errors

### Java is not recognized

Check:

```powershell
java -version
echo $env:JAVA_HOME
```

Install Java 17 or later and configure `JAVA_HOME`.

### `ModuleNotFoundError: No module named 'pyspark'`

Activate the correct environment:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Input path not found

Run the script from the project root:

```powershell
python .\src\01_support_ticket_spark_sql_demo.py
```

### Port 4040 is unavailable

Another Spark application may be using the port. Spark can select the next available port, such as 4041. Use the URL printed by:

```python
spark.sparkContext.uiWebUrl
```

---

## 20. Practice extensions

1. Add a `channel` column such as Email, Chat and Phone.
2. Calculate SLA compliance by channel.
3. Save the detailed joined data as partitioned Parquet by `location`.
4. Add a date-level report.
5. Compare resolved and unresolved ticket counts.
6. Add an agent ranking using a Spark SQL window function.
