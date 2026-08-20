from google.cloud import bigquery

PROJECT_ID = "bigquery-optimization-lab"

client = bigquery.Client(project=PROJECT_ID)

sql = f"""
SELECT
    category,
    COUNT(*) AS number_of_orders,
    SUM(quantity) AS units_sold,
    SUM(quantity * price) AS revenue
FROM `{PROJECT_ID}.streamlit_demo.sales`
GROUP BY category
ORDER BY revenue DESC
"""

query_job = client.query(sql)

df = query_job.to_dataframe()

print(df)
print(df["revenue"].sum())