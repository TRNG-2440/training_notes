-- ============================================================
-- BIGQUERY CLUSTERING: COLUMN-LEVEL SORTING END-TO-END DEMO
-- Real-world scenario: Retail order analytics
-- Moderate volume: 150,000 rows
-- Replace YOUR_PROJECT_ID before execution.
-- ============================================================

-- STEP 1: Create dataset
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.retail_clustering_lab`
OPTIONS (
  location = 'US',
  description = 'Training dataset for BigQuery clustering demo'
);

-- STEP 2: Create a moderate source table without clustering
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retail_clustering_lab.orders_unclustered`
AS
WITH generated_orders AS (
  SELECT
    order_number,
    DATE_ADD(DATE '2025-01-01', INTERVAL MOD(order_number, 180) DAY) AS order_date,
    CONCAT('CUST-', LPAD(CAST(MOD(order_number * 17, 10000) + 1 AS STRING), 5, '0')) AS customer_id,
    ['South','North','East','West'][OFFSET(MOD(order_number, 4))] AS region,
    ['Electronics','Grocery','Fashion','Furniture','Sports'][OFFSET(MOD(order_number * 3, 5))] AS category,
    ['Completed','Pending','Cancelled','Returned'][OFFSET(MOD(order_number * 7, 4))] AS order_status,
    MOD(order_number * 11, 8) + 1 AS quantity,
    ROUND(50 + MOD(order_number * 29, 4950) + RAND() * 100, 2) AS unit_price,
    CONCAT(
      'Retail order generated for clustering demonstration. ',
      REPEAT('Training data block content. ', 8)
    ) AS order_description
  FROM UNNEST(GENERATE_ARRAY(1, 150000)) AS order_number
)
SELECT
  order_number AS order_id,
  order_date,
  customer_id,
  region,
  category,
  order_status,
  quantity,
  unit_price,
  ROUND(quantity * unit_price, 2) AS order_amount,
  order_description
FROM generated_orders;

-- STEP 3: Inspect volume
SELECT
  COUNT(*) AS row_count,
  MIN(order_date) AS minimum_date,
  MAX(order_date) AS maximum_date,
  COUNT(DISTINCT customer_id) AS customers,
  COUNT(DISTINCT region) AS regions,
  COUNT(DISTINCT category) AS categories
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_unclustered`;

-- STEP 4: Create clustered table
-- Column order matters:
--   1. region
--   2. category
--   3. customer_id
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
CLUSTER BY region, category, customer_id
AS
SELECT *
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_unclustered`;

-- STEP 5: Verify clustering metadata
SELECT
  table_name,
  ddl
FROM `YOUR_PROJECT_ID.retail_clustering_lab.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('orders_unclustered', 'orders_clustered');

SELECT
  table_name,
  clustering_ordinal_position,
  column_name
FROM `YOUR_PROJECT_ID.retail_clustering_lab.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'orders_clustered'
  AND clustering_ordinal_position IS NOT NULL
ORDER BY clustering_ordinal_position;

-- STEP 6A: Baseline query on unclustered table
SELECT
  region,
  category,
  COUNT(*) AS order_count,
  ROUND(SUM(order_amount), 2) AS revenue
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_unclustered`
WHERE region = 'South'
  AND category = 'Electronics'
  AND customer_id BETWEEN 'CUST-02000' AND 'CUST-02999'
GROUP BY region, category;

-- STEP 6B: Same query on clustered table
SELECT
  region,
  category,
  COUNT(*) AS order_count,
  ROUND(SUM(order_amount), 2) AS revenue
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE region = 'South'
  AND category = 'Electronics'
  AND customer_id BETWEEN 'CUST-02000' AND 'CUST-02999'
GROUP BY region, category;

-- STEP 7: Test column order
-- Best: starts with first clustering column
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE region = 'South';

-- Better: first + second clustering columns
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE region = 'South'
  AND category = 'Electronics';

-- Strong: first + second + third
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE region = 'South'
  AND category = 'Electronics'
  AND customer_id = 'CUST-02500';

-- Less effective: skips the leading clustering column
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE category = 'Electronics';

-- Less effective: filters only the third clustering column
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE customer_id = 'CUST-02500';

-- STEP 8: Good and bad filter expressions
-- Good: simple filter directly on clustered column
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE customer_id = 'CUST-02500';

-- Bad: function applied to clustered column may reduce block pruning
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_clustered`
WHERE LOWER(customer_id) = 'cust-02500';

-- STEP 9: Optional production design:
-- Partition by date, cluster inside every date partition
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retail_clustering_lab.orders_partitioned_clustered`
PARTITION BY order_date
CLUSTER BY region, category, customer_id
AS
SELECT *
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_unclustered`;

-- STEP 10: Combined partition + clustering query
SELECT
  order_date,
  region,
  category,
  COUNT(*) AS order_count,
  ROUND(SUM(order_amount), 2) AS revenue
FROM `YOUR_PROJECT_ID.retail_clustering_lab.orders_partitioned_clustered`
WHERE order_date BETWEEN DATE '2025-03-01' AND DATE '2025-03-31'
  AND region = 'South'
  AND category = 'Electronics'
GROUP BY order_date, region, category
ORDER BY order_date;

-- STEP 11: Cleanup when the lab is complete
-- DROP SCHEMA `YOUR_PROJECT_ID.retail_clustering_lab` CASCADE;