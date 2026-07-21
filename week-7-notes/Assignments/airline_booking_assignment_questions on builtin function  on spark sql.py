# Databricks notebook source

# COMMAND ----------
# MAGIC %md
# MAGIC # PySpark Built-in Functions Assignment
# MAGIC ## Airline Booking Analytics — Revised Scope
# MAGIC 
# MAGIC Excluded: arrays, maps, structs, window functions, and the complete pipeline.
# MAGIC 
# MAGIC Run the setup cell and complete each TODO cell.

# COMMAND ----------
from pyspark.sql import functions as F

columns = [
    "booking_id",
    "passenger_name",
    "airline_code",
    "route_code",
    "ticket_amount",
    "baggage_kg",
    "booking_date",
    "travel_date",
    "origin_city",
    "destination_city",
    "seat_class",
    "promo_discount",
    "services",
    "booking_status",
    "satisfaction_score",
    "payment_mode"
]

bookings = [(1001, '  aarav mehta  ', 'SKY', 'BLR-DEL', 8500.0, 15.0, '2026-01-05', '2026-02-10', 'Bengaluru', 'Delhi', 'Economy', None, 'Meal|WiFi', 'CONFIRMED', 4.5, 'Card'), (1002, 'DIYA IYER', 'NVA', 'DEL-BOM', 7200.0, 20.0, '2026-01-08', '2026-02-12', 'Delhi', 'Mumbai', 'Economy', 500.0, 'Meal|Priority Boarding', 'CONFIRMED', 4.2, 'UPI'), (1003, 'kabir khan', 'ORB', 'MAA-HYD', 6400.0, 10.0, '2026-01-10', '2026-02-15', 'Chennai', 'Hyderabad', 'Economy', 300.0, 'WiFi', 'COMPLETED', 3.8, 'Card'), (1004, 'Meera Das', 'ZEP', 'BOM-GOA', 5100.0, 7.0, '2026-01-12', '2026-02-18', 'Mumbai', 'Goa', 'Economy', None, 'Meal', 'CANCELLED', None, 'NetBanking'), (1005, '  nisha roy', 'LUM', 'CCU-DEL', 9300.0, 22.0, '2026-01-15', '2026-02-20', 'Kolkata', 'Delhi', 'Premium Economy', 750.0, 'Meal|WiFi|Lounge', 'CONFIRMED', 4.7, 'UPI'), (1006, 'ARJUN NAIR', 'SKY', 'BLR-MAA', 5800.0, 12.0, '2026-01-18', '2026-02-21', 'Bengaluru', 'Chennai', 'Economy', 250.0, 'Meal|WiFi', 'COMPLETED', 4.0, 'Card'), (1007, 'sana sheikh', 'NVA', 'HYD-BLR', 6900.0, 18.0, '2026-01-20', '2026-02-23', 'Hyderabad', 'Bengaluru', 'Economy', None, 'Priority Boarding', 'CONFIRMED', 4.1, 'Wallet'), (1008, 'Rohan  Sen', 'ORB', 'DEL-JAI', 4300.0, 5.0, '2026-01-22', '2026-02-25', 'Delhi', 'Jaipur', 'Economy', 200.0, None, 'COMPLETED', 3.6, 'UPI'), (1009, '  priya kapoor  ', 'ZEP', 'BLR-DEL', 12500.0, 25.0, '2026-01-25', '2026-03-01', 'Bengaluru', 'Delhi', 'Business', 1000.0, 'Meal|WiFi|Lounge|Priority Boarding', 'CONFIRMED', 4.9, 'Card'), (1010, 'VIKAS JAIN', 'LUM', 'DEL-BOM', 11800.0, 24.0, '2026-01-28', '2026-03-03', 'Delhi', 'Mumbai', 'Business', None, 'Meal|Lounge', 'CONFIRMED', 4.4, 'NetBanking'), (1011, 'ananya bose', 'SKY', 'MAA-HYD', 6100.0, 9.0, '2026-02-01', '2026-03-05', 'Chennai', 'Hyderabad', 'Economy', 350.0, 'Meal', 'COMPLETED', 4.0, 'UPI'), (1012, 'Karan Malhotra', 'NVA', 'BOM-GOA', 5400.0, 8.0, '2026-02-02', '2026-03-06', 'Mumbai', 'Goa', 'Economy', None, 'Meal|WiFi', 'CONFIRMED', 3.9, 'Card'), (1012, 'Karan Malhotra', 'NVA', 'BOM-GOA', 5400.0, 8.0, '2026-02-02', '2026-03-06', 'Mumbai', 'Goa', 'Economy', None, 'Meal|WiFi', 'CONFIRMED', 3.9, 'Card'), (1013, '  ishita paul', 'ORB', 'CCU-DEL', 8700.0, 16.0, '2026-02-04', '2026-03-08', 'Kolkata', 'Delhi', 'Premium Economy', 600.0, 'Meal|WiFi', 'COMPLETED', 4.3, 'Wallet'), (1014, 'MOHAN RAO', 'ZEP', 'BLR-MAA', 5900.0, 14.0, '2026-02-06', '2026-03-10', 'Bengaluru', 'Chennai', 'Economy', 300.0, 'Meal', 'CONFIRMED', 4.1, 'UPI'), (1015, 'leena joseph', 'LUM', 'HYD-BLR', 7600.0, 19.0, '2026-02-08', '2026-03-12', 'Hyderabad', 'Bengaluru', 'Premium Economy', None, 'WiFi|Priority Boarding', 'CANCELLED', 3.5, 'Card'), (1016, 'Dev Patel', 'SKY', 'DEL-JAI', 4500.0, 6.0, '2026-02-10', '2026-03-14', 'Delhi', 'Jaipur', 'Economy', 150.0, 'Meal', 'COMPLETED', 3.7, 'Cash'), (1017, '  kavya reddy  ', 'NVA', 'BLR-DEL', 8500.0, 15.0, '2026-02-12', '2026-03-16', 'Bengaluru', 'Delhi', 'Economy', 500.0, 'Meal|WiFi', 'CONFIRMED', 4.6, 'UPI'), (1018, 'RAHUL VERMA', 'ORB', 'DEL-BOM', 7200.0, 20.0, '2026-02-14', '2026-03-18', 'Delhi', 'Mumbai', 'Economy', None, 'Meal|Priority Boarding', 'CONFIRMED', 4.0, 'Card'), (1019, 'simran kaur', 'ZEP', 'MAA-HYD', 6400.0, 11.0, '2026-02-16', '2026-03-20', 'Chennai', 'Hyderabad', 'Economy', 250.0, 'WiFi', 'COMPLETED', 3.8, 'Wallet'), (1020, 'Naveen  Kumar', 'LUM', 'BOM-GOA', 5200.0, 7.5, '2026-02-18', '2026-03-22', 'Mumbai', 'Goa', 'Economy', None, 'Meal', 'CONFIRMED', 4.2, 'NetBanking'), (1021, '  tara singh', 'SKY', 'CCU-DEL', 9400.0, 21.0, '2026-02-20', '2026-03-24', 'Kolkata', 'Delhi', 'Premium Economy', 700.0, 'Meal|WiFi|Lounge', 'CONFIRMED', 4.8, 'Card'), (1022, 'AMAN GUPTA', 'NVA', 'BLR-MAA', 5800.0, 12.0, '2026-02-22', '2026-03-26', 'Bengaluru', 'Chennai', 'Economy', 200.0, 'Meal|WiFi', 'COMPLETED', 3.9, 'UPI'), (1023, 'pooja shah', 'ORB', 'HYD-BLR', 7000.0, 17.0, '2026-02-24', '2026-03-28', 'Hyderabad', 'Bengaluru', 'Economy', None, 'Priority Boarding', 'CONFIRMED', 4.1, 'Card'), (1024, 'Suresh Menon', 'ZEP', 'DEL-JAI', 4400.0, 5.5, '2026-02-26', '2026-03-30', 'Delhi', 'Jaipur', 'Economy', 180.0, None, 'COMPLETED', 3.6, 'Cash'), (1025, '  riya chatterjee  ', 'LUM', 'BLR-DEL', 12700.0, 26.0, '2026-03-01', '2026-04-02', 'Bengaluru', 'Delhi', 'Business', 1100.0, 'Meal|WiFi|Lounge|Priority Boarding', 'CONFIRMED', 4.9, 'Card'), (1026, 'ADITYA SINGH', 'SKY', 'DEL-BOM', 11900.0, 23.0, '2026-03-03', '2026-04-04', 'Delhi', 'Mumbai', 'Business', None, 'Meal|Lounge', 'CONFIRMED', 4.5, 'NetBanking'), (1027, 'neha pillai', 'NVA', 'MAA-HYD', 6200.0, 10.0, '2026-03-05', '2026-04-06', 'Chennai', 'Hyderabad', 'Economy', 300.0, 'Meal', 'COMPLETED', 4.0, 'UPI'), (1028, 'Harish  Babu', 'ORB', 'BOM-GOA', 5500.0, 8.0, '2026-03-07', '2026-04-08', 'Mumbai', 'Goa', 'Economy', None, 'Meal|WiFi', 'CONFIRMED', 3.8, 'Card'), (1029, '  zoya ali', 'ZEP', 'CCU-DEL', 8800.0, 16.0, '2026-03-09', '2026-04-10', 'Kolkata', 'Delhi', 'Premium Economy', 650.0, 'Meal|WiFi', 'COMPLETED', 4.4, 'Wallet'), (1030, 'MANOJ DAS', 'LUM', 'BLR-MAA', 6000.0, 13.0, '2026-03-11', '2026-04-12', 'Bengaluru', 'Chennai', 'Economy', 280.0, 'Meal', 'CONFIRMED', 4.0, 'UPI'), (1031, 'swati nair', 'SKY', 'HYD-BLR', 7700.0, 18.0, '2026-03-13', '2026-04-14', 'Hyderabad', 'Bengaluru', 'Premium Economy', None, 'WiFi|Priority Boarding', 'CANCELLED', 3.4, 'Card'), (1032, 'Ritesh Jain', 'NVA', 'DEL-JAI', 4600.0, 6.0, '2026-03-15', '2026-04-16', 'Delhi', 'Jaipur', 'Economy', 160.0, 'Meal', 'COMPLETED', 3.7, 'Cash'), (1033, '  lavanya krishnan ', 'ORB', 'BLR-DEL', 8600.0, 15.0, '2026-03-17', '2026-04-18', 'Bengaluru', 'Delhi', 'Economy', 450.0, 'Meal|WiFi', 'CONFIRMED', 4.5, 'UPI'), (1034, 'OM PRAKASH', 'ZEP', 'DEL-BOM', 7300.0, 20.0, '2026-03-19', '2026-04-20', 'Delhi', 'Mumbai', 'Economy', None, 'Meal|Priority Boarding', 'CONFIRMED', 4.1, 'Card'), (1035, 'farah khan', 'LUM', 'MAA-HYD', 6500.0, 11.0, '2026-03-21', '2026-04-22', 'Chennai', 'Hyderabad', 'Economy', 320.0, 'WiFi', 'COMPLETED', 3.9, 'Wallet'), (1036, '  gautam roy', 'UNK', 'BLR-DEL', 8100.0, 14.0, '2026-03-23', '2026-04-24', 'Bengaluru', 'Delhi', 'Economy', None, 'Meal', 'CONFIRMED', None, None)]

