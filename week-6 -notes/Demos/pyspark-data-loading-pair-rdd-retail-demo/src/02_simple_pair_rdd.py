"""A small Pair-RDD example before the complete industry pipeline."""
from retail_common import create_spark


def main() -> None:
    spark = create_spark("02_Simple_Pair_RDD")
    sc = spark.sparkContext

    sales = [
        ("Electronics", 47500.0),
        ("Grocery", 1200.0),
        ("Fashion", 4860.0),
        ("Electronics", 57040.0),
        ("Grocery", 1862.0),
    ]

    # Each element already has the Pair-RDD shape: (key, value).
    sales_pair_rdd = sc.parallelize(sales, 3)

    totals = sales_pair_rdd.reduceByKey(lambda left, right: left + right)
    sorted_totals = totals.sortBy(lambda item: item[1], ascending=False)

    print("Input Pair RDD:", sales_pair_rdd.collect())
    print("Revenue by category:", sorted_totals.collect())
    print("Electronics values:", sales_pair_rdd.lookup("Electronics"))
    print("Records per key:", dict(sales_pair_rdd.countByKey()))

    spark.stop()


if __name__ == "__main__":
    main()
