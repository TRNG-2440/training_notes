# Databricks notebook source
# MAGIC # Current Databricks Free Edition — DataFrame Alternative
# MAGIC 
# MAGIC Free Edition is serverless-only and does not support SparkContext or RDD APIs. This notebook implements the same business pipeline with DataFrames, a Unity Catalog Volume and managed tables.

# COMMAND ----------

# MAGIC ## 1 — Import DataFrame functions

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC ## 2 — Create a managed Volume for file loading and saving

# COMMAND ----------

CATALOG=spark.sql("SELECT current_catalog() AS c").first()["c"]
SCHEMA="default";VOLUME="retail_data_loading_demo"
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.`{VOLUME}`")
BASE=f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}";RAW_PATH=f"{BASE}/raw_orders";REPORT_PATH=f"{BASE}/category_report"
print(BASE)

# COMMAND ----------

# MAGIC ## 3 — Create source DataFrames
# MAGIC 
# MAGIC This is the serverless replacement for `sc.parallelize`.

# COMMAND ----------

orders=[(1001, '2026-07-01', 'C101', 'Coimbatore', 'Electronics', 2, 25000.0, 5.0, 'COMPLETED'), (1002, '2026-07-01', 'C102', 'Chennai', 'Grocery', 10, 120.0, 0.0, 'COMPLETED'), (1003, '2026-07-01', 'C103', 'Bengaluru', 'Fashion', 3, 1800.0, 10.0, 'COMPLETED'), (1004, '2026-07-02', 'C104', 'Coimbatore', 'Grocery', 5, 250.0, 0.0, 'CANCELLED'), (1005, '2026-07-02', 'C105', 'Chennai', 'Electronics', 1, 62000.0, 8.0, 'COMPLETED'), (1006, '2026-07-02', 'C106', 'Hyderabad', 'Fashion', 4, 2200.0, 15.0, 'COMPLETED'), (1007, '2026-07-03', 'C107', 'Bengaluru', 'Grocery', 20, 95.0, 2.0, 'COMPLETED'), (1008, '2026-07-03', 'C108', 'Hyderabad', 'Electronics', 2, 18000.0, 5.0, 'RETURNED'), (1009, '2026-07-03', 'C109', 'Coimbatore', 'Fashion', 5, 1400.0, 0.0, 'COMPLETED'), (1010, '2026-07-04', 'C110', 'Chennai', 'Grocery', 12, 150.0, 5.0, 'COMPLETED'), (1011, '2026-07-04', 'C111', 'Bengaluru', 'Electronics', 1, 45000.0, 12.0, 'COMPLETED'), (1012, '2026-07-04', 'C112', 'Hyderabad', 'Grocery', 8, 210.0, 0.0, 'COMPLETED'), (1013, '2026-07-05', 'C113', '', 'Fashion', -2, 1500.0, 0.0, 'COMPLETED'), (1014, '2026-07-05', 'C114', 'Chennai', 'Electronics', 1, 30000.0, 120.0, 'COMPLETED'), (1015, '2026-07-05', 'C115', 'Coimbatore', 'Grocery', 6, 180.0, 10.0, 'COMPLETED'), (1016, '2026-07-06', 'C116', 'Chennai', 'Electronics', 1, 28000.0, 0.0, 'COMPLETED'), (1017, '2026-07-06', 'C117', 'Hyderabad', 'Fashion', 2, 3200.0, 5.0, 'COMPLETED'), (1018, '2026-07-06', 'C118', 'Bengaluru', 'Grocery', 15, 110.0, 0.0, 'COMPLETED'), (1019, '2026-07-07', 'C119', 'Coimbatore', 'Electronics', 3, 12000.0, 10.0, 'COMPLETED'), (1020, '2026-07-07', 'C120', 'Chennai', 'Fashion', 1, 5000.0, 20.0, 'CANCELLED')]
columns=["order_id","order_date","customer_id","city","category","quantity","unit_price","discount_pct","status"]
orders_df=spark.createDataFrame(orders,columns)
master_df=spark.createDataFrame([('Electronics', 'Digital', 'Anita', 200000.0), ('Fashion', 'Lifestyle', 'Rahul', 30000.0), ('Grocery', 'Daily Needs', 'Meena', 10000.0)],["category","department","manager","monthly_target"])
display(orders_df)

