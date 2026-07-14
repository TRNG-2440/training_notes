from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def main() -> None:
    spark=(
        SparkSession.builder
        .appName("TriprevenueDataframe")
        .master("local[*]")
        .getOrCreate()
    )
    
    
    trips =[
        (101, "New York", 250.0),
        (102, "Chicago", 400.0),
        (103, "New York", 300.0),
        (104, "Dallas", 550.0),
        (105, "Chicago", 475.0)
    ]
    
    
    trip_df=spark.createDataFrame(
        trips,
        ["trips_id","city","fare"]
        )
    
    print("Original Data")
    trip_df.show()
    
    print("Schema")
    trip_df.printSchema()
    
    revenue_by_city=(
        trip_df
        .groupBy("city")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.sum("fare"),2).alias("total_revenue"),
            F.round(F.avg("fare"),2).alias("average_fare"),
            )
        .orderBy(F.desc("total_revenue"))
        )
    
    print("Revenue By City : ")
    revenue_by_city.show()
    
    print("Execution plan")
    revenue_by_city.explain()
    
    
    spark.stop()
    
if __name__=="__main__":
    main()