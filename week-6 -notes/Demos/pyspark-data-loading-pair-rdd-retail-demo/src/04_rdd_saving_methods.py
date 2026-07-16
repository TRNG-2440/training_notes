"""Compare RDD saving formats with small examples."""
from retail_common import (
    GENERATED_DIR,
    create_spark,
    file_uri,
    reset_directory,
)


def main() -> None:
    spark = create_spark("04_RDD_Saving_Methods")
    sc = spark.sparkContext

    text_path = GENERATED_DIR / "saving_text"
    gzip_path = GENERATED_DIR / "saving_text_gzip"
    pickle_path = GENERATED_DIR / "saving_pickle"
    sequence_path = GENERATED_DIR / "saving_sequence"

    for path in [text_path, gzip_path, pickle_path, sequence_path]:
        reset_directory(path)

    values = sc.parallelize(["Electronics,204540", "Fashion,25420", "Grocery,9074"], 2)
    values.saveAsTextFile(file_uri(text_path))
    values.saveAsTextFile(file_uri(gzip_path), "org.apache.hadoop.io.compress.GzipCodec")

    objects = sc.parallelize([{"category": "Electronics", "revenue": 204540.0}], 1)
    objects.saveAsPickleFile(file_uri(pickle_path))

    pairs = sc.parallelize([("Electronics", "204540"), ("Fashion", "25420")], 2)
    pairs.saveAsSequenceFile(file_uri(sequence_path))

    print("Text:", text_path)
    print("Compressed text:", gzip_path)
    print("Pickle:", pickle_path)
    print("SequenceFile:", sequence_path)
    spark.stop()


if __name__ == "__main__":
    main()