# COMMAND ----------

# MAGIC ## 4 — Write and reload CSV through the Volume

# COMMAND ----------

dbutils.fs.rm(RAW_PATH,recurse=True)
orders_df.coalesce(1).write.mode("overwrite").option("header",True).csv(RAW_PATH)
loaded_df=spark.read.option("header",True).option("inferSchema",True).csv(RAW_PATH)
display(loaded_df)

# COMMAND ----------

# MAGIC ## 5 — Clean and classify records

# COMMAND ----------

valid=((F.length(F.trim("city"))>0)&(F.col("quantity")>0)&(F.col("unit_price")>=0)&F.col("discount_pct").between(0,100)&F.col("status").isin("COMPLETED","CANCELLED","RETURNED"))
classified=(loaded_df.withColumn("is_valid",valid).withColumn("gross_amount",F.round(F.col("quantity")*F.col("unit_price"),2)).withColumn("net_amount",F.round(F.col("quantity")*F.col("unit_price")*(1-F.col("discount_pct")/100.0),2)).withColumn("rejection_reason",F.when(F.length(F.trim("city"))==0,"MISSING_CITY").when(F.col("quantity")<=0,"INVALID_QUANTITY").when(~F.col("discount_pct").between(0,100),"INVALID_DISCOUNT").otherwise("VALID")))
clean_df=classified.filter("is_valid");rejected_df=classified.filter("NOT is_valid")
print("Valid",clean_df.count(),"Rejected",rejected_df.count())

# COMMAND ----------

# MAGIC ## 6 — DataFrame equivalent of Pair-RDD aggregation and join

# COMMAND ----------

summary_df=(clean_df.filter(F.col("status")=="COMPLETED").groupBy("category").agg(F.count("*").alias("completed_orders"),F.sum("quantity").alias("units_sold"),F.round(F.sum("net_amount"),2).alias("net_revenue"),F.round(F.avg("net_amount"),2).alias("average_order_value")).join(master_df,"category","inner").withColumn("achievement_pct",F.round(F.col("net_revenue")/F.col("monthly_target")*100,2)).orderBy(F.desc("net_revenue")))
display(summary_df)

# COMMAND ----------

# MAGIC ## 7 — Save managed tables and a CSV report

# COMMAND ----------

CLEAN_TABLE=f"`{CATALOG}`.`default`.`retail_clean_orders_demo`";REJECT_TABLE=f"`{CATALOG}`.`default`.`retail_rejected_orders_demo`";REPORT_TABLE=f"`{CATALOG}`.`default`.`retail_category_report_demo`"
for t in [CLEAN_TABLE,REJECT_TABLE,REPORT_TABLE]:spark.sql(f"DROP TABLE IF EXISTS {t}")
clean_df.write.mode("overwrite").saveAsTable(CLEAN_TABLE);rejected_df.write.mode("overwrite").saveAsTable(REJECT_TABLE);summary_df.write.mode("overwrite").saveAsTable(REPORT_TABLE)
dbutils.fs.rm(REPORT_PATH,recurse=True);summary_df.coalesce(1).write.mode("overwrite").option("header",True).csv(REPORT_PATH)
print(REPORT_TABLE,REPORT_PATH)

# COMMAND ----------

# MAGIC ## 8 — Verify expected results

# COMMAND ----------

expected={"Electronics":204540.0,"Fashion":25420.0,"Grocery":9074.0};actual={r["category"]:float(r["net_revenue"]) for r in summary_df.select("category","net_revenue").collect()};assert actual==expected;print("Verification passed",actual)

# COMMAND ----------

# MAGIC # Conclusion
# MAGIC 
# MAGIC The current Free Edition can run the DataFrame alternative, but not Pair RDD code. Use classic/dedicated compute for the RDD notebook.
