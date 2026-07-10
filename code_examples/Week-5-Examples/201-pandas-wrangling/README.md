# Demo 201 — Pandas Wrangling

A guided tour of the core pandas operations from
[`notes/201-pandas-refresher.md`](../../notes/201-pandas-refresher.md), run
against a tiny sales dataset. Each step prints its result so you can watch the
DataFrame transform.

## What it shows

The script (`wrangle.py`) walks 10 numbered stages, each mapping to a section of
note 201:

1. **Load** — `read_csv` with `parse_dates`
2. **Inspect** — `shape`, `dtypes`, `info()`, `describe()`, `isna().sum()`
3. **Selection** — `[]` vs `.loc` vs `.iloc`
4. **Clean** — fill missing values (group-mean fill + a constant fill)
5. **Derive** — a `revenue` column and a conditional `size` flag (`np.where`)
6. **Filter** — boolean masks with `&`, and `.isin`
7. **Aggregate** — `groupby` + `agg` + `reset_index` + `sort_values`
8. **Merge** — join a region lookup table and compute % of target
9. **Concat** — stack two row subsets back together
10. **Export** — write the cleaned frame to Parquet and read it back

## Data

- `sales.csv` — 15 sales rows. **Deliberately contains two blank cells**
  (one `quantity`, one `unit_price`) so the missing-value handling in step 4 has
  something real to do.
- `regions.csv` — a small lookup table (manager + target per region) for the merge.

## Run

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python wrangle.py
```

## What to observe

- In **step 2**, `info()` shows `quantity`/`unit_price` with fewer non-null
  counts than the others — that's how you *spot* missing data before touching it.
  Also note `order_date` is a real `datetime64` (because of `parse_dates`), not text.
- In **step 4**, the missing counts drop to zero. The blank `unit_price` for the
  Gizmos order gets filled with the average Gizmos price, not a global average.
- In **step 7**, the group key (`category`) becomes a normal column after
  `reset_index()` — the shape you want before turning results into JSON (demo 203).
- In **step 8**, `Guido`'s region has no target row? It does — but watch how a
  `how="left"` merge would produce `NaN` if a region were missing from the lookup.
- **step 10** writes `sales_clean.parquet` next to the script; delete it any time.

## Follow-Along Build Walkthrough

### Intro — what we build and why

We are going to build `wrangle.py` from an empty file, live, one stage at a time.
The finished script takes a raw `sales.csv` (with a couple of deliberately blank
cells), cleans it, enriches it, summarizes it, joins it to a regions lookup, and
writes a tidy Parquet file — the exact shape of the "raw data in, clean answer
out" pipeline that shows up in almost every data job.

The audience already knows Python and SQL. That is our secret weapon: nearly
every pandas operation here has a SQL cousin, and we lean on that the whole way.
`groupby` is `GROUP BY`, boolean masks are `WHERE`, `merge` is `JOIN`. The goal
is not to teach new *concepts* — it is to build muscle memory for the pandas
*syntax* that expresses concepts they already own. We build it stage by stage and
run the script after each stage so associates literally watch the DataFrame
change.

By the end we will have reconstructed all 10 numbered stages and printed a
readable trace of the transformation from load to export.

### Step-by-step assembly

Build the file top-down. Start with the imports and a small helper, then add one
numbered stage at a time inside `main()`, re-running after each stage.

#### Stage 0 — scaffolding

```python
"""
201 - Pandas wrangling demo.
"""

from pathlib import Path
import pandas as pd
import numpy as np

HERE = Path(__file__).parent


def banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
```

`import pandas as pd` and `import numpy as np` are the two conventional aliases —
associates will see them everywhere, so type them by hand, not copy-paste.
`HERE = Path(__file__).parent` makes every file path relative to the script, so
the demo runs no matter what directory you launch it from. `banner()` is just a
print helper so each stage's output is visually separated in the terminal — it is
scaffolding, not pandas, but it makes the live demo readable.

#### Stage 1 — LOAD

```python
    banner("1. LOAD  (read_csv, parse dates)")
    sales = pd.read_csv(HERE / "sales.csv", parse_dates=["order_date"])
    print(sales.head())
