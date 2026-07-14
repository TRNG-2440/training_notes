from pyspark.sql import SparkSession

spark=SparkSession.builder\
    .appName("Demo")\
    .master("local[*]")\
    .getOrCreate()
    
numbers=spark.sparkContext.parallelize([1,2,3,4,5,6,7,8],2)


even_numbers=numbers.filter(lambda number:number  % 2 ==0)
spark.stop()