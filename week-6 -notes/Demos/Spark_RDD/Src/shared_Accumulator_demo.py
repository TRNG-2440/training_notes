from pyspark.sql import SparkSession


spark = (
    SparkSession.builder
    .appName("AccumulatorExample")
    .master("local[4]")
    .config("spark.ui.showConsoleProgress", "false")
    .getOrCreate()
)

sc = spark.sparkContext
sc.setLogLevel("ERROR")


orders = sc.parallelize(
    [
        (1001, "Laptop", "Electronics", 1, 65000.0),
        (1002, "Chair", "Furniture", -2, 7000.0),
        (1003, "Notebook", "Stationery", 5, 100.0),
        (1004, "Mouse", "Electronics", 0, 800.0),
    ],
    2,
)


# Create an integer accumulator with initial value 0
invalid_quantity_count = sc.accumulator(0)


def inspect_order(order):
    quantity = order[3]

    if quantity <= 0:
        invalid_quantity_count.add(1)


# foreach() is an action and triggers RDD execution
orders.foreach(inspect_order)


# Only the driver reads the final value
print(
    "Orders with invalid quantity:",
    invalid_quantity_count.value,
)


spark.stop()