```

`pd.read_csv` reads the file into a **DataFrame** — pandas' table type, the
in-memory equivalent of a SQL table. The one thing worth stopping on is
`parse_dates=["order_date"]`: without it, `order_date` would come in as plain
strings ("2026-01-05"), and you could not do date math on it. With it, pandas
converts that column to a real `datetime64` type at load time. `sales.head()`
prints the first five rows — the fastest way to confirm the file loaded the way
you expected. Point out that our `sales.csv` has 15 rows and two blank cells
(row `1004` has no `unit_price`, row `1008` has no `quantity`) — those blanks are
the whole reason later stages exist.

#### Stage 2 — INSPECT

```python
    banner("2. INSPECT  (shape / dtypes / info / describe)")
    print("shape:", sales.shape)
    print("\ndtypes:\n", sales.dtypes)
    print("\ninfo():")
    sales.info()
    print("\ndescribe():\n", sales.describe())

    banner("2b. MISSING VALUES  (isna().sum())")
    print(sales.isna().sum())
```

Before touching data, look at it. `sales.shape` returns a `(rows, columns)`
tuple — here `(15, 7)`. `sales.dtypes` shows the type pandas inferred per column;
this is where you confirm `order_date` really is `datetime64` and, importantly,
that `quantity` and `unit_price` came in as **floats, not ints** — because a
blank cell forces the whole column to float (pandas represents "missing" as the
float `NaN`). `sales.info()` prints non-null counts per column: `quantity` and
`unit_price` show 14 non-null out of 15 — that is how you *spot* the missing data.
`sales.describe()` gives summary statistics (count, mean, min, max, quartiles) for
the numeric columns. Finally, `sales.isna().sum()` is the direct answer to "how
many missing values per column": `isna()` returns a True/False frame, and summing
booleans counts the Trues — one for `quantity`, one for `unit_price`.

#### Stage 3 — SELECTION

```python
    banner("3. SELECTION  ([] vs .loc vs .iloc)")
    print("single column -> Series:\n", sales["customer"].head(3))
    print("\ntwo columns -> DataFrame:\n", sales[["customer", "region"]].head(3))
    print("\n.loc[0, 'customer']:", sales.loc[0, "customer"])
    print(".iloc[0, 1] (first row, 2nd col):", sales.iloc[0, 1])
```

This is the SELECT stage — how you pick columns and cells. Four things, and the
distinctions matter:

- `sales["customer"]` — one column name in brackets returns a **Series** (a
  single labeled column).
- `sales[["customer", "region"]]` — a *list* of names in brackets returns a
  **DataFrame** (a table). The doubled brackets trip everyone up; call it out.
- `sales.loc[0, "customer"]` — `.loc` selects by **label**: row label `0`,
  column named `"customer"`.
- `sales.iloc[0, 1]` — `.iloc` selects by **integer position**: row 0, column 1
  (the second column). Here the labels happen to equal positions, but stress that
  after filtering or sorting they diverge, and that is exactly when the
  label-vs-position distinction bites.

#### Stage 4 — CLEAN (handle missing values)

```python
    banner("4. CLEAN  (fill missing values)")
    sales["unit_price"] = sales["unit_price"].fillna(
        sales.groupby("category")["unit_price"].transform("mean")
    )
    sales["quantity"] = sales["quantity"].fillna(1).astype(int)
    print("missing after cleaning:\n", sales.isna().sum())
