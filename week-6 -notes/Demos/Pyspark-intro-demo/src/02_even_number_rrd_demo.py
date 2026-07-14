from pyspark.sql import SparkSession

def main()->None:
    spark=(
        SparkSession.builder
        .appName("evenNumber-RDD -Demo")
        .master("local[*]")
        .getOrCreate()
    )
    
    numbers= spark.sparkContext.parallelize(
        [1,2,3,4,5,6,7,8],2
    )
    
    even_numbers=numbers.filter(
        lambda number:number%2 ==0
    )
    print("Number of Partitions: ",numbers.getNumPartitions())
    print("Even_Number :",even_numbers)
    print(" Even Numbers Count: ",even_numbers.count())
    
    spark.stop()
if __name__ == "__main__":
    main()
    