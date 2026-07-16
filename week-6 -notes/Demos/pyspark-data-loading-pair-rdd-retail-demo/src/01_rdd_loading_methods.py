"""Demonstrate common RDD data-loading methods in local VS Code."""

from retail_common import (
    DATA_DIR,
    GENERATED_DIR,
    create_spark,
    file_uri,
    reset_directory,
)


def main() -> None:
    spark = create_spark("01_RDD_Loading_Methods")
    sc = spark.sparkContext

    try:
        # 1. Local Python collection -> RDD.
        collection_rdd = sc.parallelize([10, 20, 30, 40], 2)
        print("parallelize:", collection_rdd.collect())

        # 2. Text / CSV file -> one string per line.
        orders_path = DATA_DIR / "retail_orders.csv"

        print("Python file path :", orders_path)
        print("File exists      :", orders_path.exists())
        print("Spark input path :", file_uri(orders_path))

        if not orders_path.exists():
            raise FileNotFoundError(
                f"Input file was not found: {orders_path}"
            )

        text_rdd = sc.textFile(file_uri(orders_path), 4)

        print(
            "textFile count including header:",
            text_rdd.count(),
        )
        print("textFile first line:", text_rdd.first())

        # # 3. wholeTextFiles requires Hadoop Windows native support
        # # when listing a local directory.
        # print(
        #     "\nwholeTextFiles skipped on Windows because "
        #     "HADOOP_HOME/winutils.exe is not configured."
        # )

        # # Python-based equivalent for classroom demonstration.
        # print("\nFiles available inside data folder:")

        # for input_file in DATA_DIR.glob("*"):
        #     if input_file.is_file():
        #         content = input_file.read_text(
        #             encoding="utf-8-sig"
        #         )

        #         print(
        #             input_file.name,
        #             "characters=",
        #             len(content),
        #         )

        # # 4. Pickle file round trip.
        # pickle_path = GENERATED_DIR / "loading_demo_pickle"
        # reset_directory(pickle_path)

        # collection_rdd.saveAsPickleFile(
        #     file_uri(pickle_path)
        # )

        # loaded_pickle = sc.pickleFile(
        #     file_uri(pickle_path)
        # )

        # print("pickleFile:", loaded_pickle.collect())

        # # 5. SequenceFile round trip.
        # sequence_path = (
        #     GENERATED_DIR / "loading_demo_sequence"
        # )

        # reset_directory(sequence_path)

        # pair_rdd = sc.parallelize(
        #     [
        #         ("Electronics", "204540"),
        #         ("Grocery", "9074"),
        #     ]
        # )

        # pair_rdd.saveAsSequenceFile(
        #     file_uri(sequence_path)
        # )

        # loaded_sequence = sc.sequenceFile(
        #     file_uri(sequence_path)
        # )

        # print(
        #     "sequenceFile:",
        #     loaded_sequence.collect(),
        # )

        # 6. DataFrame -> RDD.
        frame = spark.createDataFrame(
            [
                ("Electronics", 5),
                ("Grocery", 6),
            ],
            ["category", "orders"],
        )

        dataframe_rdd = frame.rdd.map(
            lambda row: (
                row.category,
                row.orders,
            )
        )

        print(
            "DataFrame.rdd:",
            dataframe_rdd.collect(),
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()