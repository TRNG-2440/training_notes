from pyspark.sql import SparkSession


def create_spark_session(app_name: str) -> SparkSession:
    """
    Create a local SparkSession for VS Code exercises.

    local[*] means:
    - Run Spark on this computer.
    - Use all available logical CPU cores.
    """

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.ui.showConsoleProgress", "true")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")
    return spark