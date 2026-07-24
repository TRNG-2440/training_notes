# BigQuery: On-Demand vs Reserved Capacity 
## 1. Overview

BigQuery offers two compute pricing models: - On-Demand (Pay per
Query) - Reserved Capacity (BigQuery Editions)

Both use the same execution engine and slots. The difference is how
compute is allocated and billed.

## 2. Slot

A slot is BigQuery's unit of compute used to execute SQL work.

## 3. On-Demand

-   Pay for data processed.
-   Shared slot pool.
-   Best for learning, sandbox, ad-hoc analytics.

Flow:

    User Query
        |
    Optimizer
        |
    Shared Slots
        |
      Result

Pros: - No upfront commitment - Serverless

Cons: - Cost depends on bytes scanned - Performance may vary

## 4. Reserved Capacity

-   Purchase/reserve slot capacity.
-   Dedicated compute.
-   Best for enterprise workloads.

Flow:

    User Query
        |
    Optimizer
        |

Reserved Slots \| Result

Pros: - Predictable cost - Consistent performance

Cons: - Planning required - Idle capacity can cost money

## 5. Comparison

  Feature               On-Demand        Reserved Capacity
  --------------------- ---------------- -------------------
  Billing               Per TB scanned   Per slot capacity
  Slot Source           Shared           Reserved
  Best For              Ad-hoc           Enterprise
  Cost Predictability   Low              High
  Infrastructure        Serverless       Serverless

## 6. Retail Example

Small reporting team: - Use On-Demand.

Large retailer with scheduled ETL and dashboards: - Use Reserved
Capacity.

## 7. Sandbox Demo

1.  Create dataset.
2.  Load retail CSV.
3.  Execute:

``` sql
SELECT category,
SUM(sales_amount) total_sales
FROM retail_orders
GROUP BY category;
```

Observe bytes processed and execution graph.

## 8. Reserved Demo

Run the same query using reserved capacity and compare slot utilization.

## 9. Interview Questions

1.  What is a slot?
2.  Difference between On-Demand and Reserved Capacity?
3.  When should you use reservations?
4.  Does SQL change between models?

## Key Takeaways

-   Same SQL engine.
-   Different billing model.
-   On-Demand for variable workloads.
-   Reserved Capacity for predictable enterprise workloads.
