# Pandas Refresher

## Learning Objectives

- Explain what a `Series` and a `DataFrame` are and how they relate
- Load data with `read_csv` / `read_json` and inspect it with `head`, `info`, `describe`, `dtypes`
- Select and filter data three ways: `[]`, `.loc`, `.iloc`, and boolean masks
- Add derived columns and clean up missing values
- Aggregate with `groupby` + agg, sort results, and combine tables with `merge` / `concat`
- Read pandas code without guessing what each line does

## Why This Matters

Pandas is the workhorse you will lean on for the **rest of this week** and most of your career as a data engineer:

- **Day 4** — you pull query results out of BigQuery straight into a `DataFrame`.
- **Day 5** — the whole ETL/ELT capstone transforms data with pandas before loading it.
- **Today** — you serve pandas results out of a FastAPI endpoint (note 204).

You already know Python and SQL. Good news: pandas is basically **SQL-for-Python-objects plus spreadsheet ergonomics**. Almost every SQL idea you know (`SELECT`, `WHERE`, `GROUP BY`, `JOIN`, `ORDER BY`) has a direct pandas equivalent. This note maps them so you can lean on what you already know.

> **Mental model:** a `DataFrame` is a table. A `Series` is one column of that table (plus an index). That is 90% of the intuition you need.

## Concept Explanation

### Setup

```python
import pandas as pd   # the universal convention — always `pd`
import numpy as np    # pandas is built on numpy; you'll see np.nan for "missing"
```

Everything below assumes `import pandas as pd`.

### Series vs DataFrame

A **Series** is a 1-D labeled array — one column with an index.

```python
s = pd.Series([10, 20, 30], index=["a", "b", "c"])
print(s)
# a    10
# b    20
# c    30
# dtype: int64

print(s["b"])   # 20   -> label-based lookup
print(s.mean()) # 20.0 -> vectorized math, no loop needed
```

A **DataFrame** is a 2-D table — a dict of Series that share one index (the row labels).

```python
df = pd.DataFrame({
    "name": ["Ada", "Linus", "Grace"],
    "lang": ["Python", "C", "COBOL"],
    "age":  [36, 54, 41],
})
print(df)
#     name    lang  age
# 0    Ada  Python   36
# 1  Linus       C   54
# 2  Grace   COBOL   41
```

```
DataFrame  = table
  │
  ├── df["age"]      -> a Series (one column)
  ├── df.index       -> row labels (0,1,2 by default)
  └── df.columns     -> column labels (name, lang, age)
```

Selecting **one** column gives a Series; selecting a **list** of columns gives a DataFrame:

```python
df["age"]            # Series
df[["name", "age"]]  # DataFrame (note the double brackets)
```

### Loading data: `read_csv` / `read_json`

```python
df = pd.read_csv("employees.csv")           # the one you'll use 90% of the time

# Common, useful arguments:
pd.read_csv("data.csv",
            usecols=["id", "salary"],        # read only these columns
            dtype={"id": "int64"},           # force a column's type
            parse_dates=["hire_date"],       # parse text -> real datetimes
            nrows=1000)                       # peek at just the first 1000 rows

# JSON (an array of objects) and JSON Lines (one object per line):
pd.read_json("data.json")                    # [{...}, {...}]
pd.read_json("data.jsonl", lines=True)       # {...}\n{...}\n  (see note 203)
```

### Inspecting a DataFrame (do this FIRST, every time)

Before you transform anything, look at what you loaded.

| Call | What it tells you |
|------|-------------------|
| `df.head(5)` | first 5 rows — sanity-check the shape and values |
| `df.tail(5)` | last 5 rows |
| `df.shape` | `(rows, columns)` tuple |
| `df.info()` | column names, non-null counts, and dtypes — **spot missing data here** |
| `df.describe()` | count/mean/std/min/quartiles/max for numeric columns |
| `df.dtypes` | the type of each column |
| `df.columns` | the column labels |
| `df["dept"].value_counts()` | frequency count of each value (like `GROUP BY … COUNT(*)`) |

```python
df.info()
# <class 'pandas.core.frame.DataFrame'>
# RangeIndex: 3 entries, 0 to 2
# Data columns (total 3 columns):
#  #   Column  Non-Null Count  Dtype
# ---  ------  --------------  -----
#  0   name    3 non-null      object    <- "object" usually means text/string
#  1   lang    3 non-null      object
#  2   age     3 non-null      int64
```

> **Watch dtypes.** `object` = Python objects (usually strings). If a numeric column shows up as `object`, something dirty is in it (a stray `"N/A"`, a `$`, a comma) and math will fail. `info()` is where you catch that.

