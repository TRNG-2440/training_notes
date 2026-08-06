<div align="center">

# 🔵 Data Warehouse vs 🟢 Data Lake vs 🟣 Lakehouse

### Architecture, Data Flow, Features, Use Cases and Interview Questions

</div>

![Professional 3D architecture comparison of Data Warehouse, Data Lake and Lakehouse](data_warehouse_vs_data_lake_vs_lakehouse_infographic.png)

> **Colour guide:** 🔵 Data Warehouse · 🟢 Data Lake · 🟣 Lakehouse · 🟠 Important concept

---

Think of these three systems as different ways of **storing, organizing, processing, and serving business data**.

* A **Data Warehouse** is like a well-organized supermarket.
* A **Data Lake** is like a large storage reservoir containing water from many sources.
* A **Lakehouse** combines the flexibility of the lake with the organization and reliability of the warehouse.

The visual below lets you compare their architecture and data flow.

---

## 1. Why do we need these systems?

An organization generates data from many places:

* Customer applications
* Websites and mobile apps
* Sales systems
* Banking transactions
* CRM and ERP applications
* Sensors and IoT devices
* Log files
* Social media
* Images, videos and documents

Operational systems are designed to run the daily business. For example:

```text
Customer places an order
        ↓
Application validates payment
        ↓
Order database stores the transaction
        ↓
Warehouse system updates inventory
```

These systems are excellent for handling individual transactions. However, they are usually not designed to answer analytical questions such as:

* What was our total revenue for the last three years?
* Which region has the highest customer growth?
* Which products are frequently purchased together?
* Which customers are likely to leave?
* What caused yesterday’s sales decline?

For those questions, data is copied into a specialized analytical platform: a warehouse, lake or lakehouse.

---

# 🔵 Part 1: Data Warehouse

## 2. What is a Data Warehouse?

A **Data Warehouse** is a centralized system that stores **cleaned, transformed and structured data** for reporting and analysis.

The data is normally organized into:

* Rows and columns
* Tables
* Facts and dimensions
* Star or snowflake schemas

Examples of data warehouse technologies include:

* Amazon Redshift
* Google BigQuery
* Azure Synapse Analytics
* Snowflake
* Teradata
* Oracle Autonomous Data Warehouse

---

## 3. Data Warehouse architecture

```text
+---------------------+
| Operational Systems |
|---------------------|
| CRM                 |
| ERP                 |
| Sales Database      |
| HR System           |
| Finance System      |
+----------+----------+
           |
           | Extract
           v
+---------------------+
| ETL Processing      |
|---------------------|
| Clean data          |
| Remove duplicates   |
| Standardize values  |
| Apply business rules|
| Join datasets       |
+----------+----------+
           |
           | Load structured data
           v
+-----------------------------+
|       DATA WAREHOUSE        |
|-----------------------------|
| Fact_Sales                  |
| Dim_Customer                |
| Dim_Product                 |
| Dim_Date                    |
| Dim_Store                   |
+--------------+--------------+
               |
        SQL and BI queries
               |
       +-------+-------+
       |               |
       v               v
+-------------+   +-------------+
| Dashboards  |   | Reports     |
| Power BI    |   | Analysts    |
| Tableau     |   | Management  |
+-------------+   +-------------+
```

---

## 4. Schema-on-write

A data warehouse normally follows **schema-on-write**.

This means the structure must be defined before the data is stored.

Suppose the source contains:

```text
customer_id, customer_name, city, purchase_amount
```

Before loading it into the warehouse, we define a table:

```sql
CREATE TABLE sales (
    customer_id       INTEGER,
    customer_name     VARCHAR(100),
    city              VARCHAR(50),
    purchase_amount   DECIMAL(10,2)
);
```

The incoming data must match this structure.

```text
Raw Data
   ↓
Validate structure
   ↓
Clean data
   ↓
Transform data
   ↓
Write into predefined tables
```

### Why is this useful?

Because warehouse data becomes:

* Consistent
* Validated
* Easy to query
* Business-friendly
* Reliable for reports

### Limitation

A lot of preparation is required before the data can be stored.

---

