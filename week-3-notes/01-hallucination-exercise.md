# Catch the Hallucination Exercise

Each block below is an AI's response to a prompt, handed to you to review - exactly like deciding whether to accept an AI suggestion in a real codebase.

**Some of these are correct. Some are not.** For each one, without running the code decide: **approve as-is**, or **identify the issue and fix it.** Write down your decision and the **specific thing you checked** to be confident. "Approve" needs a reason behind it just as much as "reject" does.

---

## Exercise 1 — Python

**Prompt given to the AI:**
> Write a function that returns only the orders from the last 30 days.

**AI output:**
```python
from datetime import datetime, timedelta

def recent_orders(orders):
    cutoff = datetime.now() - timedelta(days=30)
    return [o for o in orders if o["order_date"] < cutoff]
```

*Decision + what you checked:*

---

## Exercise 2 — Python

**Prompt given to the AI:**
> Write a function to compute the average order value, returning 0 if there are no orders.

**AI output:**
```python
def average_order_value(orders):
    if not orders:
        return 0
    total = sum(o["amount"] for o in orders)
    return total / len(orders)
```

*Decision + what you checked:*

---

## Exercise 3 — PostgreSQL

**Prompt given to the AI:**
> Join orders to customers so each order row also shows the customer's name.

**AI output:**
```sql
SELECT o.order_id, o.amount, c.name
FROM orders o
JOIN customers c ON o.order_id = c.customer_id;
```

*Decision + what you checked:*

---

## Exercise 4 — Python

**Prompt given to the AI:**
> Write a function that splits a list of records into batches of size `n` for bulk loading.

**AI output:**
```python
def batch(records, n):
    batches = []
    for i in range(0, len(records) - n, n):
        batches.append(records[i:i + n])
    return batches
```

*Decision + what you checked:*

---

## Exercise 5 — PostgreSQL

**Prompt given to the AI:**
> For each customer, return their total number of orders, including customers who have placed no orders (a count of 0).

**AI output:**
```sql
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;
```

*Decision + what you checked:*

---

## Exercise 6 — PostgreSQL

**Prompt given to the AI:**
> Get the 3 most recent orders for each customer.

**AI output:**
```sql
SELECT customer_id, order_id, order_date
FROM orders
ORDER BY order_date DESC
LIMIT 3;
```

*Decision + what you checked:*

---

## Exercise 7 — Python

**Prompt given to the AI:**
> Write a function to fetch a single order by its id from Postgres using psycopg2.

**AI output:**
```python
def get_order_by_id(conn, order_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, customer_id, amount FROM orders WHERE id = %s",
            (order_id,),
        )
        return cur.fetchone()
```

*Decision + what you checked:*

---

## Exercise 8 — PostgreSQL

**Prompt given to the AI:**
> Compute each product's conversion rate as `purchases` divided by `views`, expressed as a percentage. `purchases` and `views` are integer columns.

**AI output:**
```sql
SELECT product_id,
       (purchases / views) * 100 AS conversion_rate_pct
FROM product_stats;
```

*Decision + what you checked:*

---

## Exercise 9 — Python

**Prompt given to the AI:**
> I need to load a pandas DataFrame into Postgres efficiently. Give me the install command and the code.

**AI output:**
```bash
pip install pandas sqlalchemy psycopg2-binary pandas-postgres-bulk
```
```python
from pandas_postgres_bulk import bulk_load

bulk_load(
    df,
    table="orders",
    conn_string="postgresql://user:pass@host:5432/analytics",
)
```

*Decision + what you checked:*