### Selection: `[]` vs `.loc` vs `.iloc`

This trips up newcomers, so here is the rule:

| You want… | Use | Example |
|-----------|-----|---------|
| A column (or columns) | `df[...]` | `df["age"]`, `df[["name","age"]]` |
| Rows/cols by **label** | `df.loc[...]` | `df.loc[0, "age"]`, `df.loc[df.age > 40, "name"]` |
| Rows/cols by **position** | `df.iloc[...]` | `df.iloc[0, 2]`, `df.iloc[0:2, :]` |

```python
df.loc[1]                    # the row with index label 1 (a Series)
df.loc[1, "name"]            # "Linus"
df.loc[:, ["name", "age"]]   # all rows, two columns
df.loc[0:1]                  # label slice is INCLUSIVE -> rows 0 and 1

df.iloc[0]                   # first row by position
df.iloc[0, 2]                # first row, third column -> 36
df.iloc[0:2]                 # position slice is EXCLUSIVE -> rows 0 and 1
```

> **`.loc` is label-based and inclusive; `.iloc` is position-based and exclusive** (like normal Python slicing). When in doubt, prefer `.loc` — it's what you'll read most in real code.

### Filtering with boolean masks (this is your `WHERE`)

A comparison on a Series produces a Series of `True`/`False`. Passing that back into `df[...]` keeps only the `True` rows.

```python
mask = df["age"] > 40        # Series of booleans
df[mask]                     # rows where age > 40

# usually written inline:
df[df["age"] > 40]

# combine conditions with & (and), | (or), ~ (not)
# -> each condition MUST be wrapped in parentheses
df[(df["age"] > 40) & (df["lang"] == "C")]

# membership (like SQL IN):
df[df["lang"].isin(["Python", "COBOL"])]

# text matching:
df[df["name"].str.startswith("A")]
```

| SQL | pandas |
|-----|--------|
| `WHERE age > 40` | `df[df["age"] > 40]` |
| `WHERE a AND b` | `df[(a) & (b)]` |
| `WHERE lang IN (...)` | `df[df["lang"].isin([...])]` |

### Adding / deriving columns

Assigning to a column that doesn't exist creates it. Operations are **vectorized** — they apply to the whole column at once, no loop.

```python
df["age_in_10"] = df["age"] + 10             # arithmetic on a whole column
df["senior"]    = df["age"] > 50             # boolean column
df["initial"]   = df["name"].str[0]          # string ops via .str

# conditional column (like CASE WHEN):
df["band"] = np.where(df["age"] >= 50, "senior", "junior")

# a reusable derived column with .assign (returns a NEW df; chainable):
df2 = df.assign(decade=(df["age"] // 10) * 10)
```

### Handling missing values

Missing values show up as `NaN` (numbers) or `None`/`NaT`. `info()` and `isna()` reveal them.

```python
df.isna().sum()              # count of missing per column  <- run this often

df.dropna()                  # drop any row with a missing value
df.dropna(subset=["email"])  # drop rows missing THIS column only

df["age"].fillna(0)                        # fill with a constant
df["age"].fillna(df["age"].mean())         # fill with the column mean
df["dept"] = df["dept"].fillna("Unknown")  # assign back to keep the change
```

> **`fillna`/`dropna` return a NEW DataFrame** — they don't change `df` in place unless you assign the result back. This is the #1 "why didn't my change stick?" gotcha.

### Aggregation: `groupby` + agg (this is your `GROUP BY`)

```python
# average age per language  (SELECT lang, AVG(age) ... GROUP BY lang)
df.groupby("lang")["age"].mean()

# count rows per group
df.groupby("lang").size()

# multiple aggregations at once, with clean output names:
df.groupby("lang").agg(
    avg_age=("age", "mean"),
    max_age=("age", "max"),
    people=("name", "count"),
)
#         avg_age  max_age  people
# lang
# C          54.0       54       1
# COBOL      41.0       41       1
# Python     36.0       36       1
```

The result is indexed by the group key. Add `.reset_index()` to turn that key back into a normal column (handy before serving as JSON — see note 204):

```python
summary = df.groupby("lang")["age"].mean().reset_index()
```

### Sorting: your `ORDER BY`

```python
df.sort_values("age")                       # ascending
df.sort_values("age", ascending=False)      # descending
df.sort_values(["lang", "age"])             # multi-key
df.nlargest(3, "age")                       # top 3 by age (fast + readable)
```

### Combining tables: `merge` and `concat`

**`merge`** joins two DataFrames on key column(s) — this is your SQL `JOIN`.