## 5. Star schema example

Consider an e-commerce company.

### Fact table

```text
Fact_Sales
--------------------------------------------------
sale_id
customer_key
product_key
date_key
store_key
quantity
unit_price
discount
sales_amount
```

### Dimension tables

```text
Dim_Customer           Dim_Product
----------------       ----------------
customer_key           product_key
customer_name          product_name
city                   category
state                  brand
segment                supplier

Dim_Date               Dim_Store
----------------       ----------------
date_key               store_key
full_date              store_name
month                  city
quarter                state
year                   region
```

### Diagram

```text
                  +----------------+
                  |  Dim_Customer  |
                  +-------+--------+
                          |
                          |
+-------------+    +------+-------+    +-------------+
| Dim_Product |----|  Fact_Sales  |----|  Dim_Date   |
+-------------+    +------+-------+    +-------------+
                          |
                          |
                  +-------+--------+
                  |   Dim_Store    |
                  +----------------+
```

The central fact table contains measurable business events. Dimension tables provide descriptive information.

---

## 6. Typical Data Warehouse workflow

```text
Source database
      ↓
Nightly ETL job
      ↓
Clean invalid records
      ↓
Convert datatypes
      ↓
Join customer and product data
      ↓
Calculate sales amount
      ↓
Load warehouse tables
      ↓
Refresh Power BI dashboard
```

### Example SQL query

```sql
SELECT
    d.year,
    p.category,
    SUM(f.sales_amount) AS total_sales
FROM Fact_Sales f
JOIN Dim_Date d
    ON f.date_key = d.date_key
JOIN Dim_Product p
    ON f.product_key = p.product_key
GROUP BY
    d.year,
    p.category
ORDER BY
    d.year,
    total_sales DESC;
```

---

## 7. Strengths of a Data Warehouse

* Fast analytical SQL queries
* High-quality, validated data
* Strong governance and security
* Suitable for business intelligence
* Consistent business definitions
* Excellent performance for dashboards
* Supports historical reporting

## 8. Limitations of a Data Warehouse

* Structured data is preferred
* Loading unstructured data can be difficult
* Data preparation can take significant time
* Storage and compute can be expensive
* Schema changes may require redesign
* Less suitable for raw data exploration
* Less flexible for machine learning workloads

---

# 🟢 Part 2: Data Lake

## 9. What is a Data Lake?

A **Data Lake** is a centralized repository that stores large quantities of data in its original or near-original form.

It can store:

### Structured data

```text
Database tables
CSV files
Transaction records
```

### Semi-structured data

```text
JSON
XML
Application logs
Web events
```

### Unstructured data

```text
Images
Videos
Audio
PDF documents
Emails
```

Examples of technologies commonly used for data lakes include:

* Amazon S3
* Azure Data Lake Storage
* Google Cloud Storage
* Hadoop HDFS
* MinIO

A storage service alone is not the complete data platform, but it often forms the foundation of the lake.

---

## 10. Data Lake architecture

```text
+------------------------------------------------+
|                 DATA SOURCES                   |
|------------------------------------------------|
| Databases | APIs | Logs | IoT | Images | Video |
+------------------------+-----------------------+
                         |
                         | Batch and streaming ingestion
                         v
+------------------------------------------------+
|                   DATA LAKE                    |
|------------------------------------------------|
| CSV | JSON | Parquet | XML | Images | Logs     |
| Audio | Video | Documents | Sensor Records     |
+------------------------+-----------------------+
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
+---------------+ +---------------+ +---------------+
| Data Engineer | | Data Scientist| | ML Engineer   |
| Spark         | | Exploration   | | Model Training|
+---------------+ +---------------+ +---------------+
```

---

## 11. Schema-on-read

A data lake generally uses **schema-on-read**.

The data is stored first. Its structure is interpreted when someone reads it.

```text
Store raw data immediately
           ↓
Keep original format
           ↓
Choose a processing tool
           ↓
Apply schema while reading
           ↓
Transform for the current use case
```

Example raw JSON:

```json
{
  "customer_id": "C101",
  "purchase_amount": "4500.75",
  "event_time": "2026-08-05T10:30:00",
  "device": {
    "type": "mobile",
    "os": "Android"
  }
}
```

Spark can apply a schema when reading it:

```python
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType
)

schema = StructType([
    StructField("customer_id", StringType(), True),
    StructField("purchase_amount", DoubleType(), True),
    StructField("event_time", StringType(), True)
])

events_df = spark.read.schema(schema).json("data/events/")
```

The lake did not force the data to follow a predefined table when it arrived.

---

## 12. Data Lake folder design

A simple data lake might be organized like this:

```text
data-lake/
│
├── raw/
│   ├── customers/
│   ├── orders/
│   ├── clickstream/
│   ├── logs/
│   └── images/
│
├── cleaned/
│   ├── customers/
│   ├── orders/
│   └── clickstream/
│
└── curated/
    ├── daily_sales/
    ├── customer_360/
    └── product_performance/
```

However, in a traditional unmanaged lake, the organization may gradually become inconsistent:

```text
data-lake/
├── sales_final.csv
├── sales_final_new.csv
├── sales_final_updated.csv
├── final_sales_v2.csv
├── use_this_sales.csv
└── latest_final_sales_really_final.csv
```

This is one example of how a lake can become difficult to govern.

---

## 13. Data swamp problem

A badly managed data lake is often called a **data swamp**.

```text
                  DATA LAKE
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
  No catalog    Poor quality   Unknown owners
       |             |             |
       +-------------+-------------+
                     |
                     v
                 DATA SWAMP
```

Common problems include:

* Duplicate datasets
* Missing documentation
* Unknown data owners
* Inconsistent file formats
* Poor data quality
* No transaction protection
* No clear security model
* Difficulty discovering useful data

A data lake does not automatically become a data swamp. The problem occurs when governance, metadata and quality controls are missing.

---

## 14. Strengths of a Data Lake

* Stores almost any type of data
* Suitable for very large volumes
* Relatively low-cost storage
* Good for machine learning and exploration
* Supports batch and streaming data
* Preserves raw historical data
* Flexible for future use cases
* Works well with Spark and distributed processing

## 15. Limitations of a traditional Data Lake

* Data quality may vary
* SQL performance may be inconsistent
* Files can be accidentally overwritten
* Concurrent updates can be difficult
* Governance may be weak
* Schema may not be enforced
* Business users may struggle to use it directly
* BI tools may require additional serving layers

---

# 🟣 Part 3: Lakehouse

## 16. What is a Lakehouse?

A **Lakehouse** is a data architecture that combines:

```text
Data Lake capabilities
        +
Data Warehouse capabilities
        =
Lakehouse
```

It uses low-cost file or object storage but adds features normally associated with data warehouses:

* ACID transactions
* Schema enforcement
* Schema evolution
* Table metadata
* Version history
* Governance
* SQL optimization
* Reliable updates and deletes
* Support for BI and machine learning

Common lakehouse technologies include:

* Delta Lake
* Apache Iceberg
* Apache Hudi
* Databricks Lakehouse
* Microsoft Fabric Lakehouse

---

## 17. Lakehouse architecture

```text
+--------------------------------------------------+
|                  DATA SOURCES                    |
|--------------------------------------------------|
| Databases | APIs | Files | Events | IoT | Logs   |
+-------------------------+------------------------+
                          |
                  Batch and streaming
                          |
                          v
+--------------------------------------------------+
|                  BRONZE LAYER                    |
|--------------------------------------------------|
| Raw data | Original format | Full history        |
+-------------------------+------------------------+
                          |
                     Clean and validate
                          |
                          v
+--------------------------------------------------+
|                  SILVER LAYER                    |
|--------------------------------------------------|
| Cleaned | Deduplicated | Standardized | Joined   |
+-------------------------+------------------------+
                          |
                  Aggregate and model
                          |
                          v
+--------------------------------------------------+
|                   GOLD LAYER                     |
|--------------------------------------------------|
| Business tables | KPIs | Aggregated datasets     |
+-------------------------+------------------------+
                          |
       +------------------+------------------+
       |                  |                  |
       v                  v                  v
+-------------+    +-------------+    +-------------+
| BI and SQL  |    | Data Science|    | ML Systems  |
| Dashboards  |    | Exploration |    | Predictions |
+-------------+    +-------------+    +-------------+
```

