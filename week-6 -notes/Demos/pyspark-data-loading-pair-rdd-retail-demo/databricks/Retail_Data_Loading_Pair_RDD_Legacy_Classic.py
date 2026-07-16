# Databricks notebook source
# MAGIC # Retail Data Loading, Pair RDD and Saving — Legacy/Classic Databricks
# MAGIC 
# MAGIC Requires Spark Classic architecture. It loads CSV from legacy DBFS, creates clean/rejected RDDs, aggregates a Pair RDD, joins category master data, and saves text plus SequenceFile outputs.

# COMMAND ----------

# MAGIC ## 1 — Verify RDD support

# COMMAND ----------

try:
    sc = spark.sparkContext
except Exception as exc:
    raise RuntimeError("Attach classic/dedicated compute; serverless does not support RDDs.") from exc
print(spark.version, sc.master)

# COMMAND ----------

# MAGIC ## 2 — Import parsing and output helpers

# COMMAND ----------

import csv
import itertools
import json

# COMMAND ----------

# MAGIC ## 3 — Create CSV source files in legacy DBFS
# MAGIC 
# MAGIC The notebook embeds the classroom data, so no manual upload is needed.

# COMMAND ----------

BASE="dbfs:/FileStore/retail_pair_rdd_demo"
ORDERS_PATH=f"{BASE}/input/retail_orders.csv"
MASTER_PATH=f"{BASE}/input/category_master.csv"
CLEAN_OUTPUT=f"{BASE}/output/cleaned_orders"
REJECT_OUTPUT=f"{BASE}/output/rejected_orders"
REPORT_OUTPUT=f"{BASE}/output/category_report"
SEQUENCE_OUTPUT=f"{BASE}/output/category_sequence"
orders_csv='order_id,order_date,customer_id,city,category,quantity,unit_price,discount_pct,status\n1001,2026-07-01,C101,Coimbatore,Electronics,2,25000,5,COMPLETED\n1002,2026-07-01,C102,Chennai,Grocery,10,120,0,COMPLETED\n1003,2026-07-01,C103,Bengaluru,Fashion,3,1800,10,COMPLETED\n1004,2026-07-02,C104,Coimbatore,Grocery,5,250,0,CANCELLED\n1005,2026-07-02,C105,Chennai,Electronics,1,62000,8,COMPLETED\n1006,2026-07-02,C106,Hyderabad,Fashion,4,2200,15,COMPLETED\n1007,2026-07-03,C107,Bengaluru,Grocery,20,95,2,COMPLETED\n1008,2026-07-03,C108,Hyderabad,Electronics,2,18000,5,RETURNED\n1009,2026-07-03,C109,Coimbatore,Fashion,5,1400,0,COMPLETED\n1010,2026-07-04,C110,Chennai,Grocery,12,150,5,COMPLETED\n1011,2026-07-04,C111,Bengaluru,Electronics,1,45000,12,COMPLETED\n1012,2026-07-04,C112,Hyderabad,Grocery,8,210,0,COMPLETED\n1013,2026-07-05,C113,,Fashion,-2,1500,0,COMPLETED\n1014,2026-07-05,C114,Chennai,Electronics,1,30000,120,COMPLETED\n1015,2026-07-05,C115,Coimbatore,Grocery,6,180,10,COMPLETED\n1016,2026-07-06,C116,Chennai,Electronics,1,28000,0,COMPLETED\n1017,2026-07-06,C117,Hyderabad,Fashion,2,3200,5,COMPLETED\n1018,2026-07-06,C118,Bengaluru,Grocery,15,110,0,COMPLETED\n1019,2026-07-07,C119,Coimbatore,Electronics,3,12000,10,COMPLETED\n1020,2026-07-07,C120,Chennai,Fashion,1,5000,20,CANCELLED\n'
master_csv='category,department,manager,monthly_target\nElectronics,Digital,Anita,200000\nFashion,Lifestyle,Rahul,30000\nGrocery,Daily Needs,Meena,10000\n'
dbutils.fs.mkdirs(f"{BASE}/input")
dbutils.fs.put(ORDERS_PATH,orders_csv,overwrite=True)
dbutils.fs.put(MASTER_PATH,master_csv,overwrite=True)
print(ORDERS_PATH,MASTER_PATH)

# COMMAND ----------

# MAGIC ## 4 — Load an RDD of strings with textFile

# COMMAND ----------

raw_orders=sc.textFile(ORDERS_PATH,4)
header=raw_orders.first()
print("Rows including header:",raw_orders.count())
print("Partitions:",raw_orders.getNumPartitions())
print(raw_orders.take(2))

# COMMAND ----------

# MAGIC ## 5 — Parse and classify every order
# MAGIC 
# MAGIC `mapPartitions` creates one CSV reader per partition. The resulting RDD is cached because it is reused.

# COMMAND ----------

FIELDS=["order_id","order_date","customer_id","city","category","quantity","unit_price","discount_pct","status"]
def parse_partition(lines):
    for values in csv.reader(lines):
        try:
            r=dict(zip(FIELDS,values));r["order_id"]=int(r["order_id"]);r["quantity"]=int(r["quantity"]);r["unit_price"]=float(r["unit_price"]);r["discount_pct"]=float(r["discount_pct"]);r["city"]=r["city"].strip();r["status"]=r["status"].strip().upper();yield r
        except Exception: yield {"_error":"PARSE_ERROR","_raw":values}
