# Week 2 PySpark and Spark SQL Interview Questions and Answers

## Topics Covered

- Spark SQL
- SparkSession and SparkContext
- SQLContext and HiveContext
- DataFrames and Datasets
- JSON datasets
- Selecting and filtering data
- Aggregate functions
- Joins
- Set operations
- Adding and removing columns
- Sorting and partitioning
- Bucketing
- Caching
- BigQuery partition pruning, clustering and execution model
- Scenario-based questions
- Code-based questions
- Rapid-fire questions

---

# 1. Spark SQL Fundamentals

## Q1. What is Spark SQL?

### Interview Answer

Spark SQL is a Spark module used to process structured and semi-structured data. It allows developers to work with SQL queries, the DataFrame API, and the Dataset API in Scala and Java.

Spark SQL uses the Catalyst Optimizer to optimize queries and the Tungsten execution engine to improve memory and CPU efficiency.

### Real-World Example

A food-delivery company stores millions of orders in Parquet files. Spark SQL can read the files, filter completed orders, calculate city-wise revenue, and write the result back to Cloud Storage.

```python
orders_df = spark.read.parquet("gs://bucket/orders/")

orders_df.createOrReplaceTempView("orders")

spark.sql("""
    SELECT city, SUM(order_amount) AS revenue
    FROM orders
    WHERE status = 'Completed'
    GROUP BY city
""").show()
```

## Q2. What are the advantages of Spark SQL?

Spark SQL provides schema-based processing, SQL and DataFrame APIs, query optimization, support for CSV/JSON/Parquet/ORC/JDBC, Hive integration, and distributed joins and aggregations.

## Q3. Can Spark SQL process only SQL tables?

No. Spark SQL can process DataFrames, temporary views, Hive tables, CSV, JSON, Parquet, JDBC sources, and cloud-storage data.

---

# 2. SparkSession, SparkContext, SQLContext and HiveContext

## Q4. What is SparkSession?

`SparkSession` is the main entry point for Spark SQL, DataFrames, and structured data.

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("FoodDeliveryAnalytics")
    .getOrCreate()
)
```

## Q5. What happens when `getOrCreate()` is called?

If a SparkSession already exists, it returns it. Otherwise, it creates a new SparkSession and the underlying SparkContext.

## Q6. What is SparkContext?

`SparkContext` connects the application to the cluster manager. It requests executors, creates RDDs, schedules jobs, sends tasks, and manages broadcast variables and accumulators.

```python
sc = spark.sparkContext
print(sc.appName)
print(sc.master)
```

## Q7. SparkSession vs SparkContext?

| SparkSession | SparkContext |
|---|---|
| Entry point for DataFrames and Spark SQL | Entry point for Spark Core and RDDs |
| Modern API | Low-level core API |
| Creates DataFrames | Creates RDDs |
| Accessed using `spark` | Accessed using `spark.sparkContext` |

## Q8. What is SQLContext?

`SQLContext` was the original entry point for Spark SQL before Spark 2.0. Modern applications use SparkSession.

```python
sql_context = spark.sqlContext
```

## Q9. What is HiveContext?

`HiveContext` extended SQLContext with HiveQL, Hive metastore, Hive UDF, and Hive table support.

```python
spark = (
    SparkSession.builder
    .appName("HiveDemo")
    .enableHiveSupport()
    .getOrCreate()
)
```

## Q10. SQLContext vs HiveContext?

| SQLContext | HiveContext |
|---|---|
| Basic Spark SQL | Spark SQL plus Hive support |
| No Hive metastore by default | Supports Hive metastore |
| Replaced by SparkSession | Replaced by SparkSession with Hive support |

---

# 3. DataFrames and Datasets

## Q11. What is a DataFrame?

A DataFrame is a distributed collection of rows organized into named columns.

```python
data = [
    (1, "Mumbai", 800.0),
    (2, "Pune", 500.0),
    (3, "Chennai", 700.0),
]
columns = ["order_id", "city", "order_amount"]
orders_df = spark.createDataFrame(data, columns)
orders_df.show()
```

## Q12. Why are DataFrames generally preferred over RDDs?

They provide schemas, Catalyst optimization, Tungsten execution improvements, efficient memory representation, easier SQL-like operations, and better structured-data integration.

## Q13. Are DataFrames mutable?

No. Every transformation creates a new DataFrame.

```python
filtered_df = orders_df.filter(orders_df.order_amount > 500)
```

## Q14. What is a Dataset?

A Dataset is a strongly typed distributed collection available mainly in Scala and Java. PySpark primarily uses DataFrames.

## Q15. DataFrame vs Dataset?

| DataFrame | Dataset |
|---|---|
| Untyped rows | Strongly typed objects |
| Available in Python, Scala, Java, R | Mainly Scala and Java |
| Runtime schema checks | Some compile-time checks |

---

# 4. Reading Data

## Q16. How do you read a CSV file in PySpark?

```python
orders_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("orders.csv")
)
```

## Q17. Why should `inferSchema` be avoided in production?

It requires an extra scan and can infer incorrect types. An explicit schema is faster, predictable, and easier to validate.

## Q18. How do you provide an explicit schema?

```python
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType

order_schema = StructType([
    StructField("order_id", IntegerType(), False),
    StructField("city", StringType(), True),
    StructField("status", StringType(), True),
    StructField("order_amount", DoubleType(), True),
])

orders_df = (
    spark.read
    .option("header", True)
    .schema(order_schema)
    .csv("orders.csv")
)
```

## Q19. How do you read JSON data?

```python
json_df = spark.read.json("orders.json")
```

For multiline JSON:

```python
json_df = (
    spark.read
    .option("multiline", True)
    .json("orders.json")
)
```

## Q20. Normal JSON vs multiline JSON?

Normal JSON expects one complete JSON object per line. Multiline JSON may contain arrays or formatted objects spanning several lines.

## Q21. CSV vs JSON vs Parquet?

| CSV | JSON | Parquet |
|---|---|---|
| Row-based text | Semi-structured text | Columnar binary |
| No built-in schema | Supports nesting | Stores schema |
| Larger and slower | Human-readable | Compressed and analytics-friendly |

---

# 5. Selecting and Filtering Data

## Q22. How do you select columns?

```python
orders_df.select("order_id", "city", "order_amount").show()
```

## Q23. Why is `F.col()` useful?

It creates column expressions that support aliases, arithmetic, comparisons, functions, and dynamic references.

```python
from pyspark.sql import functions as F
orders_df.select(F.col("order_amount").alias("amount"))
```

## Q24. `filter()` vs `where()`?

They are functionally equivalent.

```python
orders_df.filter(F.col("status") == "Completed")
orders_df.where(F.col("status") == "Completed")
```

## Q25. How do you apply multiple filter conditions?

```python
completed_high_value_df = orders_df.filter(
    (F.col("status") == "Completed") &
    (F.col("order_amount") > 500)
)
```

Use `&` for AND, `|` for OR, and `~` for NOT.

## Q26. How do you check for null values?

```python
orders_df.filter(F.col("city").isNull()).show()
orders_df.filter(F.col("city").isNotNull()).show()
```

## Q27. Find orders from Mumbai or Pune with an amount above $500.

```python
result_df = orders_df.filter(
    (F.col("city").isin("Mumbai", "Pune")) &
    (F.col("order_amount") > 500)
)
result_df.show()
```

---

# 6. DataFrame Operations

## Q28. How do you add a new column?

```python
orders_df = orders_df.withColumn(
    "tax_amount",
    F.col("order_amount") * 0.05
)
```

## Q29. How do you update an existing column?

```python
orders_df = orders_df.withColumn(
    "city",
    F.upper(F.col("city"))
)
```

## Q30. How do you rename a column?

```python
renamed_df = orders_df.withColumnRenamed("order_amount", "amount")
```

## Q31. How do you remove columns?

```python
clean_df = orders_df.drop("temporary_column", "raw_timestamp")
```

## Q32. How do you remove duplicate rows?

```python
unique_df = orders_df.distinct()
unique_by_order = orders_df.dropDuplicates(["order_id"])
```

## Q33. `distinct()` vs `dropDuplicates()`?

`distinct()` compares every column. `dropDuplicates()` can compare selected columns.

---

# 7. Aggregate Functions

## Q34. What does `groupBy()` do?

It groups rows with the same key so aggregate functions can be applied.

```python
orders_df.groupBy("city").count().show()
```

## Q35. How do you calculate city-wise order count, revenue, and average?

```python
city_summary_df = (
    orders_df
    .groupBy("city")
    .agg(
        F.count("*").alias("order_count"),
        F.sum("order_amount").alias("total_revenue"),
        F.round(F.avg("order_amount"), 2).alias("average_order_value")
    )
)
city_summary_df.show()
```

## Q36. Common aggregate functions

`count`, `countDistinct`, `sum`, `avg`, `min`, `max`, `collect_list`, `collect_set`, `first`, and `last`.

## Q37. `collect_list()` vs `collect_set()`?

`collect_list()` retains duplicates. `collect_set()` removes duplicates.

## Q38. Find total revenue only for completed orders.

```python
completed_revenue_df = (
    orders_df
    .filter(F.col("status") == "Completed")
    .agg(F.sum("order_amount").alias("completed_revenue"))
)
completed_revenue_df.show()
```

---

# 8. Joins

## Q39. What is an inner join?

Returns only matching rows from both DataFrames.

```python
joined_df = customers_df.join(orders_df, on="customer_id", how="inner")
```

## Q40. What is a left join?

Returns all left-side rows and matching right-side rows.

```python
customers_df.join(orders_df, on="customer_id", how="left")
```

## Q41. What is a left anti join?

Returns left-side rows with no match on the right.

```python
customers_without_orders_df = customers_df.join(
    orders_df,
    on="customer_id",
    how="left_anti"
)
```

## Q42. What is a left semi join?

Returns left-side rows that have at least one right-side match, without right-side columns.

```python
customers_with_orders_df = customers_df.join(
    orders_df,
    on="customer_id",
    how="left_semi"
)
```

## Q43. What join types does Spark support?

Inner, left, right, full outer, left semi, left anti, and cross join.

## Q44. How do you handle duplicate column names after a join?

Use aliases and explicit selection.

```python
c = customers_df.alias("c")
o = orders_df.alias("o")