---

## 18. Medallion architecture

A lakehouse often uses the **Bronze, Silver and Gold** model.

## Bronze layer

Stores raw data as received.

```text
Source files
     ↓
Bronze
```

Characteristics:

* Minimal transformation
* Original values preserved
* Supports audit and replay
* May contain invalid records
* May contain duplicates

Example:

```text
customer_id | amount   | order_date | status
C101        | "2500"   | 05-08-2026 | completed
C102        | "invalid"| 05-08-2026 | Complete
C101        | "2500"   | 05-08-2026 | completed
```

## Silver layer

Stores cleaned and standardized data.

```text
Bronze
   ↓
Remove duplicates
   ↓
Fix datatypes
   ↓
Handle null values
   ↓
Standardize categories
   ↓
Silver
```

Example:

```text
customer_id | amount  | order_date | status
C101        | 2500.00 | 2026-08-05 | COMPLETED
```

## Gold layer

Stores business-ready data.

```text
Silver
   ↓
Join business datasets
   ↓
Calculate KPIs
   ↓
Aggregate
   ↓
Gold
```

Example:

```text
region | order_month | total_sales | order_count
South  | 2026-08     | 4500000.00  | 1250
North  | 2026-08     | 3800000.00  | 1030
```

---

## 19. What are ACID transactions?

ACID stands for:

### Atomicity

A transaction either completes fully or does not happen.

```text
Update 1 succeeds
Update 2 fails
        ↓
Entire transaction is rolled back
```

### Consistency

Data must remain valid before and after a transaction.

### Isolation

Multiple users can work on the data without corrupting each other’s operations.

### Durability

After a successful commit, the change remains saved.

---

## 20. Why ACID matters in a Lakehouse

Imagine two jobs run simultaneously.

```text
Job A: Update customer records
Job B: Read customer records
```

In a plain file-based lake:

```text
Job A starts replacing files
        ↓
Job B reads during replacement
        ↓
Job B may see incomplete data
```

In a transactional lakehouse:

```text
Job A prepares new version
        ↓
Transaction log records the update
        ↓
Job A commits
        ↓
Readers see one consistent version
```

---

## 21. Transaction log concept

A lakehouse table usually includes data files and metadata describing which files belong to the current table version.

```text
Customer Table
│
├── data/
│   ├── part-0001.parquet
│   ├── part-0002.parquet
│   └── part-0003.parquet
│
└── transaction-log/
    ├── version-0001
    ├── version-0002
    └── version-0003
```

The transaction log can record:

* Files added
* Files removed
* Table schema
* Commit time
* Operation type
* Table version

This enables reliable operations such as:

```sql
INSERT
UPDATE
DELETE
MERGE
```

---

## 22. Time travel

Many lakehouse table formats allow users to query an earlier version of a table.

```text
Version 1 ── Version 2 ── Version 3 ── Version 4
   |             |             |             |
 Monday        Tuesday       Wednesday      Today
```

A user may query the Wednesday version even though Thursday’s data is now active.

Typical use cases:

* Recovering accidentally deleted records
* Auditing changes
* Reproducing an old report
* Debugging a pipeline
* Comparing table versions
* Training an ML model with a historical snapshot

---

# 🟠 23. Direct Comparison