airline_columns = [
    "airline_code",
    "airline_name",
    "headquarters",
    "service_tier"
]
airlines = [('SKY', 'SkyBridge Airways', 'Bengaluru', 'Full Service'), ('NVA', 'NovaJet', 'Delhi', 'Low Cost'), ('ORB', 'Orbit Air', 'Mumbai', 'Low Cost'), ('ZEP', 'Zephyr Airlines', 'Hyderabad', 'Full Service'), ('LUM', 'Lumina Flights', 'Chennai', 'Hybrid'), ('PAC', 'Pacifica Air', 'Kochi', 'Regional')]

route_columns = [
    "route_code",
    "route_name",
    "region",
    "distance_km",
    "standard_duration_minutes"
]
routes = [('BLR-DEL', 'Bengaluru to Delhi', 'North-South', 1740, 165), ('DEL-BOM', 'Delhi to Mumbai', 'West', 1150, 130), ('MAA-HYD', 'Chennai to Hyderabad', 'South', 630, 75), ('BOM-GOA', 'Mumbai to Goa', 'West', 435, 65), ('CCU-DEL', 'Kolkata to Delhi', 'East-North', 1305, 145), ('BLR-MAA', 'Bengaluru to Chennai', 'South', 290, 60), ('HYD-BLR', 'Hyderabad to Bengaluru', 'South', 500, 70), ('DEL-JAI', 'Delhi to Jaipur', 'North', 240, 55)]

