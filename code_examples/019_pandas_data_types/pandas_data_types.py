import pandas as pd
import json
import pyarrow
import random
import os
import time

def create_sample_data(n_rows = 1000):

    data = {
        'id': range(n_rows),
        'name': [f'User_{i}' for i in range(n_rows)],
        'age': [random.randint(18, 65) for _ in range(n_rows)],
        'salary': [random.uniform(45000, 150000) for _ in range(n_rows)],
        'department': [random.choice(['Engineering', 'Sales', 'Marketing', 'HR']) for _ in range(n_rows)],
        'active': [random.choice([True, False]) for _ in range(n_rows)]
    }

    return pd.DataFrame(data)

# Create the data frame
print("running pandas_data_types.py")
df = create_sample_data(n_rows=100)
print(f"Created dataframe with {len(df)} rows and {len(df.columns)} columns")
print(df.head())

# Save the data frame to different formats
start = time.time()
df.to_csv("sample_data.csv", index=False)
csv_time = time.time() - start
print("Dataframe saved to sample_data.csv")

start = time.time()
df.to_json("sample_data.json", orient="records", lines=True)
json_time = time.time() - start
print("Dataframe saved to sample_data.json")

start = time.time()
df.to_parquet("sample_data.parquet", index=False)
parquet_time = time.time() - start
print("Dataframe saved to sample_data.parquet")

print()
print("File sizes:")
print(f"sample_data.csv: {os.path.getsize('sample_data.csv')} bytes")
print(f"sample_data.json: {os.path.getsize('sample_data.json')} bytes")
print(f"sample_data.parquet: {os.path.getsize('sample_data.parquet')} bytes")

print()
print("write times:")
print(f"sample_data.csv: {csv_time} seconds")
print(f"sample_data.json: {json_time} seconds")
print(f"sample_data.parquet: {parquet_time} seconds")

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
print("read times:")
print(f"sample_data.csv: {csv_time} seconds")
print(f"sample_data.json: {json_time} seconds")
print(f"sample_data.parquet: {parquet_time} seconds")