| Feature           | Data Warehouse             | Data Lake                                    | Lakehouse                            |
| ----------------- | -------------------------- | -------------------------------------------- | ------------------------------------ |
| Primary purpose   | BI and reporting           | Raw data storage and exploration             | BI, data engineering and ML          |
| Data type         | Mainly structured          | Structured, semi-structured and unstructured | All major data types                 |
| Data state        | Cleaned and transformed    | Raw or lightly processed                     | Raw through business-ready           |
| Schema approach   | Schema-on-write            | Schema-on-read                               | Both                                 |
| Storage           | Warehouse-managed storage  | Object or distributed file storage           | Object storage with table format     |
| SQL performance   | Usually excellent          | Depends on tools and file design             | Warehouse-like performance           |
| ACID transactions | Yes                        | Usually limited in traditional lakes         | Yes                                  |
| Update and delete | Native                     | Difficult with plain files                   | Supported                            |
| Governance        | Strong                     | Can be difficult                             | Strong when properly implemented     |
| Machine learning  | Possible, but not primary  | Very suitable                                | Very suitable                        |
| BI dashboards     | Excellent                  | Often needs extra processing                 | Excellent                            |
| Cost              | Can be relatively high     | Usually lower storage cost                   | Balanced storage and processing cost |
| Data preparation  | Required before loading    | Can happen later                             | Supports progressive refinement      |
| Typical users     | BI developers and analysts | Engineers and data scientists                | Analysts, engineers and scientists   |

---

# 🟠 24. Restaurant Analogy

## Data Warehouse: Restaurant dining area

A restaurant dining area is prepared and organized.

```text
Raw ingredients
      ↓
Washed and prepared
      ↓
Cooked according to recipe
      ↓
Served neatly on a plate
```

The customer receives only the final, prepared result.

Similarly:

```text
Raw business data
      ↓
Cleaned and transformed
      ↓
Organized into tables
      ↓
Presented through reports
```

## Data Lake: Restaurant storage facility

The storage area contains many kinds of items:

* Vegetables
* Rice
* Frozen food
* Bottles
* Packaging materials
* Cleaning supplies

The materials are available for many future recipes, but they are not immediately ready to serve.

## Lakehouse: Organized storage plus restaurant kitchen

The lakehouse keeps the large storage capacity but adds:

* Inventory control
* Quality checks
* Labels
* Preparation areas
* Standard recipes
* Serving counters

It supports both raw material storage and reliable final delivery.

---

# 🟠 25. Library Analogy

## Data Warehouse

A curated reference section:

* Books are approved
* Categories are fixed
* Catalog information is accurate
* Users can quickly find trusted information

## Data Lake

A large collection room:

* Books
* Notes
* Audio recordings
* Photographs
* Unclassified documents
* Research materials

It provides flexibility but needs proper cataloging.

## Lakehouse

A digital library that stores everything while also offering:

* Cataloging
* Version control
* Access policies
* Search
* Verified collections
* Research workspaces

---

# 🟠 26. Example: E-commerce Company

An e-commerce company collects:

```text
Orders from MySQL
Customer details from CRM
Product information from ERP
Website clickstream events
Mobile app JSON events
Product images
Customer support recordings
Delivery GPS events
```

## Using only a Data Warehouse

```text
MySQL Orders ──┐
CRM Customers ─┼─> ETL ─> Warehouse ─> Dashboard
ERP Products ──┘
```

This works well for:

* Monthly sales
* Revenue by category
* Customer reports
* Inventory dashboards

But product images, audio recordings and detailed clickstream events may be difficult or expensive to manage directly.

## Using a Data Lake

```text
Orders ──────────┐
CRM Data ────────┤
Clickstream ─────┤
Images ──────────┼─> Data Lake
Audio ───────────┤
GPS Events ──────┘
```

This supports:

* Machine learning
* Customer behavior exploration
* Recommendation systems
* Image classification
* Delivery route analysis

But business dashboards may require extra cleaned datasets and query engines.

## Using a Lakehouse

```text
All sources
    ↓
Bronze raw layer
    ↓
Silver cleaned layer
    ↓
Gold business layer
    ↓
+----------------------+-----------------------+
|                      |                       |
BI dashboards      Data science          Machine learning
```

The same platform can support:

* Revenue dashboards
* Customer segmentation
* Recommendation models
* Fraud detection
* Operational reporting
* Historical auditing

---

# 🟠 27. Example Data Flow

## Source records

```text
order_id,customer_id,amount,status,order_date
O101,C101,2500,completed,05-08-2026
O102,C102,invalid,complete,05-08-2026
O103,C103,1750,COMPLETED,2026/08/05
O101,C101,2500,completed,05-08-2026
```

## Warehouse approach

The records are corrected before they enter the warehouse:

