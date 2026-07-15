from pyspark.sql import SparkSession


spark = (
    SparkSession.builder
    .appName("BroadcastVariableExample")
    .master("local[4]")
    .config("spark.ui.showConsoleProgress", "false")
    .getOrCreate()
)

sc = spark.sparkContext
sc.setLogLevel("ERROR")


# Main distributed data
orders = sc.parallelize(
    [
        (1001, "Laptop", "Electronics", 1, 65000.0),
        (1002, "Chair", "Furniture", 2, 7000.0),
        (1003, "Notebook", "Stationery", 5, 100.0),
    ],
    2,
)


# Small lookup data in driver memory
tax_rates = {
    "Electronics": 0.18,
    "Furniture": 0.12,
    "Stationery": 0.05,
}


# Create the shared read-only variable
tax_rates_broadcast = sc.broadcast(tax_rates)


def calculate_order_amount(order):
    order_id, product, category, quantity, unit_price = order

    gross_amount = quantity * unit_price

    # Access the broadcast value using .value
    tax_rate = tax_rates_broadcast.value.get(category, 0.0)

    tax_amount = gross_amount * tax_rate
    total_amount = gross_amount + tax_amount

    return (
        order_id,
        product,
        category,
        gross_amount,
        tax_rate,
        tax_amount,
        total_amount,
    )


enriched_orders = orders.map(calculate_order_amount)

for result in enriched_orders.collect():
    print(result)


# Remove executor-side cached copies when no longer required
tax_rates_broadcast.unpersist()

spark.stop()