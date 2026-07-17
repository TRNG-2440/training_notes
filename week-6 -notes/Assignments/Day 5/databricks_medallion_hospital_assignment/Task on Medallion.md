# Databricks Medallion Architecture Assignment  
## Hospital Appointment and Revenue Analytics

### Environment

Complete this assignment in **Databricks Legacy Free Edition without Unity Catalog**.

Use the classic workspace file system available in your environment. Suggested paths:

```text
/Volumes/tables/medallion_hospital/input/
/Volumes/tables/medallion_hospital/raw/
/Volumes/tables/medallion_hospital/bronze/
/Volumes/tables/medallion_hospital/silver/
/Volumes/tables/medallion_hospital/gold/
```

You may use different paths, but keep the RAW, Bronze, Silver, and Gold layers clearly separated.

---

# Business Scenario

A multi-specialty hospital receives appointment data from web, mobile, and call-center systems. The source data contains duplicate appointments, invalid values, inconsistent text, invalid dates, incorrect doctor mappings, and billing errors.

Management needs a reliable medallion pipeline that:

1. Preserves the original source data.
2. Creates an auditable Bronze layer.
3. Cleans and validates records in Silver.
4. Produces report-ready Gold tables for hospital operations and revenue analysis.

---

# Files Provided

## 1. `hospital_appointments_raw.csv`

Contains **60 source records** with intentionally incorrect data.

Important data-quality problems include:

- Duplicate appointment IDs
- An exact duplicate row
- Missing patient ID and patient name
- Leading and trailing spaces
- Inconsistent upper/lower case
- Invalid dates
- Mixed date formats
- Invalid age values
- Invalid gender
- Invalid department names
- Unknown doctor IDs
- Doctor and department mismatch
- Negative consultation fee
- Non-numeric consultation fee
- Invalid discount percentages
- Incorrect amount paid
- Negative amount paid
- Invalid appointment statuses
- Invalid payment modes
- Invalid phone numbers
- Null discount value

## 2. `hospital_reference_master.xlsx`

Contains the following sheets:

- `doctor_master`
- `department_targets`
- `status_mapping`
- `data_dictionary`

---

# Expected Architecture

```text
CSV + Excel source files
          │
          ▼
┌─────────────────────┐
│ RAW Layer           │
│ Original files      │
│ No transformation   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Bronze Layer        │
│ Source structure    │
│ Audit columns       │
│ Minimal conversion  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Silver Layer        │
│ Cleaned records     │
│ Validated records   │
│ Rejected records    │
│ Reference joins     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Gold Layer          │
│ Department KPIs     │
│ Doctor performance  │
│ Daily trends        │
│ Quality dashboard   │
└─────────────────────┘
```

---

# Part A — Workspace and File Setup

## Question 1

Create the following folder structure:

```text
medallion_hospital/
├── input/
├── raw/
├── bronze/
├── silver/
└── gold/
```

Upload the CSV and Excel files into the `input` folder.

## Question 2

Create a new notebook named:

```text
01_Hospital_Medallion_Pipeline
```

Add a Markdown cell containing:

- Assignment name
- Student name
- Execution date
- Source file names
- Brief business objective

## Question 3

Define reusable path variables for all layers.

Example variable names:

```python
base_path
input_path
raw_path
bronze_path
silver_path
gold_path
```

---

# Part B — RAW Layer

## Question 4

Copy the original CSV and Excel files from the input location into the RAW layer without changing their content.

The RAW layer must preserve:

- Original file name
- Original file format
- Original column names
- Original records
- Original incorrect values

## Question 5

Display the files available in the RAW layer and prove that both source files were copied successfully.

## Question 6

Explain in a Markdown cell why the RAW layer should not contain business transformations.

---

# Part C — Bronze Layer

## Question 7

Read `hospital_appointments_raw.csv` into a Spark DataFrame.

Use options appropriate for a header-based CSV file.

Initially load source columns in a way that prevents invalid values from being silently lost.

## Question 8

Read all Excel sheets required for the assignment.

Create individual DataFrames for:

```text
doctor_master
department_targets
status_mapping
data_dictionary
```

Use a method supported by your workspace. A Python Excel library may be used to read the workbook and then convert each sheet to a Spark DataFrame.

## Question 9

Add the following audit columns to the appointment Bronze DataFrame:

```text
source_file_name
source_system_name
bronze_ingestion_timestamp
bronze_ingestion_date
record_hash
```

