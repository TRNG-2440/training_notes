import pandas as pd
import json
import pyarrow
import random
import os
import time

print("running pandas_read_format.py")


# Save the data frame to different formats
start = time.time()
df = pd.read_csv("sample_data.csv")
csv_time = time.time() - start
print("Dataframe read from sample_data.csv")

start = time.time()
df = pd.read_json("sample_data.json", orient="records", lines=True)
json_time = time.time() - start
print("Dataframe read from sample_data.json")

start = time.time()
df =  pd.read_parquet("sample_data.parquet")
parquet_time = time.time() - start
print("Dataframe read from sample_data.parquet")

print()
print("File sizes:")
print(f"sample_data.csv: {os.path.getsize('sample_data.csv')} bytes")
print(f"sample_data.json: {os.path.getsize('sample_data.json')} bytes")
print(f"sample_data.parquet: {os.path.getsize('sample_data.parquet')} bytes")

print()
print("read times:")
print(f"sample_data.csv: {csv_time} seconds")
print(f"sample_data.json: {json_time} seconds")
print(f"sample_data.parquet: {parquet_time} seconds")