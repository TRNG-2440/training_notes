# E-commerce Medallion Architecture Assignment Questions

## Instructions

Use `02_Ecommerce_Assignment_Starter.ipynb` and the seven CSV files. Complete the work in Databricks Free Edition using PySpark DataFrames, Spark SQL, and Delta tables.

Do not modify the source CSV files. Invalid rows must be retained in quarantine tables with an understandable `dq_reason`.

## Submission

Submit:

1. completed notebook
2. screenshots of Bronze, Silver, quarantine, and Gold outputs
3. answers to conceptual questions
4. SQL query outputs
5. final reconciliation results

---

## Part A — Environment and Bronze Layer

### Q1
Display the Spark version, current catalog, and current schema.

### Q2
Create three schemas named `ecom_bronze`, `ecom_silver`, and `ecom_gold`. Explain the purpose of each schema.

### Q3
Create a Unity Catalog managed volume named `ecommerce_training_files` under the `default` schema. Print its `/Volumes/...` path.

### Q4
Verify that all seven required CSV files exist in the volume and display each file's row count.

### Q5
Read `orders.csv` without schema inference. Prove that its business columns were loaded as strings.

### Q6
Create a reusable Bronze ingestion function. It must add `_source_file`, `_ingested_at`, and `_raw_row_hash`.

### Q7
Write each source DataFrame as a managed Delta table in the Bronze layer.

### Q8
Calculate the row count and column count for every Bronze table.

### Q9
Find duplicate raw rows by grouping on `_raw_row_hash`. Which source contains deliberately duplicated business records?

### Q10
Profile the business key and three important columns from each source for null or blank values.

---

## Part B — Silver Data Quality and Transformation

### Q11
Clean customer names, email, city, state, and country by trimming spaces and applying consistent casing.

### Q12
Validate `customer_id` using the format `C######` and email using a regular expression.

### Q13
Convert customer `date_of_birth` and `signup_date` to date columns without failing on malformed values.

### Q14
Convert customer active values such as `Y`, `Yes`, `1`, and `true` to Boolean `true`, and corresponding negative values to `false`.

### Q15
Normalize gender and loyalty tier. Reject unsupported loyalty tiers.

### Q16
Deduplicate customers by `customer_id`, retaining the row with the most recent valid signup date.

### Q17
Create `customers` and `customers_quarantine` Delta tables. Show the five most common customer quality reasons.

### Q18
Cast product price, cost, stock quantity, rating, and created date to correct types.

### Q19
Apply product business rules: positive price and cost, nonnegative stock, rating from 0 to 5, allowed category, and cost not greater than price.

### Q20
Deduplicate products and create valid and quarantine tables.

### Q21
Parse the multiple timestamp formats in `orders.order_date` and `orders.last_updated`.

### Q22
Normalize order status variations such as `complete`, `CANCELLED`, and `in-transit`.

### Q23
Normalize the order channel and validate currency.

### Q24
Cast all order financial fields to decimals. Do not disable ANSI mode.

### Q25
Validate the formula:

```text
total_amount = subtotal - discount_amount + tax_amount + shipping_cost
```

Allow a tolerance of 1.00.

### Q26
Use a referential check to quarantine orders whose customer does not exist in valid Silver customers.

### Q27
Deduplicate orders using the most recent `last_updated` value.

### Q28
Validate order-item quantity, price, discount percentage, and line total.

### Q29
Check the order-item formula:

```text
line_total = quantity × unit_price × (1 - discount_pct / 100)
```

Allow a tolerance of 0.05.

### Q30
Quarantine order items whose order or product does not exist in valid Silver data.

### Q31
Normalize payment method and payment status. Check that successful payment amount matches the order total.

### Q32
Identify payments made before the corresponding order timestamp.

### Q33
Validate shipment sequence, tracking number, status, and shipping cost.

### Q34
Validate return date, reason, status, refund amount, order reference, and product reference.

### Q35
Create one quality summary containing Bronze count, valid Silver count, quarantine count, and valid percentage for every entity.

---

## Part C — PySpark DataFrame Operations: 

### Q36
Select delivered or shipped orders whose total amount is at least 5,000. Return only order ID, customer ID, date, channel, and amount.

### Q37
Add `order_year`, `order_month`, `order_day`, and `order_week` columns to valid orders.

### Q38
Join orders, customers, and payments. Display customer name, loyalty tier, order amount, payment method, and payment status.

### Q39
Calculate revenue, units sold, order count, and average line value by product category.

### Q40
Use a window function to rank products by revenue within each category.

### Q41
Use `lag` and a running total to analyze daily revenue.

### Q42
Repartition order items by `order_id` into eight partitions and show row counts by `spark_partition_id()`.

---

## Part D — Spark SQL: 
### Q43
Using Spark SQL, find the top 20 customers by lifetime order value, excluding cancelled orders.

### Q44
Use a CTE and `DENSE_RANK` to rank categories by revenue.

### Q45
Find customers who exist in Silver customers but have no valid Silver orders. Use either `LEFT ANTI JOIN` or `NOT EXISTS`.

### Q46
Create a SQL view called `vw_monthly_channel_sales` containing year, month, channel, order count, customer count, and revenue.

### Q47
Find the top three products by revenue in every category.

### Q48
Calculate payment success rate by payment method.

### Q49
Calculate return rate by category using valid order items and returns.

### Q50
Show daily revenue, previous-day revenue, daily change, and cumulative revenue.

---

## Part E — Gold and Delta Lake: 
### Q51
Create `dim_customer` and `dim_product` Gold tables.

### Q52
Create a line-level Gold fact table joining valid orders, order items, products, latest payment, latest shipment, and return summary.

### Q53
Create `daily_sales_kpi`, `category_performance`, and `customer_360`.

### Q54
Create a safe copy of the Silver products table and use `MERGE` to update two products and insert one late-arriving product.

### Q55
Run one `UPDATE`, one `DELETE`, and `DESCRIBE HISTORY` on the safe copy.

### Q56
Explain why the assignment uses built-in functions instead of Python UDFs for standard cleansing.

### Q57
Explain why invalid records are written to quarantine instead of being silently deleted.

### Q58
Explain why Bronze values are initially loaded as strings.

### Q59
Explain why the notebook does not use RDD APIs.

### Q60
Produce a final validation report proving:

- Bronze equals valid plus quarantine for every entity.
- Valid business keys are unique.
- Valid order items have no orphan order or product references.
- The Gold fact row count equals the valid Silver order-item row count.