result_df = (
    c.join(o, F.col("c.customer_id") == F.col("o.customer_id"), "inner")
    .select(
        F.col("c.customer_id"),
        F.col("c.customer_name"),
        F.col("o.order_id"),
        F.col("o.amount")
    )
)
```

## Q45. Find orders whose customer record is missing.

```python
invalid_orders_df = orders_df.join(
    customers_df,
    on="customer_id",
    how="left_anti"
)
```

## Q46. What is a broadcast join?

A broadcast join sends a small DataFrame to every executor to avoid a large shuffle.

```python
result_df = large_orders_df.join(
    F.broadcast(small_city_lookup_df),
    on="city_code",
    how="left"
)
```

---

# 9. Set Operations

## Q47. Supported set operations

`union`, `unionByName`, `intersect`, `exceptAll`, and `subtract`.

## Q48. What does `union()` do?

It combines rows from two DataFrames and does not remove duplicates.

```python
combined_df = january_df.union(february_df)
```

## Q49. `union()` vs `unionByName()`?

`union()` matches columns by position. `unionByName()` matches them by name.

```python
combined_df = df1.unionByName(df2)
```

## Q50. How do you union DataFrames with missing columns?

```python
combined_df = df1.unionByName(df2, allowMissingColumns=True)
```

## Q51. What does `intersect()` do?

Returns rows common to both DataFrames.

```python
common_df = source_df.intersect(target_df)
```

## Q52. What does `exceptAll()` do?

Returns rows present in the first DataFrame but not in the second while preserving duplicate differences.

```python
missing_df = source_df.exceptAll(target_df)
```

---

# 10. Sorting and Partitioning

## Q53. How do you sort a DataFrame?

```python
sorted_df = orders_df.orderBy(F.col("order_amount").desc())
```

## Q54. `sort()` vs `orderBy()`?

They are aliases for global sorting in the DataFrame API.

## Q55. What is a partition in Spark?

A partition is a logical subset of distributed data. A Spark task generally processes one partition.

## Q56. How do you inspect the number of partitions?

```python
print(orders_df.rdd.getNumPartitions())
```

## Q57. What is `repartition()`?

It increases or decreases partitions using a full shuffle.

```python
repartitioned_df = orders_df.repartition(8, "city")
```

## Q58. What is `coalesce()`?

It normally reduces partitions with less data movement.

```python
small_output_df = orders_df.coalesce(2)
```

## Q59. `repartition()` vs `coalesce()`?

| repartition | coalesce |
|---|---|
| Increase or decrease | Usually decrease |
| Full shuffle | Avoids full shuffle where possible |
| Better balancing | May be uneven |

## Q60. Spark writes 200 small CSV files. What would you do?

```python
(
    result_df
    .coalesce(4)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv("output/")
)
```

---

# 11. Bucketing

## Q61. What is bucketing?

Bucketing distributes rows into a fixed number of files based on the hash of a bucket column.

```python
(
    customer_df.write
    .bucketBy(16, "customer_id")
    .sortBy("customer_id")
    .mode("overwrite")
    .saveAsTable("bucketed_customers")
)
```

## Q62. Partitioning vs bucketing?

| Partitioning | Bucketing |
|---|---|
| Creates folders by column value | Creates fixed files using hash |
| Good for low-cardinality columns | Useful for high-cardinality keys |
| Supports partition pruning | Can improve repeated joins |

## Q63. Real-world bucketing scenario

If customer and transaction tables are repeatedly joined by `customer_id`, bucketing both tables by the same key and bucket count may reduce shuffle.

## Q64. Is bucketing always faster?

No. It helps only when table metadata is preserved, bucket keys and counts are compatible, and the workload frequently joins or aggregates by that key.

---

# 12. Spark Caching

## Q65. What is caching?

Caching stores a DataFrame or RDD so Spark can reuse it without recomputing its full lineage.

```python
orders_df.cache()
orders_df.count()
```

## Q66. Why is an action needed after `cache()`?

Because caching is lazy. Data is stored only after an action executes.

## Q67. When should you cache data?

Cache when the same expensive DataFrame is reused multiple times and fits the selected storage level.

## Q68. `cache()` vs `persist()`?

`cache()` uses the default persistence level. `persist()` allows a specific storage level.

```python
from pyspark import StorageLevel
orders_df.persist(StorageLevel.MEMORY_AND_DISK)
```

## Q69. How do you remove cached data?

```python
orders_df.unpersist()
spark.catalog.clearCache()
```

## Q70. A DataFrame is used for five reports. What should you do?

```python
clean_orders_df = (
    raw_orders_df
    .filter(F.col("order_id").isNotNull())
    .dropDuplicates(["order_id"])
)

