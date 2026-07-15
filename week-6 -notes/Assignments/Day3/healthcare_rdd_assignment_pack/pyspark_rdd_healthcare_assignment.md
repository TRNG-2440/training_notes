# PySpark RDD Assignment: Healthcare Patient Visit Analytics

## Scenario
You are working as a data engineer for a multi-city hospital group. The hospital receives daily patient visit data from branches. Your job is to build an RDD-based PySpark program in VS Code that reads the CSV, validates records, performs transformations/actions, and uses shared variables.

## Dataset
Use `healthcare_patient_visits.csv` with 34 records. The file intentionally contains a few bad records so that you can practice accumulators and validation.

## Columns
- visit_id
- visit_date
- patient_id
- patient_name
- age
- city
- department
- doctor_id
- visit_type
- diagnosis
- bill_amount
- payment_status
- rating

## Business Requirements

### Part A: RDD Creation
1. Create a SparkSession in local mode.
2. Create an RDD using `sc.textFile()` from the CSV.
3. Remove the header.
4. Parse every row into a dictionary.
5. Cache the valid parsed RDD.

### Part B: Data Validation Using Accumulators
Create accumulators to count:
1. Missing city records
2. Invalid age records where age <= 0
3. Invalid bill amount records where bill_amount <= 0
4. Invalid payment status records where status is not PAID, PENDING, or CANCELLED
5. Total invalid records

Valid records only should continue to business analytics.

### Part C: Broadcast Variable
Create a broadcast variable for department service charges:

```python
service_charge_map = {
    "Cardiology": 0.18,
    "Orthopedics": 0.12,
    "Dermatology": 0.08,
    "Neurology": 0.15,
    "General Medicine": 0.05,
}
```

Use it to calculate:
- service_charge = bill_amount * service_charge_pct
- final_amount = bill_amount + service_charge

### Part D: Transformations to Perform
Use at least these transformations:
1. `map()` - parse CSV and calculate final amount
2. `filter()` - keep valid records and paid records
3. `flatMap()` - create searchable tags like `city:Chennai`, `dept:Cardiology`, `type:OPD`
4. `distinct()` - find distinct cities and departments
5. `mapValues()` - format amounts or enrich pair RDD values
6. `reduceByKey()` - calculate revenue by city and department
7. `groupByKey()` - collect visit IDs by department
8. `sortBy()` - sort departments by revenue descending
9. `union()` - combine OPD and Emergency patient IDs
10. `repartition()` and `coalesce()` - change partition count

### Part E: Actions to Perform
Use at least these actions:
1. `count()`
2. `first()`
3. `take()`
4. `collect()`
5. `countByValue()`
6. `reduce()`
7. `takeOrdered()`
8. `foreach()` with accumulator validation

### Part F: Expected Analytics Questions
Answer these using RDD operations:
1. How many total data rows are available?
2. How many valid and invalid records are present?
3. How many visits happened in each city?
4. How many visits happened in each department?
5. What is the final revenue by city?
6. What is the final revenue by department?
7. Which top 3 paid visits generated the highest final amount?
8. Which departments handled emergency visits?
9. What are all distinct cities and departments?
10. Which department has the highest average patient rating?

## Expected Validation Result
The dataset contains 34 data rows.

Expected invalid records:
- V031: age is 0
- V032: city is missing
- V033: bill_amount is negative
- V034: payment_status is UNKNOWN

So expected counts:
- Total rows: 34
- Valid rows: 30
- Invalid rows: 4

## Submission
Submit:
1. Python file: `healthcare_rdd_assignment_solution.py`
2. Dataset: `healthcare_patient_visits.csv`
3. Screenshot of output
4. Short explanation of where you used broadcast variable and accumulator