new_bookings = [(1037, '  tanvi desai', 'SKY', 'BOM-GOA', 5600.0, 9.0, '2026-03-25', '2026-04-26', 'Mumbai', 'Goa', 'Economy', 250.0, 'Meal|WiFi', 'CONFIRMED', 4.2, 'UPI'), (1038, 'YASH AGARWAL', 'NVA', 'CCU-DEL', 9000.0, 18.0, '2026-03-27', '2026-04-28', 'Kolkata', 'Delhi', 'Premium Economy', None, 'Meal|Lounge', 'CONFIRMED', 4.6, 'Card'), (1039, 'maria jose', 'ORB', 'BLR-MAA', 6050.0, 12.0, '2026-03-29', '2026-04-30', 'Bengaluru', 'Chennai', 'Economy', 200.0, 'Meal', 'COMPLETED', 4.0, 'Wallet'), (1040, '  vivek sharma  ', 'ZEP', 'HYD-BLR', 7800.0, 17.0, '2026-03-31', '2026-05-02', 'Hyderabad', 'Bengaluru', 'Premium Economy', 400.0, 'WiFi|Priority Boarding', 'CONFIRMED', 4.3, 'NetBanking')]

bookings_df = spark.createDataFrame(bookings, columns)
airline_df = spark.createDataFrame(airlines, airline_columns)
route_df = spark.createDataFrame(routes, route_columns)
new_bookings_df = spark.createDataFrame(new_bookings, columns)

