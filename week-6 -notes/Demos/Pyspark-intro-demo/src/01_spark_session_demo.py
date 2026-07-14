from pyspark.sql import SparkSession
import os

def main() ->None:
    spark= (
        SparkSession.builder
        .appName("SparkSessionDemo")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    
    print("Spark Session created Successfully")
    print("Spark Version: ",spark.version)
    print("Application Name : ",spark.sparkContext.appName)
    print("master : ",spark.sparkContext.master)
    print("Default parallelism : ",spark.sparkContext.defaultParallelism)
    print("Cpu count :" ,os.cpu_count())
    spark.stop()
    
if __name__ == "__main__":
    main()
    