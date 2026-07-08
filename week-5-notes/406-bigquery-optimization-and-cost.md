# BigQuery Optimization and Cost

## Learning Objectives
- Explain BigQuery's **cost model**: bytes scanned, on-demand vs flat-rate, and the 1 TB/month free tier.
- Use a **dry run** to estimate a query's cost *before* running it.
- Apply the top optimizations: avoid `SELECT *`, filter partitions, limit columns, and materialize repeated work.
- Recognize the cost pitfalls that surprise newcomers.

## Why This Matters
BigQuery's superpower — scanning terabytes in seconds — is also how it bills you. A careless `SELECT *` over a big table can scan (and charge for) far more data than the question needed. The single most valuable habit a data engineer can build with BigQuery is **knowing a query's cost before pressing run**, and shaping queries to scan less. This note turns the "bytes scanned" idea from notes 402/405 into concrete money and habits.

## Concept Explanation

### The Cost Model
BigQuery has two separable costs:

| Cost | What you pay for | Notes |
|------|------------------|-------|
| **Storage** | GB stored per month | Active vs long-term (untouched 90 days) is cheaper; ~cents/GB |
| **Compute (query)** | **Bytes scanned** by the query | This is the one you control per query |

For **query** cost there are two pricing modes:

| Mode | How it works | Best for |
|------|--------------|----------|
| **On-demand** | Pay per **TB scanned**. **First 1 TB/month free**, then ~$6.25/TB | Variable / exploratory workloads, learning |
| **Capacity (flat-rate / editions)** | Reserve **slots** (compute) for a flat price; queries don't pay per byte | High, predictable volume |

The number that matters on-demand is **bytes scanned**, and — crucially — it depends on the **columns and partitions you touch**, *not* the rows you return. `LIMIT 10` does **not** reduce cost; the scan happens before the limit.

```
Cost driver:  bytes SCANNED (columns x partitions read)
NOT:          rows returned, LIMIT, or query runtime
```

Because BigQuery is **columnar**, selecting fewer columns scans fewer bytes — this is the biggest lever after partition pruning.

### Dry Runs: Cost Before You Run
A **dry run** validates the SQL and reports exactly how many bytes it *would* scan, **without running it or charging you**. Do this before any query over a large table.

**In the console:** the editor shows "This query will process X when run" in the top-right before you click Run.

**With the `bq` CLI:**
```bash
bq query --dry_run --use_legacy_sql=false \
  'SELECT order_id FROM `bigquery-public-data.thelook_ecommerce.order_items`'
# Query successfully validated. Assuming the query is run, it would process 12345678 bytes.
```