print("Main dataset row count (includes one intentional duplicate):", bookings_df.count())
bookings_df.printSchema()
display(bookings_df)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 1 — DataFrame inspection
# MAGIC 
# MAGIC Display the complete booking DataFrame without truncating long values. Print the schema and count the total records.
# MAGIC 
# MAGIC **Functions/concepts:** `show, printSchema, count`

# COMMAND ----------
# TODO Question 1
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 2 — Column operations
# MAGIC 
# MAGIC Select only booking_id, passenger_name, airline_code, route_code, and ticket_amount.
# MAGIC 
# MAGIC **Functions/concepts:** `select`

# COMMAND ----------
# TODO Question 2
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 3 — Column operations
# MAGIC 
# MAGIC Use F.col() to select passenger_name and ticket_amount.
# MAGIC 
# MAGIC **Functions/concepts:** `col`

# COMMAND ----------
# TODO Question 3
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 4 — Column operations
# MAGIC 
# MAGIC Rename passenger_name as traveller_name and ticket_amount as fare using alias().
# MAGIC 
# MAGIC **Functions/concepts:** `alias`

# COMMAND ----------
# TODO Question 4
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 5 — Column operations
# MAGIC 
# MAGIC Create a gross_amount column equal to ticket_amount + promo_discount. Treat a null discount as 0 before calculating.
# MAGIC 
# MAGIC **Functions/concepts:** `withColumn, coalesce, lit`