```

Now we fix the blanks we found in stage 2, and we choose the fill *strategy*
per column — that is the teaching point, not the syntax.

For `unit_price`, filling with a single global average would be crude. Instead we
fill each blank with the **average price of that row's own category**.
`sales.groupby("category")["unit_price"].transform("mean")` computes the mean
`unit_price` within each category and — crucially — `transform` returns a result
**aligned back to the original 15 rows** (unlike `agg`, which would collapse to
one row per category). `fillna(...)` then substitutes those category-means only
where the value was missing. So the blank Gizmos price gets the Gizmos average,
not a whole-table average.

For `quantity`, a missing order quantity most sensibly means 1, so we
`fillna(1)`. Then `.astype(int)` converts the column back to integer — remember
it was forced to float by the blank; now that there are no NaNs left, we can
restore the honest `int` type. The closing `isna().sum()` should now print all
zeros, proving the clean worked.

#### Stage 5 — DERIVE

```python
    banner("5. DERIVE  (revenue + a big/small flag)")
    sales["revenue"] = (sales["quantity"] * sales["unit_price"]).round(2)
    sales["size"] = np.where(sales["revenue"] >= 100, "big", "small")
    print(sales[["order_id", "quantity", "unit_price", "revenue", "size"]].head())
```

Add new columns computed from existing ones. `sales["quantity"] *
sales["unit_price"]` multiplies the two columns **element-wise** across all rows
at once — no loop. This is *vectorization*, and it is both faster and shorter than
iterating rows; make sure associates see that assigning to `sales["revenue"]`
creates the column in place. `.round(2)` tidies to cents.

`np.where(condition, a, b)` is a vectorized if/else: wherever `revenue >= 100` it
writes `"big"`, otherwise `"small"`. It is the pandas idiom for a
`CASE WHEN` — one expression, applied to the whole column.

#### Stage 6 — FILTER (boolean masks)

```python
    banner("6. FILTER  (boolean masks / .isin)")
    east_big = sales[(sales["region"] == "East") & (sales["revenue"] >= 100)]
    print("East orders with revenue >= 100:\n",
          east_big[["order_id", "customer", "revenue"]])
    print("\nWidgets or Gadgets only (isin):",
          len(sales[sales["category"].isin(["Widgets", "Gadgets"])]), "rows")