**In Python:**
```python
from google.cloud import bigquery
client = bigquery.Client()

sql = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.order_items`"
cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
job = client.query(sql, job_config=cfg)   # not executed
gb = job.total_bytes_processed / 1e9
print(f"Would scan {gb:.2f} GB  ~ ${gb/1000*6.25:.4f}")
```

> DuckDB has **no billing and no dry-run cost**, because it runs locally against your own CPU/disk — nothing to charge. To *approximate* the lesson offline, use `EXPLAIN` / `EXPLAIN ANALYZE` to see the plan and rows read. The habit ("estimate before you scan") is what transfers; the dollar figure only exists on BigQuery.

### The Optimization Playbook
In rough order of impact:

**1. Never `SELECT *` on wide/large tables.** Name the columns you need. On a 40-column table, selecting 3 columns can scan ~1/13th of the data.
```sql
-- Bad: scans all columns
SELECT * FROM `...order_items` WHERE created_at >= '2023-01-01';
-- Good: scans 4 columns
SELECT order_id, product_id, sale_price, created_at
FROM `...order_items` WHERE created_at >= '2023-01-01';
```

**2. Filter on the partition column** so pruning kicks in (note 405). Filter the raw column — don't wrap it in a function.

**3. Cluster + filter/group on high-cardinality IDs** to prune within partitions.

**4. Materialize repeated work.** If a heavy aggregation is queried often, store it (a table, a **materialized view**, or a scheduled query) instead of recomputing every time.

**5. Prune early, join late.** Filter and aggregate in CTEs before joining, so joins operate on fewer rows.

**6. Use `APPROX_*` functions** (`APPROX_COUNT_DISTINCT`) when exactness isn't required — far cheaper on huge cardinalities.

**7. Preview instead of query** for a peek. The table **Preview** tab and `tabledata.list` are **free** — no scan. Don't `SELECT * LIMIT 100` just to eyeball data.

**8. Leverage the query cache.** Identical queries return cached results **for free** within ~24h (as long as underlying data is unchanged).

### Cost Pitfalls (the surprises)
| Pitfall | Why it bites | Fix |
|---------|--------------|-----|
| `SELECT *` "just to see" | Scans every column | Preview tab, or name columns |
| `LIMIT` "to be safe" | Doesn't reduce scan | Filter partitions/columns instead |
| Function on partition col | Kills pruning | Filter the raw column |
| Re-running the same heavy report | Pays each time | Materialize / cache / scheduled query |
| Streaming small rows constantly | Per-row streaming charge | Batch-load when sub-second isn't needed |
| Cross-region joins | Not allowed / extra cost | Keep datasets in one location |

Set a **custom quota / maximum bytes billed** as a guardrail:
```python
cfg = bigquery.QueryJobConfig(maximum_bytes_billed=10 * 1024**3)  # cap at 10 GB
client.query(sql, job_config=cfg)  # errors out instead of overspending
```

## Code Example
A reusable cost-estimator that dry-runs any query and prints GB + a dollar estimate — the exact helper associates build in exercise 402.

```python
from google.cloud import bigquery

client = bigquery.Client()
ON_DEMAND_USD_PER_TB = 6.25

def estimate(sql: str) -> float:
    """Dry-run a query; return estimated on-demand USD (0 within free tier)."""
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=cfg)
    tb = job.total_bytes_processed / 1e12
    usd = tb * ON_DEMAND_USD_PER_TB
    print(f"{job.total_bytes_processed/1e9:8.3f} GB  ~ ${usd:.4f}")
    return usd

wide = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.order_items`"
narrow = ("SELECT order_id, sale_price FROM "
          "`bigquery-public-data.thelook_ecommerce.order_items` "
          "WHERE created_at >= '2023-01-01'")

print("SELECT *      :", end=" "); estimate(wide)
print("narrow+filter :", end=" "); estimate(narrow)
# The narrow query scans a fraction of the bytes for the same rows.
```

## Key Takeaways
- On-demand cost = **bytes scanned**, driven by **columns x partitions read** — not rows returned, not `LIMIT`, not runtime.
- **First 1 TB/month is free**; after that ~$6.25/TB on-demand. Flat-rate/editions reserve slots for predictable heavy use.
- **Dry-run every query over a big table** (console estimate, `bq --dry_run`, or Python `dry_run=True`) to see the cost before paying it.
- Top levers: **name columns (no `SELECT *`)**, **filter the partition column**, cluster + filter on IDs, materialize repeated work, use the free **Preview** and **query cache**.
- Guardrail with **`maximum_bytes_billed`**. DuckDB has no billing; use `EXPLAIN` to keep the "estimate first" habit offline.

## Resources
- Query pricing: <https://cloud.google.com/bigquery/pricing>
- Estimate & control costs: <https://cloud.google.com/bigquery/docs/best-practices-costs>
- Performance best practices: <https://cloud.google.com/bigquery/docs/best-practices-performance-overview>
- `bq` command-line: <https://cloud.google.com/bigquery/docs/bq-command-line-tool>
- Prev: `405-bigquery-loading-partitioning-clustering.md` · Next: `407-bigquery-python-integration.md`