# COMMAND ----------
# TODO Question 5
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 6 — Column operations
# MAGIC 
# MAGIC Rename booking_status to reservation_status using withColumnRenamed().
# MAGIC 
# MAGIC **Functions/concepts:** `withColumnRenamed`

# COMMAND ----------
# TODO Question 6
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 7 — Column operations
# MAGIC 
# MAGIC Create a DataFrame without services and payment_mode.
# MAGIC 
# MAGIC **Functions/concepts:** `drop`

# COMMAND ----------
# TODO Question 7
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 8 — Filtering
# MAGIC 
# MAGIC Display bookings with ticket_amount greater than 8,000 using filter().
# MAGIC 
# MAGIC **Functions/concepts:** `filter`

# COMMAND ----------
# TODO Question 8
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 9 — Filtering
# MAGIC 
# MAGIC Repeat the previous condition using where().
# MAGIC 
# MAGIC **Functions/concepts:** `where`

# COMMAND ----------
# TODO Question 9
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 10 — Filtering
# MAGIC 
# MAGIC Find confirmed Business or Premium Economy bookings whose ticket_amount is above 9,000.
# MAGIC 
# MAGIC **Functions/concepts:** `filter, multiple conditions`

# COMMAND ----------
# TODO Question 10
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 11 — Filtering
# MAGIC 
# MAGIC Find bookings belonging to SKY, NVA, or ORB using isin().
# MAGIC 
# MAGIC **Functions/concepts:** `isin`

# COMMAND ----------
# TODO Question 11
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 12 — Filtering
# MAGIC 
# MAGIC Find bookings with baggage_kg between 10 and 18 kilograms, inclusive.
# MAGIC 
# MAGIC **Functions/concepts:** `between`

# COMMAND ----------
# TODO Question 12
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 13 — Duplicates
# MAGIC 
# MAGIC Display the unique seat_class values.
# MAGIC 
# MAGIC **Functions/concepts:** `distinct`

# COMMAND ----------
# TODO Question 13
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 14 — Duplicates
# MAGIC 
# MAGIC Remove duplicate records based on booking_id and confirm the new row count.
# MAGIC 
# MAGIC **Functions/concepts:** `dropDuplicates, count`

# COMMAND ----------
# TODO Question 14
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 15 — String functions
# MAGIC 
# MAGIC Trim passenger_name and convert it to title case.
# MAGIC 
# MAGIC **Functions/concepts:** `trim, initcap`

# COMMAND ----------
# TODO Question 15
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 16 — String functions
# MAGIC 
# MAGIC Display passenger_name in uppercase, lowercase, and title case.
# MAGIC 
# MAGIC **Functions/concepts:** `upper, lower, initcap`

# COMMAND ----------
# TODO Question 16
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 17 — String functions
# MAGIC 
# MAGIC Calculate the length of each cleaned passenger name.
# MAGIC 
# MAGIC **Functions/concepts:** `length, trim`

# COMMAND ----------
# TODO Question 17
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 18 — String functions
# MAGIC 
# MAGIC Extract the first five characters of every cleaned passenger name. Remember Spark substring positions start at 1.
# MAGIC 
# MAGIC **Functions/concepts:** `substring`

# COMMAND ----------
# TODO Question 18
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 19 — String functions
# MAGIC 
# MAGIC Create booking_code in the format BOOK-1001 by joining a literal and booking_id.
# MAGIC 
# MAGIC **Functions/concepts:** `concat, lit, cast`

# COMMAND ----------
# TODO Question 19
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 20 — String functions
# MAGIC 
# MAGIC Create booking_summary as Passenger - Airline - Route - Seat Class.
# MAGIC 
# MAGIC **Functions/concepts:** `concat_ws`

# COMMAND ----------
# TODO Question 20
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 21 — String functions
# MAGIC 
# MAGIC Replace repeated spaces inside passenger_name with one space.
# MAGIC 
# MAGIC **Functions/concepts:** `regexp_replace`

# COMMAND ----------
# TODO Question 21
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 22 — String functions
# MAGIC 
# MAGIC Split route_code into an array containing origin code and destination code.
# MAGIC 
# MAGIC **Functions/concepts:** `split`

