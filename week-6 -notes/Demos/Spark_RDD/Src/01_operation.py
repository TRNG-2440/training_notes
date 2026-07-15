from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("PythonPracticalRDD")
         .master("local[4]")
         .getOrCreate())

sc = spark.sparkContext
sc.setLogLevel("WARN")

transactions_data = [
    (1001, "C101", "Laptop",      "Electronics", 1, 65000.0, "Chennai",   "PAID"),
    (1002, "C102", "Mouse",       "Electronics", 2,   800.0, "Coimbatore","PAID"),
    (1003, "C101", "Keyboard",    "Electronics", 1,  1500.0, "Chennai",   "PAID"),
    (1004, "C103", "Chair",       "Furniture",   1,  7000.0, "Bengaluru", "PENDING"),
    (1005, "C104", "Desk",        "Furniture",   1, 12000.0, "Hyderabad", "PAID"),
    (1006, "C105", "Notebook",    "Stationery",  5,   100.0, "Chennai",   "PAID"),
    (1007, "C102", "USB Cable",   "Electronics", 3,   300.0, "Coimbatore","CANCELLED"),
    (1008, "C106", "Monitor",     "Electronics", 2, 15000.0, "Hyderabad", "PAID"),
    (1009, "C103", "Pen",         "Stationery", 10,    20.0, "Bengaluru", "PAID"),
    (1010, "C107", "Office Lamp", "Furniture",   2,  1200.0, "Chennai",   "PAID"),
]

transactions = sc.parallelize(transactions_data, 4)
products = sc.parallelize([
    ("Laptop", "Premium"), ("Mouse", "Standard"), ("Keyboard", "Standard"),
    ("Chair", "Standard"), ("Desk", "Premium"), ("Notebook", "Budget"),
    ("USB Cable", "Budget"), ("Monitor", "Premium"), ("Pen", "Budget"),
    ("Office Lamp", "Standard")
], 2)


 # print(products.collect())
TXN_ID = 0
CUSTOMER_ID = 1
PRODUCT = 2
CATEGORY = 3
QTY = 4
PRICE = 5
CITY = 6
STATUS = 7

#rs_df=[tr]
city_revenue = (transactions
    .filter(lambda t: t[STATUS] == "PAID")
    .map(lambda t: (t[CITY], t[QTY] * t[PRICE]))
    .reduceByKey(lambda a, b: a + b, numPartitions=2))

print(city_revenue.toDebugString().decode("utf-8"))
print(city_revenue.collect())

#print(products.collect())


spark.stop()