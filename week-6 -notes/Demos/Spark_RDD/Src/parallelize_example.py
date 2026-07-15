from spark_setup import create_spark_session


def main() -> None:
    spark = create_spark_session("ParallelizeExample")
    sc = spark.sparkContext

    numbers = [10, 20, 30, 40, 50]

    # numbers_rdd = sc.parallelize(numbers)
#     numbers_rdd = sc.parallelize(
#     [10, 20, 30, 40, 50, 60],
#     numSlices=3
# )
#     print("RDD elements:", numbers_rdd.collect())
#     print("Number of elements:", numbers_rdd.count())
#     print("Number of partitions:", numbers_rdd.getNumPartitions())


    employees = [
        (101, "Anu"),
        (102, "Bala"),
        (103, "Charan")
    ]

    employee_rdd = sc.parallelize(employees, 2)

    print(employee_rdd.collect())
    print(employee_rdd.keys().collect())
    print(employee_rdd.values().collect())
    spark.stop()


if __name__ == "__main__":
    main()