# COMMAND ----------
# TODO Question 22
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 23 — String functions
# MAGIC 
# MAGIC Find names containing 'an', origin cities starting with 'B', and destination cities ending with 'i'.
# MAGIC 
# MAGIC **Functions/concepts:** `contains, startswith, endswith`

# COMMAND ----------
# TODO Question 23
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 24 — Numeric functions
# MAGIC 
# MAGIC Divide ticket_amount by 3 and show the rounded value (2 decimals), ceiling, and floor.
# MAGIC 
# MAGIC **Functions/concepts:** `round, ceil, floor`

# COMMAND ----------
# TODO Question 24
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 25 — Numeric functions
# MAGIC 
# MAGIC Calculate the absolute difference between ticket_amount and a reference fare of 7,000.
# MAGIC 
# MAGIC **Functions/concepts:** `abs`

# COMMAND ----------
# TODO Question 25
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 26 — Numeric functions
# MAGIC 
# MAGIC Calculate baggage_kg squared.
# MAGIC 
# MAGIC **Functions/concepts:** `pow`

# COMMAND ----------
# TODO Question 26
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 27 — Numeric functions
# MAGIC 
# MAGIC Calculate the square root of ticket_amount.
# MAGIC 
# MAGIC **Functions/concepts:** `sqrt`

# COMMAND ----------
# TODO Question 27
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 28 — Numeric functions
# MAGIC 
# MAGIC Create fare_plus_tax, fare_after_flat_discount, doubled_baggage, and fare_per_kg using arithmetic operators. Use a safe divisor for zero baggage.
# MAGIC 
# MAGIC **Functions/concepts:** `arithmetic operators, when`

# COMMAND ----------
# TODO Question 28
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 29 — Conditional logic
# MAGIC 
# MAGIC Create fare_category: PREMIUM for fare >= 10,000; STANDARD for fare >= 6,000; otherwise BUDGET.
# MAGIC 
# MAGIC **Functions/concepts:** `when, otherwise`

# COMMAND ----------
# TODO Question 29
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 30 — Null handling
# MAGIC 
# MAGIC Display records where promo_discount is null and records where it is not null.
# MAGIC 
# MAGIC **Functions/concepts:** `isNull, isNotNull`

# COMMAND ----------
# TODO Question 30
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 31 — Null handling
# MAGIC 
# MAGIC Replace null promo_discount values with 0 using fillna().
# MAGIC 
# MAGIC **Functions/concepts:** `fillna`

# COMMAND ----------
# TODO Question 31
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 32 — Null handling
# MAGIC 
# MAGIC Remove rows with null satisfaction_score.
# MAGIC 
# MAGIC **Functions/concepts:** `dropna`

# COMMAND ----------
# TODO Question 32
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 33 — Null handling
# MAGIC 
# MAGIC Create final_discount using promo_discount when available, otherwise 0.
# MAGIC 
# MAGIC **Functions/concepts:** `F.coalesce`

# COMMAND ----------
# TODO Question 33
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 34 — Data type conversion
# MAGIC 
# MAGIC Cast booking_id to string, satisfaction_score to integer, and ticket_amount to decimal(10,2). Print the resulting schema.
# MAGIC 
# MAGIC **Functions/concepts:** `cast`

# COMMAND ----------
# TODO Question 34
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 35 — Date functions
# MAGIC 
# MAGIC Convert booking_date and travel_date from strings to DateType columns.
# MAGIC 
# MAGIC **Functions/concepts:** `to_date`

# COMMAND ----------
# TODO Question 35
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 36 — Date functions
# MAGIC 
# MAGIC Add current_date and current_timestamp columns.
# MAGIC 
# MAGIC **Functions/concepts:** `current_date, current_timestamp`

# COMMAND ----------
# TODO Question 36
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 37 — Date functions
# MAGIC 
# MAGIC Extract travel year, month, day of month, and day of week.
# MAGIC 
# MAGIC **Functions/concepts:** `year, month, dayofmonth, dayofweek`