## Question 10

The `record_hash` should be created from the source business columns. It must help detect exact duplicate records.

## Question 11

Write the appointment Bronze DataFrame and all Excel reference DataFrames to the Bronze layer.

Suggested names:

```text
bronze_appointments
bronze_doctor_master
bronze_department_targets
bronze_status_mapping
bronze_data_dictionary
```

Use Delta format when supported. Otherwise, use Parquet and clearly document the choice.

## Question 12

Show:

- Bronze row count
- Distinct appointment ID count
- Exact duplicate count using `record_hash`
- Duplicate business-key count using `appointment_id`

---

# Part D — Silver Data Quality and Transformation

Perform the following transformations.

## Question 13 — Trim and standardize text

Apply trimming and case standardization to:

```text
patient_name
city
department
doctor_name
appointment_status
payment_mode
source_system
```

Expected examples:

```text
"  Diya Sharma  " → "Diya Sharma"
"chennai" → "Chennai"
"ORTHOPEDICS" → "Orthopedics"
"dr. meera iyer" → "Dr. Meera Iyer"
```

## Question 14 — Standardize appointment status

Join with `status_mapping` and derive:

```text
standard_appointment_status
is_billable
include_in_utilization
```

Unmapped statuses must be marked as rejected or assigned a clear validation failure.

## Question 15 — Convert and validate appointment dates

Convert `appointment_date` to a valid date.

Support the formats present in the source data.

Create:

```text
appointment_date_clean
appointment_year
appointment_month
appointment_day
```

Invalid dates must not be accepted as valid.

## Question 16 — Convert numeric columns

Convert these columns safely:

```text
age
consultation_fee
discount_pct
amount_paid
```

Rows that cannot be converted must be flagged.

## Question 17 — Validate age

Valid age range:

```text
0 to 110
```

Flag negative ages and unrealistic ages.

## Question 18 — Validate gender

Accepted values:

```text
M
F
O
```

Any other value must be rejected or marked invalid.

## Question 19 — Standardize department values

Map known aliases where appropriate.

Example:

```text
Cardio → Cardiology
```

After standardization, the department must exist in `department_targets`.

## Question 20 — Validate doctor details

Join the appointment data with `doctor_master`.

Validate that:

- `doctor_id` exists
- Doctor is active
- Doctor name matches the master
- Doctor belongs to the stated department

Use the master doctor name and department in the clean output.

## Question 21 — Handle duplicate records

Create rules for:

1. Exact duplicate records
2. Duplicate `appointment_id` values

For duplicate appointment IDs, keep one deterministic record and reject the remaining records. Document the ordering rule used.

## Question 22 — Handle null values

Apply appropriate rules:

- Missing patient ID → reject
- Missing patient name → reject
- Null discount percentage → treat as `0`
- Blank payment mode → allowed only when amount paid is `0`
- Missing required master-data match → reject

## Question 23 — Validate consultation fee

Rules:

- Must be numeric
- Must be greater than or equal to zero

## Question 24 — Validate discount

Rules:

```text
0 <= discount_pct <= 100
```

## Question 25 — Calculate expected amount

Create:

```text
expected_amount_paid
```

Suggested formula for completed/billable appointments:

```text
consultation_fee × (1 - discount_pct / 100)
```

For non-billable statuses, expected paid amount should normally be zero.

## Question 26 — Validate amount paid

Flag:

- Negative amount paid
- Amount paid much higher than the expected amount
- Completed appointments where actual amount differs from expected amount
- Non-billable appointments with a non-zero payment

Use a small tolerance for decimal comparison.

## Question 27 — Validate payment mode

Accepted paid transaction modes:

```text
UPI
CARD
CASH
NET_BANKING
```

Blank is allowed only when no amount was paid.

## Question 28 — Validate phone number

A valid phone number must contain exactly 10 numeric digits.

Create a masked phone field for the Silver layer, for example:

```text
98******21
```

Do not expose the full phone number in Gold reports.

## Question 29 — Create validation columns

Create at least:

```text
is_valid_record
validation_error_count
validation_errors
silver_processed_timestamp
```

`validation_errors` should contain one or more readable error reasons.

Example:

```text
INVALID_AGE|INVALID_PHONE
```

## Question 30 — Split valid and rejected data

Create:

```text
silver_appointments_clean
silver_appointments_rejected
```

The rejected dataset must retain:

- Original identifying columns
- Validation reasons
- Source file
- Bronze ingestion timestamp
- Silver processing timestamp