```text
Raw source
   ↓
Validate amount
   ↓
Standardize status
   ↓
Convert date
   ↓
Remove duplicates
   ↓
Load warehouse
```

Invalid records may be rejected into an error table.

## Data Lake approach

The original file is stored immediately:

```text
data-lake/raw/orders/2026/08/05/orders.csv
```

Later, Spark or another engine reads and transforms it.

## Lakehouse approach

```text
Bronze:
Preserve all four source rows

Silver:
Remove duplicate O101
Correct status values
Convert amount to decimal
Convert dates to DATE
Quarantine invalid O102

Gold:
Calculate daily completed sales
```

Gold output:

```text
order_date | completed_orders | total_sales
2026-08-05 | 2                | 4250.00
```

---

# 🟠 28. ETL versus ELT

## Traditional Data Warehouse: ETL

ETL means:

```text
Extract
   ↓
Transform
   ↓
Load
```

```text
Source → Transformation Server → Warehouse
```

Data is cleaned before it enters the destination.

## Data Lake and modern Lakehouse: ELT

ELT means:

```text
Extract
   ↓
Load
   ↓
Transform
```

```text
Source → Raw storage → Transform inside platform
```

The raw data is preserved, and different transformations can be applied later.

A lakehouse often supports both ETL and ELT.

---

# 🟠 29. Batch and Streaming Support

## Batch processing

Data is processed at intervals.

```text
Every night at 12:00 AM
        ↓
Read yesterday’s orders
        ↓
Transform records
        ↓
Update reporting tables
```

Suitable for:

* Daily reports
* Payroll
* Monthly billing
* Historical analysis

## Streaming processing

Data is processed continuously or with very low latency.

```text
Customer places order
        ↓
Event enters Kafka or Pub/Sub
        ↓
Streaming engine processes event
        ↓
Lakehouse table is updated
        ↓
Dashboard reflects recent data
```

Traditional data warehouses increasingly support streaming, but lakehouse architectures are commonly designed to combine batch and streaming pipelines.

---

# 🟠 30. Who Typically Uses Each System?

## Data Warehouse users

* Business analysts
* BI developers
* Finance teams
* Reporting teams
* Business managers
* SQL analysts

## Data Lake users

* Data engineers
* Data scientists
* Machine learning engineers
* Researchers
* Advanced analysts

## Lakehouse users

* Data engineers
* BI analysts
* SQL developers
* Data scientists
* Machine learning engineers
* Governance teams

---

# 🟠 31. Which One Should You Choose?

## Choose a Data Warehouse when:

* Reporting is the main requirement
* Most data is structured
* Business users mainly use SQL
* Data quality must be strictly controlled
* Dashboards require predictable performance
* The organization already has mature ETL pipelines

Example:

```text
A financial company needs certified monthly reports
for revenue, expenses, tax and regulatory compliance.
```

## Choose a Data Lake when:

* You need to store very large amounts of raw data
* Data comes in many formats
* Future use cases are not yet known
* Machine learning is important
* Storage cost is a major concern
* Engineers need access to original datasets

Example:

```text
An IoT company receives billions of sensor readings,
device logs, images and maintenance documents.
```

## Choose a Lakehouse when:

* Both BI and machine learning are important
* You want open file-based storage
* You need updates, deletes and transactions
* Batch and streaming must work together
* Multiple teams need one governed data platform
* You want Bronze, Silver and Gold processing layers

Example:

```text
An e-commerce organization needs dashboards,
customer recommendations, fraud detection,
clickstream analytics and historical data recovery.
```

---

# 🟠 32. Can an Organization Use All Three?

Yes. Real organizations frequently use a combination.

```text
                    +------------------+
Operational Data -->|     Data Lake    |
                    | Raw information  |
                    +--------+---------+
                             |
                       Process and clean
                             |
                    +--------v---------+
                    |    Lakehouse     |
                    | Governed tables  |
                    +--------+---------+
                             |
                      Publish selected data
                             |
                    +--------v---------+
                    | Data Warehouse   |
                    | Certified BI     |
                    +--------+---------+
                             |
                         Dashboards
```