# COMMAND ----------
# TODO Question 37
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 38 — Date functions
# MAGIC 
# MAGIC Format travel_date as dd-MMM-yyyy.
# MAGIC 
# MAGIC **Functions/concepts:** `date_format`

# COMMAND ----------
# TODO Question 38
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 39 — Date functions
# MAGIC 
# MAGIC Calculate booking lead time in days and the months elapsed from booking_date to the current date.
# MAGIC 
# MAGIC **Functions/concepts:** `datediff, months_between`

# COMMAND ----------
# TODO Question 39
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 40 — Date functions
# MAGIC 
# MAGIC Create travel_plus_2_months, travel_plus_7_days, and travel_minus_3_days.
# MAGIC 
# MAGIC **Functions/concepts:** `add_months, date_add, date_sub`

# COMMAND ----------
# TODO Question 40
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 41 — Aggregations
# MAGIC 
# MAGIC Produce one row containing booking count, total fare, average fare, minimum fare, maximum fare, and distinct airline count.
# MAGIC 
# MAGIC **Functions/concepts:** `count, sum, avg, min, max, countDistinct`

# COMMAND ----------
# TODO Question 41
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 42 — Aggregations
# MAGIC 
# MAGIC Create an airline-level report with booking count, average fare, total fare, minimum fare, and maximum fare.
# MAGIC 
# MAGIC **Functions/concepts:** `groupBy, agg`

# COMMAND ----------
# TODO Question 42
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 43 — Aggregations
# MAGIC 
# MAGIC For each seat_class, collect all booking statuses and the unique payment modes.
# MAGIC 
# MAGIC **Functions/concepts:** `collect_list, collect_set`

# COMMAND ----------
# TODO Question 43
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 44 — Sorting
# MAGIC 
# MAGIC Sort bookings by ticket_amount ascending and then descending.
# MAGIC 
# MAGIC **Functions/concepts:** `orderBy, asc, desc`

# COMMAND ----------
# TODO Question 44
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 45 — Sorting
# MAGIC 
# MAGIC Sort by airline_code ascending and ticket_amount descending.
# MAGIC 
# MAGIC **Functions/concepts:** `multi-column orderBy`

# COMMAND ----------
# TODO Question 45
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 46 — Sorting
# MAGIC 
# MAGIC Display the top five most expensive bookings.
# MAGIC 
# MAGIC **Functions/concepts:** `limit`

# COMMAND ----------
# TODO Question 46
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 47 — Joins
# MAGIC 
# MAGIC Perform an inner join between bookings_df and airline_df using airline_code.
# MAGIC 
# MAGIC **Functions/concepts:** `inner join`

# COMMAND ----------
# TODO Question 47
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 48 — Joins
# MAGIC 
# MAGIC Perform a left join and identify bookings whose airline is missing from the master.
# MAGIC 
# MAGIC **Functions/concepts:** `left join`

# COMMAND ----------
# TODO Question 48
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 49 — Joins
# MAGIC 
# MAGIC Perform a right join so that airlines with no bookings are also visible.
# MAGIC 
# MAGIC **Functions/concepts:** `right join`

# COMMAND ----------
# TODO Question 49
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 50 — Joins
# MAGIC 
# MAGIC Perform a full join and inspect both unmatched booking and airline records.
# MAGIC 
# MAGIC **Functions/concepts:** `full join`

# COMMAND ----------
# TODO Question 50
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 51 — Joins
# MAGIC 
# MAGIC Use a left_semi join to return bookings having a valid airline code.
# MAGIC 
# MAGIC **Functions/concepts:** `left_semi`

# COMMAND ----------
# TODO Question 51
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 52 — Joins
# MAGIC 
# MAGIC Use a left_anti join to return bookings having an invalid airline code.
# MAGIC 
# MAGIC **Functions/concepts:** `left_anti`

# COMMAND ----------
# TODO Question 52
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 53 — Joins
# MAGIC 
# MAGIC Create a small seat-class reference DataFrame and cross join it with the list of airline codes.
# MAGIC 
# MAGIC **Functions/concepts:** `cross join`