```python
depts = pd.DataFrame({"lang": ["Python", "C"], "team": ["Web", "Kernel"]})

df.merge(depts, on="lang", how="left")
#     name    lang  age    team
# 0    Ada  Python   36     Web
# 1  Linus       C   54  Kernel
# 2  Grace   COBOL   41     NaN   <- no match -> NaN with a left join
```

`how` mirrors SQL: `"inner"` (default), `"left"`, `"right"`, `"outer"`.

**`concat`** stacks DataFrames — rows on top of each other (like `UNION ALL`) or columns side by side.

```python
pd.concat([df_jan, df_feb], ignore_index=True)   # stack rows, renumber index
pd.concat([df_left, df_right], axis=1)            # glue columns side by side
```

| SQL | pandas |
|-----|--------|
| `JOIN ... ON` | `a.merge(b, on=..., how=...)` |
| `UNION ALL` | `pd.concat([a, b])` |

### Method chaining (how real pandas reads)

Because most methods return a new DataFrame, you can chain them into one readable pipeline:

```python
result = (
    df[df["age"] > 30]                       # filter
      .assign(decade=(df["age"] // 10) * 10) # derive
      .groupby("decade")["name"]             # group
      .count()                               # aggregate
      .reset_index(name="headcount")         # tidy up
      .sort_values("headcount", ascending=False)
)
```

Wrapping the chain in `(...)` lets you put each step on its own line. Read it top to bottom like a SQL query.

## Code Example

A complete, runnable end-to-end wrangle. Paste it into a file and run it — no external data file needed.

```python
import pandas as pd
import numpy as np

# 1. Build a small dataset (normally you'd read_csv here)
df = pd.DataFrame({
    "employee": ["Ada", "Linus", "Grace", "Guido", "Bjarne", "Margaret"],
    "dept":     ["Web", "Kernel", "Web", "Web", "Kernel", "Web"],
    "salary":   [120000, 150000, np.nan, 135000, 145000, 110000],
    "years":    [4, 12, 8, 10, 15, 20],
})

# 2. INSPECT — always look before you leap
print(df.info())
print(df.describe())
print("missing per column:\n", df.isna().sum())

# 3. CLEAN — fill the missing salary with the department average
df["salary"] = df["salary"].fillna(df.groupby("dept")["salary"].transform("mean"))

# 4. DERIVE — a tenure band and salary-per-year
df["band"] = np.where(df["years"] >= 10, "senior", "junior")
df["salary_per_year"] = (df["salary"] / df["years"]).round(0)

# 5. FILTER — seniors only
seniors = df[df["band"] == "senior"]

# 6. AGGREGATE — per-department summary
summary = (
    df.groupby("dept")
      .agg(headcount=("employee", "count"),
           avg_salary=("salary", "mean"),
           max_years=("years", "max"))
      .reset_index()
      .sort_values("avg_salary", ascending=False)
)
print(summary)

# 7. MERGE — attach a lookup table
locations = pd.DataFrame({"dept": ["Web", "Kernel"], "office": ["NYC", "Austin"]})
enriched = df.merge(locations, on="dept", how="left")

# 8. EXPORT — pandas writes many formats (see note 203)
enriched.to_parquet("employees.parquet", index=False)
print("wrote employees.parquet")
```

Run it (`demos/201-pandas-wrangling/` builds on exactly this):

```bash
pip install pandas pyarrow
python wrangle.py
```

## Key Takeaways

- A **DataFrame is a table**; a **Series is one column**. Selecting one column returns a Series.
- **Always inspect first**: `head()`, `info()`, `describe()`, `isna().sum()`. Watch for `object` dtype on numeric columns.
- **`[]`** = columns, **`.loc`** = labels (inclusive), **`.iloc`** = positions (exclusive).
- **Boolean masks are your `WHERE`**; combine with `&` `|` `~` and wrap each condition in parentheses.
- **`groupby` + `agg`** is `GROUP BY`; **`merge`** is `JOIN`; **`concat`** is `UNION`; **`sort_values`** is `ORDER BY`.
- Most methods return a **new** DataFrame — **assign the result back** or your change is lost.
- Operations are **vectorized** — act on whole columns; you almost never need a Python `for` loop.

## Resources

- 10 Minutes to pandas: <https://pandas.pydata.org/docs/user_guide/10min.html>
- Comparison with SQL: <https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_sql.html>
- Indexing and selecting data (`loc`/`iloc`): <https://pandas.pydata.org/docs/user_guide/indexing.html>
- Group by: split-apply-combine: <https://pandas.pydata.org/docs/user_guide/groupby.html>
- Merge, join, concatenate: <https://pandas.pydata.org/docs/user_guide/merging.html>