def classify(r):
    if "_error" in r:return {"valid":False,"row":r,"reasons":[r["_error"]]}
    reasons=[]
    if not r["city"]:reasons.append("MISSING_CITY")
    if r["quantity"]<=0:reasons.append("INVALID_QUANTITY")
    if r["unit_price"]<0:reasons.append("INVALID_UNIT_PRICE")
    if not 0<=r["discount_pct"]<=100:reasons.append("INVALID_DISCOUNT")
    if r["status"] not in {"COMPLETED","CANCELLED","RETURNED"}:reasons.append("INVALID_STATUS")
    if reasons:return {"valid":False,"row":r,"reasons":reasons}
    gross=r["quantity"]*r["unit_price"]; clean={**r,"gross_amount":round(gross,2),"net_amount":round(gross*(1-r["discount_pct"]/100),2)}
    return {"valid":True,"row":clean,"reasons":[]}
classified=raw_orders.filter(lambda line:line!=header).mapPartitions(parse_partition).map(classify).cache()
input_count=classified.count()
clean_orders=classified.filter(lambda x:x["valid"]).map(lambda x:x["row"]).cache()
rejected_orders=classified.filter(lambda x:not x["valid"])
print(input_count,clean_orders.count(),rejected_orders.count())

# COMMAND ----------

# MAGIC ## 6 — Create the key-value Pair RDD
# MAGIC 
# MAGIC Key: category. Value: `(1, quantity, net_amount)`.

# COMMAND ----------

completed=clean_orders.filter(lambda r:r["status"]=="COMPLETED")
category_metrics=completed.map(lambda r:(r["category"],(1,r["quantity"],r["net_amount"])))
print(category_metrics.take(5))

# COMMAND ----------

# MAGIC ## 7 — Aggregate values by key
# MAGIC 
# MAGIC `aggregateByKey` performs map-side combining and a key shuffle.

# COMMAND ----------

def add_metric(a,b):return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
category_summary=category_metrics.aggregateByKey((0,0,0.0),add_metric,add_metric)
print(category_summary.collect())

# COMMAND ----------

# MAGIC ## 8 — Load a second Pair RDD and join on category

# COMMAND ----------

raw_master=sc.textFile(MASTER_PATH,2); master_header=raw_master.first()
category_master=raw_master.filter(lambda x:x!=master_header).map(lambda x:x.split(",")).map(lambda v:(v[0],(v[1],v[2],float(v[3]))))
joined=category_summary.join(category_master)
print(joined.collect())

# COMMAND ----------

# MAGIC ## 9 — Build a report-ready RDD

# COMMAND ----------

report_rdd=(joined.map(lambda item:{"category":item[0],"department":item[1][1][0],"manager":item[1][1][1],"completed_orders":item[1][0][0],"units_sold":item[1][0][1],"net_revenue":round(item[1][0][2],2),"average_order_value":round(item[1][0][2]/item[1][0][0],2),"monthly_target":item[1][1][2],"achievement_pct":round(item[1][0][2]/item[1][1][2]*100,2)}).sortBy(lambda r:r["net_revenue"],ascending=False).cache())
for r in report_rdd.collect():print(r)

# COMMAND ----------

# MAGIC ## 10 — Save clean, rejected and report text directories

# COMMAND ----------

def add_header(index,rows,header):return itertools.chain([header] if index==0 else [],rows)
def esc(v):
    t=str(v);return '"'+t.replace('"','""')+'"' if ',' in t else t
for p in [CLEAN_OUTPUT,REJECT_OUTPUT,REPORT_OUTPUT,SEQUENCE_OUTPUT]:dbutils.fs.rm(p,recurse=True)
clean_keys=["order_id","order_date","customer_id","city","category","quantity","unit_price","discount_pct","status","gross_amount","net_amount"]
clean_orders.sortBy(lambda r:r["order_id"]).map(lambda r:",".join(esc(r[k]) for k in clean_keys)).coalesce(1).mapPartitionsWithIndex(lambda i,rows:add_header(i,rows,",".join(clean_keys))).saveAsTextFile(CLEAN_OUTPUT)
rejected_orders.map(lambda x:f'{x["row"].get("order_id","")},{esc(x["row"].get("city",""))},{esc("|".join(x["reasons"]))}').coalesce(1).mapPartitionsWithIndex(lambda i,rows:add_header(i,rows,"order_id,city,rejection_reason")).saveAsTextFile(REJECT_OUTPUT)
report_keys=["category","department","manager","completed_orders","units_sold","net_revenue","average_order_value","monthly_target","achievement_pct"]
report_rdd.map(lambda r:",".join(esc(r[k]) for k in report_keys)).coalesce(1).mapPartitionsWithIndex(lambda i,rows:add_header(i,rows,",".join(report_keys))).saveAsTextFile(REPORT_OUTPUT)
print(dbutils.fs.ls(REPORT_OUTPUT))

# COMMAND ----------

# MAGIC ## 11 — Save a key-value SequenceFile

# COMMAND ----------

report_rdd.map(lambda r:(r["category"],json.dumps(r,sort_keys=True))).saveAsSequenceFile(SEQUENCE_OUTPUT)
print(dbutils.fs.ls(SEQUENCE_OUTPUT))

# COMMAND ----------

# MAGIC ## 12 — Verify control totals and results

# COMMAND ----------

rows=report_rdd.collect();assert input_count==clean_orders.count()+rejected_orders.count();assert {r["category"]:r["net_revenue"] for r in rows}=={"Electronics":204540.0,"Fashion":25420.0,"Grocery":9074.0};print("Verification passed")
report_rdd.unpersist();clean_orders.unpersist();classified.unpersist()

# COMMAND ----------

# MAGIC # Expected results
# MAGIC 
# MAGIC Input 20; valid 18; rejected 2; completed sales 15. Electronics revenue 204,540; Fashion 25,420; Grocery 9,074.