# COMMAND ----------
# TODO Question 53
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 54 — Union
# MAGIC 
# MAGIC Reorder the columns of new_bookings_df and append it to bookings_df using unionByName().
# MAGIC 
# MAGIC **Functions/concepts:** `unionByName`

# COMMAND ----------
# TODO Question 54
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 55 — Spark SQL
# MAGIC 
# MAGIC Register bookings_df, airline_df, and route_df as temporary views.
# MAGIC 
# MAGIC **Functions/concepts:** `createOrReplaceTempView`

# COMMAND ----------
# TODO Question 55
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 56 — Spark SQL
# MAGIC 
# MAGIC Write SQL to display confirmed bookings above 8,000 ordered by fare descending.
# MAGIC 
# MAGIC **Functions/concepts:** `spark.sql, WHERE, ORDER BY`

# COMMAND ----------
# TODO Question 56
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 57 — Spark SQL
# MAGIC 
# MAGIC Use SQL string functions to clean and format passenger names and calculate name length.
# MAGIC 
# MAGIC **Functions/concepts:** `TRIM, UPPER, LOWER, INITCAP, LENGTH`

# COMMAND ----------
# TODO Question 57
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 58 — Spark SQL
# MAGIC 
# MAGIC Use SQL CASE to create the same fare_category used in the DataFrame assignment.
# MAGIC 
# MAGIC **Functions/concepts:** `CASE WHEN`

# COMMAND ----------
# TODO Question 58
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 59 — Spark SQL
# MAGIC 
# MAGIC Use SQL COALESCE to replace null promo_discount with 0.
# MAGIC 
# MAGIC **Functions/concepts:** `COALESCE`

# COMMAND ----------
# TODO Question 59
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 60 — Spark SQL
# MAGIC 
# MAGIC Create an airline-level aggregation using SQL.
# MAGIC 
# MAGIC **Functions/concepts:** `COUNT, AVG, SUM, MIN, MAX, COUNT DISTINCT`

# COMMAND ----------
# TODO Question 60
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 61 — Spark SQL
# MAGIC 
# MAGIC Join the booking view with airline and route views in SQL.
# MAGIC 
# MAGIC **Functions/concepts:** `SQL JOIN`

# COMMAND ----------
# TODO Question 61
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 62 — Databricks
# MAGIC 
# MAGIC Display sql_airline_aggregation_df and create a bar-chart visualization using airline_code on the X-axis and total_fare on the Y-axis.
# MAGIC 
# MAGIC **Functions/concepts:** `display visualization`

# COMMAND ----------
# TODO Question 62
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 63 — Databricks
# MAGIC 
# MAGIC Optionally save sql_airline_aggregation_df as a managed table and query it again.
# MAGIC 
# MAGIC **Functions/concepts:** `saveAsTable, spark.table`

# COMMAND ----------
# TODO Question 63
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 64 — Execution plan
# MAGIC 
# MAGIC Use explain(mode='formatted') on sql_airline_aggregation_df and identify Scan, Project, Filter, Exchange, HashAggregate, and Sort where present.
# MAGIC 
# MAGIC **Functions/concepts:** `explain`

# COMMAND ----------
# TODO Question 64
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 65 — Spark execution
# MAGIC 
# MAGIC Separate examples of transformations and actions from this assignment. Run count() and collect() only on a small aggregate.
# MAGIC 
# MAGIC **Functions/concepts:** `transformations, actions, collect`

# COMMAND ----------
# TODO Question 65
# Write your PySpark solution below.


# COMMAND ----------
# MAGIC %md
# MAGIC ## Question 66 — Partitions
# MAGIC 
# MAGIC Reduce sql_airline_aggregation_df to one partition using DataFrame.coalesce(1). Explain why this should not be used blindly for large production data.
# MAGIC 
# MAGIC **Functions/concepts:** `DataFrame.coalesce`

# COMMAND ----------
# TODO Question 66
# Write your PySpark solution below.

