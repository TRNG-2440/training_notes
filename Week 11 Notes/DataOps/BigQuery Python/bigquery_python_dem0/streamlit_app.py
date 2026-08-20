import streamlit as st
from google.cloud import bigquery
from datetime import datetime
import time

PROJECT_ID = "bigquery-optimization-lab"


# =========================================================
# BIGQUERY CLIENT
# =========================================================

@st.cache_resource
def get_bigquery_client():
    return bigquery.Client(project=PROJECT_ID)


# =========================================================
# CACHED BIGQUERY QUERY
# Each category gets its own cache entry.
#
# Electronics -> one cache
# Furniture   -> another cache
# Stationery  -> another cache
#
# Cache lasts 300 seconds = 5 minutes
# =========================================================

@st.cache_data(ttl=300)
def load_sales_data(category):

    client = get_bigquery_client()

    # IMPORTANT:
    # This time is created ONLY when this function
    # actually executes.
    #
    # If Streamlit returns cached data,
    # this time will remain unchanged.
    query_executed_at = datetime.now().strftime("%H:%M:%S")

    if category == "All":

        sql = f"""
        SELECT
            product,
            category,
            quantity,
            price,
            quantity * price AS total_amount
        FROM `{PROJECT_ID}.streamlit_demo.sales`
        ORDER BY order_id
        """

        query_job = client.query(sql)

    else:

        sql = f"""
        SELECT
            product,
            category,
            quantity,
            price,
            quantity * price AS total_amount
        FROM `{PROJECT_ID}.streamlit_demo.sales`
        WHERE category = @category
        ORDER BY order_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "category",
                    "STRING",
                    category
                )
            ]
        )

        query_job = client.query(
            sql,
            job_config=job_config
        )

    df = query_job.to_dataframe()

    # This job ID changes whenever a NEW BigQuery
    # query job is created.
    job_id = query_job.job_id

    # Add execution time to result just for demonstration
    df["query_executed_at"] = query_executed_at

    return df, query_executed_at, job_id


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="BigQuery Cache Demo",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ BigQuery Streamlit Cache Demo")


st.info(
    """
    **Cache TTL = 300 seconds = 5 minutes**

    Each filter value has its own cached result.

    Try:

    Electronics → Furniture → Stationery → Electronics

    Return to Electronics within 5 minutes.
    """
)


# =========================================================
# FILTER
# =========================================================

category = st.selectbox(
    "Select Category",
    [
        "All",
        "Electronics",
        "Furniture",
        "Stationery"
    ]
)


# =========================================================
# CURRENT STREAMLIT RERUN TIME
# This is OUTSIDE the cached function.
#
# Therefore this changes on every Streamlit rerun.
# =========================================================

current_rerun_time = datetime.now().strftime("%H:%M:%S")

st.write(
    f"### Current Streamlit rerun time: {current_rerun_time}"
)


# =========================================================
# CALL CACHED FUNCTION
# =========================================================

start = time.perf_counter()

df, query_executed_at, job_id = load_sales_data(category)

elapsed = time.perf_counter() - start


# =========================================================
# DETECT CACHE BEHAVIOR FOR DEMONSTRATION
# =========================================================

st.subheader("Cache Result Information")


if query_executed_at == current_rerun_time:

    st.warning(
        "🐢 BIGQUERY QUERY EXECUTED / CACHE MISS"
    )

else:

    st.success(
        "⚡ STREAMLIT CACHE HIT — BigQuery was NOT executed again"
    )


# =========================================================
# DETAILS
# =========================================================

col1, col2 = st.columns(2)

with col1:

    st.write("### Selected Category")

    st.write(category)

    st.write("### BigQuery originally executed at")

    st.write(query_executed_at)


with col2:

    st.write("### Current Streamlit rerun time")

    st.write(current_rerun_time)

    st.write("### Function response time")

    st.write(f"{elapsed:.4f} seconds")


# =========================================================
# BIGQUERY JOB ID
# =========================================================

st.write("### BigQuery Job ID")

st.code(job_id)

st.caption(
    """
    When the same category comes from Streamlit cache,
    the BigQuery Job ID should remain the same.

    A new Job ID normally means a new BigQuery query job
    was created.
    """
)


# =========================================================
# SALES DATA
# =========================================================

st.subheader("Sales Data")

st.dataframe(
    df,
    use_container_width=True
)


# =========================================================
# REVENUE CHART
# =========================================================

st.subheader("Revenue by Category")

summary = (
    df.groupby("category")["total_amount"]
      .sum()
      .reset_index()
)

st.bar_chart(
    summary,
    x="category",
    y="total_amount"
)


# =========================================================
# CLEAR CACHE
# =========================================================

st.divider()

if st.button("🗑️ Clear Streamlit Cache"):

    load_sales_data.clear()

    st.success(
        "Cache cleared. Select a category again."
    )