clean_orders_df.cache()
clean_orders_df.count()

city_report_df = clean_orders_df.groupBy("city").count()
status_report_df = clean_orders_df.groupBy("status").count()
payment_report_df = clean_orders_df.groupBy("payment_type").count()

clean_orders_df.unpersist()
```

---

# 13. BigQuery and Spark SQL Comparison

## Q71. What is partition pruning in BigQuery?

BigQuery scans only matching partitions when a filter is applied on the partition column.

```sql
SELECT *
FROM orders
WHERE order_date = '2026-07-27';
```

## Q72. How is partition pruning similar in Spark?

Spark can skip unrelated partition folders when filtering by the partition column.

```python
orders_df = spark.read.parquet("gs://bucket/orders/")
filtered_df = orders_df.filter(F.col("order_date") == "2026-07-27")
```

## Q73. What is clustering in BigQuery?

Clustering organizes storage blocks based on selected columns.

```sql
CREATE TABLE order_dataset.orders
PARTITION BY order_date
CLUSTER BY city, customer_id AS
SELECT * FROM source_orders;
```

## Q74. BigQuery clustering vs Spark bucketing?

BigQuery clustering organizes storage blocks. Spark bucketing hashes rows into a fixed number of files.

## Q75. Spark executor model vs BigQuery slot model?

| Spark | BigQuery |
|---|---|
| Driver coordinates executors | Service coordinates slots |
| Cluster resources are configured | Infrastructure is managed by Google |
| Executors have CPU and memory | Slots represent compute capacity |

## Q76. BigQuery on-demand vs reserved capacity?

On-demand charges by data processed. Reserved capacity allocates predictable compute slots for regular workloads.

## Q77. When would you choose BigQuery over Spark SQL?

Choose BigQuery for serverless SQL analytics and BI. Choose Spark for complex ETL, multi-source processing, custom Python logic, and combined batch/streaming workloads.

---

# Small Scenario-Based Questions

## Scenario 1: Remove duplicate orders

```python
clean_df = orders_df.dropDuplicates(["order_id"])
```

## Scenario 2: Find invalid negative amounts

```python
invalid_df = orders_df.filter(F.col("order_amount") <= 0)
```

## Scenario 3: Replace null city values

```python
clean_df = orders_df.fillna({"city": "Unknown"})
```

## Scenario 4: Add order category

```python
categorized_df = orders_df.withColumn(
    "order_category",
    F.when(F.col("order_amount") >= 1000, "High")
     .when(F.col("order_amount") >= 500, "Medium")
     .otherwise("Low")
)
```

## Scenario 5: Find the highest-value order in each city

```python
from pyspark.sql.window import Window