For example:

* The lake stores all raw records.
* The lakehouse performs engineering and machine learning.
* The warehouse serves certified finance dashboards.

The choice is not always “one versus the others.” It can be a layered enterprise architecture.

---

# 🟠 33. Important Misconception

A lakehouse is not simply:

```text
Data Lake + SQL tool
```

A proper lakehouse should provide several warehouse-like capabilities on top of lake storage:

```text
Object storage
      +
Table format
      +
Transaction log
      +
Metadata catalog
      +
Schema management
      +
Security and governance
      +
Query and processing engines
```

Without these controls, the environment may still be only a collection of files.

---

# 🟠 34. Simplified Technology Mapping

```text
DATA SOURCES
MySQL | SQL Server | APIs | Kafka | Files | IoT
                    |
                    v
INGESTION
Airflow | Kafka | Pub/Sub | Data Factory | Glue
                    |
                    v
STORAGE
S3 | ADLS | Google Cloud Storage
                    |
                    v
TABLE FORMAT
Delta Lake | Apache Iceberg | Apache Hudi
                    |
                    v
PROCESSING
Spark | Databricks | Flink | Trino
                    |
                    v
SERVING
Power BI | Tableau | Looker | SQL Applications
```

A complete lakehouse usually consists of several components working together.

---

# 🟠 35. Interview Questions and Answers

## 1. What is the main difference between a warehouse and a lake?

A warehouse mainly stores cleaned and structured data for reporting. A lake stores raw structured, semi-structured and unstructured data for flexible processing.

## 2. What is schema-on-write?

The schema is defined and enforced before data is written. This is commonly associated with data warehouses.

## 3. What is schema-on-read?

The data is stored first, and its structure is applied when it is read. This is commonly associated with data lakes.

## 4. What is a lakehouse?

A lakehouse combines low-cost and flexible data-lake storage with warehouse features such as ACID transactions, schemas, governance and SQL performance.

## 5. What is a data swamp?

A data lake that lacks proper metadata, organization, ownership, quality and governance is often called a data swamp.

## 6. What is the Medallion architecture?

It is a layered data design:

```text
Bronze → Raw data
Silver → Cleaned and standardized data
Gold   → Business-ready data
```

## 7. Why are ACID transactions important?

They prevent partial or conflicting changes and ensure readers see consistent data.

## 8. Can a data lake store structured data?

Yes. It can store structured, semi-structured and unstructured data.

## 9. Can a data warehouse support machine learning?

Yes, but traditional warehouses are mainly optimized for SQL analytics and BI. A lake or lakehouse may provide greater flexibility for large-scale ML workloads.

## 10. Is a lakehouse always cheaper than a warehouse?

Not automatically. Cost depends on storage, query volume, compute usage, data design, optimization and platform pricing.

## 11. What is time travel?

Time travel allows users to query or restore an earlier version of a table.

## 12. What is the difference between ETL and ELT?

```text
ETL: Extract → Transform → Load
ELT: Extract → Load → Transform
```

## 13. Why use Parquet in a lake or lakehouse?

Parquet is a columnar format that provides:

* Compression
* Faster analytical queries
* Column pruning
* Efficient distributed processing
* Schema information

## 14. Does a Lakehouse replace a Data Warehouse?

It can replace some warehouse workloads, but many organizations still maintain warehouses for specialized reporting, predictable performance or established governance processes.

---

# 🟠 36. Final Memory Diagram

```text
DATA WAREHOUSE
--------------
Clean first, store later
Structured tables
Best known for BI and SQL

        Schema-on-write
Source ----------------> Warehouse


DATA LAKE
---------
Store first, understand later
All types of data
Best known for scale and flexibility

        Schema-on-read
Source ----------------> Raw files


LAKEHOUSE
---------
Store flexibly, manage reliably
All types of data
Supports BI, engineering and ML

Data Lake Storage
       +
ACID Tables
       +
Governance
       +
SQL and ML
```

## One-line conclusion

```text
Warehouse = trusted business reporting

Lake = flexible raw data storage

Lakehouse = lake flexibility with warehouse reliability
```
