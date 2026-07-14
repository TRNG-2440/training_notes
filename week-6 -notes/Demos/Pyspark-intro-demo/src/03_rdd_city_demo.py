from pyspark.sql import SparkSession

def main()->None:
    spark=(
        SparkSession.builder
        .appName("RDDCityCount-RDD -Demo")
        .master("local[*]")
        .getOrCreate()
    )
    
    cities= spark.sparkContext.parallelize([
        "Phoenix","Scottsdale","Phoenix","Scottsdale","Tempe","Mesa","Tucson"
    ],2)
    
    city_counts=(cities
                 .map( lambda city:(city,1))
                 .reduceByKey(lambda left,right:left+right)
                 .sortByKey()
                 )
    
    print("City Counts: ",city_counts)
    
    for city,count in city_counts.collect():
        print(f"{city} : {count}")
        
    spark.stop()
    
if __name__=="__main__":
    main()
    
    