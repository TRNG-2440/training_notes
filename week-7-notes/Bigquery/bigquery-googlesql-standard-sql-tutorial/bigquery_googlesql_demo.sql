-- BigQuery Standard SQL / GoogleSQL End-to-End Demo
-- Replace YOUR_PROJECT_ID with your actual project ID.

-- 1. Create a temporary training dataset
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.retail_standard_sql`
OPTIONS (
  location = 'US',
  description = 'Temporary GoogleSQL training dataset'
);

-- 2. Create sample data using CTAS (Sandbox-safe)
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retail_standard_sql.orders`
OPTIONS (
  description = 'Temporary retail orders training table',
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
)
AS
SELECT * FROM UNNEST([
  STRUCT(1001 AS order_id, DATE '2026-07-01' AS order_date, 'Bengaluru' AS city,
         'Electronics' AS category, 'Laptop' AS product, 1 AS quantity,
         55000.00 AS unit_price, 5.0 AS discount_pct, 'Delivered' AS status),
  STRUCT(1002, DATE '2026-07-01', 'Chennai', 'Grocery', 'Rice Bag', 2, 1200.00, 0.0, 'Delivered'),
  STRUCT(1003, DATE '2026-07-02', 'Hyderabad', 'Electronics', 'Headphones', 2, 3000.00, 10.0, 'Delivered'),
  STRUCT(1004, DATE '2026-07-02', 'Bengaluru', 'Furniture', 'Office Chair', 1, 8500.00, 8.0, 'Shipped'),
  STRUCT(1005, DATE '2026-07-03', 'Pune', 'Clothing', 'Formal Shirt', 3, 1800.00, 12.0, 'Delivered'),
  STRUCT(1006, DATE '2026-07-03', 'Chennai', 'Electronics', 'Smartphone', 1, 32000.00, 6.0, 'Cancelled'),
  STRUCT(1007, DATE '2026-07-04', 'Mumbai', 'Grocery', 'Cooking Oil', 4, 950.00, 3.0, 'Delivered'),
  STRUCT(1008, DATE '2026-07-04', 'Bengaluru', 'Electronics', 'Monitor', 2, 14000.00, 7.0, 'Delivered'),
  STRUCT(1009, DATE '2026-07-05', 'Hyderabad', 'Furniture', 'Study Table', 1, 12000.00, 5.0, 'Shipped'),
  STRUCT(1010, DATE '2026-07-05', 'Pune', 'Clothing', 'Shoes', 2, 3500.00, 15.0, 'Delivered')
]);

-- 3. Query
SELECT * FROM `YOUR_PROJECT_ID.retail_standard_sql.orders`
ORDER BY order_id;

-- 4. Aggregation
SELECT
  category,
  COUNT(*) AS order_lines,
  SUM(quantity) AS units,
  ROUND(SUM(quantity * unit_price * (1 - discount_pct / 100)), 2) AS net_sales
FROM `YOUR_PROJECT_ID.retail_standard_sql.orders`
WHERE status != 'Cancelled'
GROUP BY category
ORDER BY net_sales DESC;

-- 5. View
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.retail_standard_sql.delivered_orders_v` AS
SELECT order_id, order_date, city, category, product,
       ROUND(quantity * unit_price * (1 - discount_pct / 100), 2) AS net_amount
FROM `YOUR_PROJECT_ID.retail_standard_sql.orders`
WHERE status = 'Delivered';

-- 6. Billing-enabled projects only: DML examples
-- INSERT INTO `YOUR_PROJECT_ID.retail_standard_sql.orders`
-- VALUES (1011, DATE '2026-07-06', 'Delhi', 'Electronics',
--         'Keyboard', 2, 2200.00, 5.0, 'Delivered');

-- UPDATE `YOUR_PROJECT_ID.retail_standard_sql.orders`
-- SET status = 'Delivered'
-- WHERE order_id = 1004;

-- DELETE FROM `YOUR_PROJECT_ID.retail_standard_sql.orders`
-- WHERE status = 'Cancelled';

-- 7. Cleanup option A: remove everything in one command
DROP SCHEMA IF EXISTS `YOUR_PROJECT_ID.retail_standard_sql` CASCADE;

-- Cleanup option B: granular cleanup (run instead of option A)
-- DROP VIEW IF EXISTS `YOUR_PROJECT_ID.retail_standard_sql.delivered_orders_v`;
-- DROP TABLE IF EXISTS `YOUR_PROJECT_ID.retail_standard_sql.orders`;
-- DROP SCHEMA IF EXISTS `YOUR_PROJECT_ID.retail_standard_sql`;