## Question 31 — Silver output

Write both clean and rejected datasets into the Silver layer.

Display:

- Bronze row count
- Clean Silver row count
- Rejected Silver row count
- Reconciliation result

Required reconciliation:

```text
Bronze count = Clean Silver count + Rejected Silver count
```

---

# Part E — Gold Layer: Report-Ready Outputs

Create the following Gold outputs from clean Silver data.

## Question 32 — Department monthly performance

Create a monthly department-level report with:

```text
appointment_year
appointment_month
department
total_appointments
completed_appointments
cancelled_appointments
no_show_appointments
scheduled_appointments
completion_rate_pct
cancellation_rate_pct
no_show_rate_pct
gross_consultation_value
discount_value
net_revenue
average_revenue_per_completed_appointment
unique_patients
monthly_completed_target
monthly_revenue_target
completed_target_achievement_pct
revenue_target_achievement_pct
target_status
```

Join the report with `department_targets`.

Suggested target status:

```text
ACHIEVED
PARTIALLY_ACHIEVED
NOT_ACHIEVED
```

## Question 33 — Doctor performance report

Create a doctor-level report with:

```text
doctor_id
doctor_name
department
specialization
total_appointments
completed_appointments
cancelled_appointments
no_show_appointments
completion_rate_pct
no_show_rate_pct
unique_patients
net_revenue
average_revenue_per_completed_appointment
```

Rank doctors within each department by:

1. Net revenue
2. Completed appointments

## Question 34 — Daily operational trend

Create a daily report:

```text
appointment_date_clean
department
total_appointments
completed_appointments
cancelled_appointments
no_show_appointments
net_revenue
```

## Question 35 — Source-system performance

Create a source-system report:

```text
source_system
total_appointments
completed_appointments
conversion_to_completed_pct
cancelled_appointments
no_show_appointments
net_revenue
average_revenue
```

## Question 36 — Data-quality summary

Create a Gold quality report containing:

```text
quality_rule
failed_record_count
failed_record_pct
```

Include at least these quality categories:

- Duplicate records
- Invalid date
- Missing patient
- Invalid age
- Invalid gender
- Invalid department
- Invalid doctor
- Invalid fee
- Invalid discount
- Invalid amount paid
- Invalid payment mode
- Invalid phone
- Invalid status

## Question 37 — Top business insights

Using the Gold outputs, answer these questions:

1. Which department generated the highest net revenue?
2. Which department had the highest cancellation rate?
3. Which department had the highest no-show rate?
4. Which doctor completed the most appointments?
5. Which doctor generated the highest revenue?
6. Which source system produced the highest completed conversion rate?
7. Which month generated the highest revenue?
8. Which department missed its monthly target by the largest percentage?
9. What are the three most common data-quality failures?
10. How many records were rejected from the source?

---

# Part F — Technical Requirements

## Question 38

Use Spark transformations wherever practical.

Include examples of:

```text
select
withColumn
when
otherwise
cast
trim
upper/lower/initcap
regexp_replace
to_date
coalesce
join
groupBy
agg
countDistinct
sum
avg
row_number
rank or dense_rank
Window
```

## Question 39

Avoid collecting the full source dataset to the driver.

Small reference sheets may be converted through Python when necessary, but the appointment transformations and aggregations must be performed using Spark.

## Question 40

Make the pipeline rerunnable.

A second execution should not create uncontrolled duplicate data.

Document whether you use:

```text
overwrite
append with deduplication
run-specific paths
```

## Question 41

Add Markdown documentation before each major layer:

```text
RAW
BRONZE
SILVER
GOLD
```

Explain:

- Purpose
- Input
- Output
- Main transformations
- Validation performed

## Question 42

At the end of the notebook, print or display a control summary:

```text
Raw files copied
Bronze rows
Silver clean rows
Silver rejected rows
Gold tables created
Reconciliation passed
Pipeline status
```

---

# Deliverables

Submit:

1. Databricks notebook exported as `.dbc`, `.ipynb`, or source file.
2. Screenshot of RAW folder.
3. Screenshot of Bronze outputs.
4. Screenshot of Silver clean and rejected counts.
5. Screenshot of Gold department report.
6. Screenshot of Gold doctor ranking.
7. Screenshot of the data-quality report.
8. A short document containing the ten business insights.
9. A brief explanation of the medallion architecture used.
10. The final reconciliation result.

---