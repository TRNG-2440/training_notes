from __future__ import annotations
import csv
from io import StringIO
from pathlib import Path
from typing import Iterator

from retail_common import DATA_DIR,GENERATED_DIR,create_spark,ORDER_FIELDS,file_uri,reset_directory

def parse_csv_line(line: str) -> list[str]:
    """
    Parse a CSV line into a list of values.
    """
    return next(csv.reader(StringIO(line)))

def format_output_partition(
    partition_index: int, 
    rows: Iterator[tuple[str, float]],
) -> Iterator[str]:
    """
    Convert Pair-RDD rows into csv text and add a header to the first partition.
    """
    if partition_index == 0:
        yield "category,total_completed_revenue"
        
    for category,revenue in rows:
        yield f"{category},{revenue:.2f}"
    
def main()->None:
    # STEP 1: Create a Spark session in local mode
    spark = create_spark("01_rdd_loading_methods and Saving Results")
    sc=spark.sparkContext
    
    try:
        #STEP 2: define the local paths.
        input_path = DATA_DIR / "retail_orders.csv"
        output_path= GENERATED_DIR / "completed_revenue_by_category"  
    
        print("\n STEP 1 - Input and output paths")
        print(f"Input path: {input_path}")
        print(f"Output path: {output_path}")
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}\n"
                                    "place retail_orders.csv into the data directory.")
        
        # spark will not overwrite an existing output directory, so delete it first if it exists
        reset_directory(output_path)
        
        #STEP 3: Load the CSV file into an RDD of strings
        raw_lines_rdd = sc.textFile(file_uri(input_path),minPartitions=2)
        
        print("\n STEP 2 - RAW FILE LOADING")
        print("Total lines in the raw file:",raw_lines_rdd.count())
        print("First CSV line:",raw_lines_rdd.first())
        
        #STEP 4: Remove the header and empty line
        header = raw_lines_rdd.first()
        data_lines_rdd = raw_lines_rdd.filter(
            lambda line: line != header and line.strip()!="")
        
        print("\n STEP 3 - HEADER REMOVAL")
        print("Total data lines after removing header:",data_lines_rdd.count())
        
        #STEP 5: Parse the CSV line
        parsed_rdd = data_lines_rdd.map(parse_csv_line)
        
        print("\n STEP 4 - CSV PARSING")
        print("First parsed line:",parsed_rdd.first())
        
        #STEP 6: Filtering only completed orders
        completed_orders_rdd = parsed_rdd.filter(
            lambda values: len(values) == 9 and values[8] == "COMPLETED")
        
        print("STEP 5 - FILTERING COMPLETED ORDERS")
        print("Total completed orders:",completed_orders_rdd.count())
        
        #STEP 7: Create Pair RDD: (category, net_amount).
        category_revenue_pair_rdd = completed_orders_rdd.map(
            lambda values: (values[4], float(values[6])*(1-float(values[7])/100.0),)
        )
        
        print("\n STEP 6 - PAIR RDD CREATION")
        for item in category_revenue_pair_rdd.take(5):
            print(" ", item)
            
        #STEP _ Add revenue values for each category
        revenue_by_category_rdd = (
            category_revenue_pair_rdd
            .reduceByKey( lambda left,right:left+ right)
            .mapValues(lambda revenue: round(revenue,2))
            .sortBy(lambda item:item[1],ascending=False)
            )
        
        print ("\n STEP 7 - AGGREGATION AND SORTING")
        for category,revenue in revenue_by_category_rdd.collect():
            print(f"  {category:20}: {revenue:.2f}")
            
        #STEP 8: Convert tuples into csv text
        
        output_lines_rdd=(
            revenue_by_category_rdd
            .coalesce(1)
            .mapPartitionsWithIndex(format_output_partition)
        )
        
        output_rows=revenue_by_category_rdd.collect()
        
       # STEP 9: Save using Python instead of saveAsTextFile().
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / "completed_revenue_by_category.csv"

        with output_file.open(
            mode="w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(
                ["category", "total_completed_revenue"]
            )

            for category, revenue in output_rows:
                writer.writerow(
                    [category, f"{revenue:.2f}"]
                )

        print("\nSTEP 8 - SAVING")
        print("Output file:", output_file)

        # STEP 10: Load the saved file again using Python.
        print("\nSTEP 9 - VERIFY SAVED OUTPUT")

        with output_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line in file:
                print(line.rstrip())

        print("\nDEMO COMPLETED SUCCESSFULLY")
    finally:
        spark.stop()
    
    
if __name__ == "__main__":
    main()