city_window = (
    Window
    .partitionBy("city")
    .orderBy(F.col("order_amount").desc())
)

result_df = (
    orders_df
    .withColumn("row_number", F.row_number().over(city_window))
    .filter(F.col("row_number") == 1)
    .drop("row_number")
)
```

## Scenario 6: Find cities having revenue above $2,000

```python
result_df = (
    orders_df
    .groupBy("city")
    .agg(F.sum("order_amount").alias("revenue"))
    .filter(F.col("revenue") > 2000)
)
```

## Scenario 7: Find customers without orders

```python
customers_without_orders_df = customers_df.join(
    orders_df,
    on="customer_id",
    how="left_anti"
)
```

## Scenario 8: Combine monthly files with different column order

```python
combined_df = january_df.unionByName(february_df)
```

## Scenario 9: Join a 100-row lookup table

```python
result_df = orders_df.join(
    F.broadcast(city_lookup_df),
    on="city_code",
    how="left"
)
```

## Scenario 10: Reuse a cleaned DataFrame repeatedly

```python
clean_df.cache()
clean_df.count()
# Multiple reports
clean_df.unpersist()
```

---

# Code-Based Interview Questions

## Code Question 1

What is wrong with this code?

```python
orders_df.filter(
    orders_df.status == "Completed"
    and orders_df.order_amount > 500
)
```

### Answer

Python `and` cannot be used for Spark column expressions.

```python
orders_df.filter(
    (F.col("status") == "Completed") &
    (F.col("order_amount") > 500)
)
```

## Code Question 2

What happens here?

```python
new_df = orders_df.withColumn("city", F.upper("city"))
```

The `city` column is replaced in `new_df`. The original DataFrame remains unchanged.

## Code Question 3

Which is safer?

```python
df1.union(df2)
```

or

```python
df1.unionByName(df2)
```

`unionByName()` is safer when column order may differ.

## Code Question 4

Why might this be dangerous?

```python
orders = orders_df.collect()
```

It sends every row to the driver and can cause out-of-memory failure.

## Code Question 5

What is wrong with caching here?

```python
orders_df.cache()
orders_df.write.parquet("output/")
```

Caching provides little benefit when the DataFrame is used only once.

## Code Question 6

What is the expected result?

```python
df = spark.createDataFrame(
    [("Mumbai", 100), ("Mumbai", 200), ("Pune", 300)],
    ["city", "amount"]
)
df.groupBy("city").sum("amount").show()
```

```text
+-------+-----------+
|city   |sum(amount)|
+-------+-----------+
|Mumbai |300        |
|Pune   |300        |
+-------+-----------+
```

## Code Question 7

Return the top three orders by amount.

```python
top_three_df = orders_df.orderBy(
    F.col("order_amount").desc()
).limit(3)
```

## Code Question 8

Count completed and cancelled orders by city.

```python
summary_df = (
    orders_df
    .groupBy("city", "status")
    .agg(F.count("*").alias("order_count"))
)
```

---

# Frequently Asked Rapid-Fire Questions

1. **Is SparkSession created on the driver?** Yes.
2. **Are DataFrames mutable?** No.
3. **Does `filter()` trigger execution?** No.
4. **Does `show()` trigger execution?** Yes.
5. **Does `union()` remove duplicates?** No.
6. **Which join finds missing left-side records?** Left anti join.
7. **Which file format is commonly preferred for analytics?** Parquet.
8. **Which normally causes shuffle: `filter()` or `groupBy()`?** `groupBy()`.
9. **Which normally reduces partitions without full shuffle?** `coalesce()`.
10. **Does `cache()` immediately store data?** No.
11. **Can PySpark use typed Datasets like Scala?** No.
12. **Which component optimizes DataFrame queries?** Catalyst Optimizer.
13. **Why use a broadcast join?** To reduce shuffle when joining with a small table.
14. **Which BigQuery feature skips irrelevant partitions?** Partition pruning.
15. **What represents compute capacity in BigQuery?** Slots.
