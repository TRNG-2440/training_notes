from google.cloud import bigquery
import sys

PROJECT_ID = "bigquery-optimization-lab"

client = bigquery.Client(project=PROJECT_ID)

# Read category from terminal
if len(sys.argv) < 2:
    print("Please provide a category.")
    print("Example: python parameterised_query.py Electronics")
    sys.exit()

category_value = sys.argv[1]

print(f"Searching for category: {category_value}")

sql = f"""
SELECT *
FROM `{PROJECT_ID}.streamlit_demo.sales`
WHERE category = @category
"""

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter(
            "category",
            "STRING",
            category_value
        )
    ]
)

df = client.query(
    sql,
    job_config=job_config
).to_dataframe()

print(df)