```

This is `WHERE`. `sales["region"] == "East"` produces a boolean Series (True/False
per row); indexing `sales[ mask ]` keeps only the True rows. Combining conditions
uses `&` (and) / `|` (or) — **not** Python's `and`/`or` — and each condition
**must be parenthesized** because `&` binds tighter than `==`. Forgetting the
parentheses is the single most common pandas filtering bug, so demo the error.
`.isin(["Widgets", "Gadgets"])` is the `IN (...)` operator: True where the value
is in the list. We wrap it in `len(...)` just to count matching rows.

#### Stage 7 — AGGREGATE (groupby + agg + sort)

```python
    banner("7. AGGREGATE  (groupby + agg, then sort)")
    by_category = (
        sales.groupby("category")
        .agg(orders=("order_id", "count"),
             total_revenue=("revenue", "sum"),
             avg_revenue=("revenue", "mean"))
        .round(2)
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    print(by_category)
```

Pure `GROUP BY`. `groupby("category")` buckets rows by category; `.agg(...)` then
computes one row per bucket. The `name=("column", "func")` syntax is *named
aggregation* — it maps directly to SQL: `orders=("order_id", "count")` is
`COUNT(order_id) AS orders`, and so on for `sum` and `mean`. `.round(2)` cleans
the numbers. `.reset_index()` is important: after `groupby`, `category` is the
DataFrame's *index*, not a column — `reset_index()` promotes it back to a normal
column, which is the shape you want for exporting or turning into JSON.
`.sort_values("total_revenue", ascending=False)` is `ORDER BY total_revenue DESC`.
The whole chain reads top-to-bottom as one pipeline thanks to the wrapping
parentheses.

#### Stage 8 — MERGE (join the lookup)

```python
    banner("8. MERGE  (join region lookup, compare to target)")
    regions = pd.read_csv(HERE / "regions.csv")
    by_region = (
        sales.groupby("region")["revenue"].sum()
        .reset_index()
        .rename(columns={"revenue": "actual"})
    )
    scorecard = by_region.merge(regions, on="region", how="left")
    scorecard["pct_of_target"] = (
        (scorecard["actual"] / scorecard["target"] * 100).round(1)
    )
    print(scorecard)
```

First we build actual revenue per region (`groupby("region")["revenue"].sum()`,
reset to a column, renamed `actual`). Then we load `regions.csv` — the lookup
table with a `manager` and `target` per region — and `merge` on the shared
`region` key. `merge` is a SQL `JOIN`; `how="left"` keeps every row from the left
frame (`by_region`) and pulls matching `manager`/`target` from the right. Because
all three regions (East, West, North) exist in the lookup, nothing goes missing
here — but stress that if a region were absent from `regions.csv`, a left join
would fill its `target` with `NaN` rather than drop the row. Finally we compute
`pct_of_target` as a vectorized column expression across the joined frame.

#### Stage 9 — CONCAT

```python
    banner("9. CONCAT  (stack two subsets back together)")
    east = sales[sales["region"] == "East"]
    west = sales[sales["region"] == "West"]
    stacked = pd.concat([east, west], ignore_index=True)
    print("East rows:", len(east), "+ West rows:", len(west),
          "-> concat:", len(stacked))
```

Where `merge` joins side-by-side (adds columns), `concat` stacks top-to-bottom
(adds rows) — it is `UNION ALL`. We slice out the East and West subsets, then
`pd.concat([east, west], ...)` glues them into one frame. `ignore_index=True`
rebuilds a clean 0..n index instead of preserving the original (now
gap-riddled) row labels. The print confirms the row counts add up.

#### Stage 10 — EXPORT

```python
    banner("10. EXPORT  (write the cleaned data to Parquet)")
    out = HERE / "sales_clean.parquet"
    sales.to_parquet(out, index=False)
    print(f"wrote {out.name} ({out.stat().st_size:,} bytes)")
    print("read back OK ->", pd.read_parquet(out).shape)
```

Persist the cleaned, enriched `sales` frame. `to_parquet` writes a columnar
binary file — smaller and faster than CSV, and it *preserves dtypes* (our
`datetime64` and `int` columns survive the round trip, which CSV cannot
guarantee). `index=False` drops the pandas row index from the file. We
immediately read it back and print its shape as a sanity check that the write
succeeded. Finish with the standard entry-point guard:

```python
if __name__ == "__main__":
    main()
```

### How it fits together

The stages form a single left-to-right data flow:

`sales.csv` (raw, with blanks)
→ **load** into a DataFrame (dates parsed)
→ **inspect** to find the blanks and confirm dtypes
→ **select** the columns/cells of interest
→ **clean** the blanks (category-mean price, quantity → 1)
→ **derive** `revenue` and `size` from the clean columns
→ **filter** to interesting subsets (East big orders, Widgets/Gadgets)
→ **aggregate** into a per-category summary and **sort** it
→ **merge** per-region totals with `regions.csv` to build a target scorecard
→ **concat** subsets back together to show row-stacking
→ **export** the final clean frame to `sales_clean.parquet`.

Each stage consumes the output of the ones before it: you cannot compute
`revenue` (stage 5) until the blanks are filled (stage 4), and you cannot build
the scorecard (stage 8) until `revenue` exists. That dependency chain is exactly
why we build and run the script in this order.

### Demo Notes (instructor)

**How to run it:** `pip install -r requirements.txt` then `python wrangle.py`.
Run it once *after each stage you add* so associates watch output grow. The
banners make each stage easy to find in the scrollback.

**What to point out live, with expected output per stage:**

- **Stage 1:** `head()` shows 5 rows; note row `1004`'s `unit_price` prints as
  `NaN` and `1008`'s `quantity` as `NaN`. The dates print as timestamps, not
  strings.
- **Stage 2:** `shape: (15, 7)`. In `info()`, call out `quantity` and
  `unit_price` at **14 non-null** while everything else is 15 — that is the
  missing data. Also note both are `float64`, not `int64` — a surprise if you
  expected quantities to be integers.
- **Stage 2b:** `isna().sum()` prints `1` for `quantity` and `1` for
  `unit_price`, `0` for everything else.
- **Stage 3:** one bracket → a Series (prints with a `Name:` footer); two
  brackets → a DataFrame (prints as a table). `.loc[0, 'customer']` → `Ada`;
  `.iloc[0, 1]` → the timestamp for `2026-01-05` (the second column is
  `order_date`, not `customer` — a good "position vs label" gotcha).
- **Stage 4:** `isna().sum()` now prints all zeros. Optionally print the filled
  Gizmos row to show it got `30.0` (the Gizmos mean), not the global mean.
- **Stage 5:** `revenue` and `size` appear; the first row (Ada, 4 × 12.50 = 50.0)
  is flagged `small`; a 10 × 12.50 = 125.0 row is `big`.
- **Stage 6:** the East / revenue≥100 subset is a short table; the
  Widgets-or-Gadgets count prints as a row count.
- **Stage 7:** three-row summary (one per category), sorted so the largest
  `total_revenue` is on top, with `orders`, `total_revenue`, `avg_revenue`
  columns and `category` back as a normal column.
- **Stage 8:** three-row scorecard with `region, actual, manager, target,
  pct_of_target`.
- **Stage 9:** prints something like `East rows: 8 + West rows: 5 -> concat: 13`.
- **Stage 10:** prints the byte size written and `read back OK -> (15, 9)`.

**Common pandas gotchas to demo deliberately:**

- **SettingWithCopyWarning:** if you filter first and then assign to the slice
  (e.g. `east = sales[...]; east["x"] = ...`), pandas warns because it does not
  know if `east` is a view or a copy. In this script we assign to columns of the
  full `sales` frame (`sales["revenue"] = ...`), which avoids it — point out
  *why* that pattern is safe.
- **NaN handling:** `NaN` is a float, so *any* column with a blank becomes float,
  and `NaN == NaN` is `False`. That is why we use `isna()` to detect it and
  `fillna()` to replace it, never `== NaN`.
- **dtype surprises:** the `quantity` blank silently turned an integer column into
  float; only after `fillna(1).astype(int)` is it an honest int again. Show
  `sales.dtypes` before and after stage 4.
- **`&` vs `and`:** show the `ValueError`/`TypeError` you get from
  `sales["a"] == 1 and sales["b"] == 2`, then fix it with `&` and parentheses.
- **`transform` vs `agg`:** `agg` collapses groups to one row each; `transform`
  keeps the original row count so the result can be assigned back — the reason
  stage 4's fill works.

### Discussion Topics

1. **Vectorization vs loops.** Stage 5 computes `revenue` for all rows in one
   expression. How would you do it with a Python `for` loop over rows, and why is
   the vectorized version both faster and clearer? When (if ever) is an explicit
   loop justified?
2. **When to use `.loc` vs `.iloc` vs `[]`.** After a filter or sort, row labels
   no longer match positions. Which selector do you reach for, and what breaks if
   you pick the wrong one?
3. **Missing-value strategy.** We filled `unit_price` with a category mean but
   `quantity` with the constant 1. What are the trade-offs of mean-fill,
   constant-fill, forward-fill, and simply dropping rows? When would dropping be
   the right call?
4. **Merge types.** We used `how="left"`. How would `inner`, `right`, and `outer`
   change the scorecard if a region were missing from `regions.csv` (or vice
   versa)? Which join do you want for a scorecard that must list every region?
5. **`groupby` result shape.** Why do we call `reset_index()` after the
   aggregation? What is the difference between having `category` as an index
   versus a column, and when does it matter downstream?
6. **CSV vs Parquet.** Stage 10 exports Parquet. What does Parquet preserve that
   CSV loses (think dtypes, the float/int/date issues we hit), and when would you
   still choose CSV?
