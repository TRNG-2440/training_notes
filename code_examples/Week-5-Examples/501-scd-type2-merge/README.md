# Demo 501 — SCD Type 2 update (DuckDB)

> Day 5 · pairs with `notes/504-slowly-changing-dimensions.md`

## What this shows

A runnable, offline demonstration of a **Slowly Changing Dimension Type 2** update:

1. Build a `dim_customer` dimension with SCD-2 audit columns (`effective_date`, `end_date`, `is_current`) and seed 3 customers.
2. Land a batch of source changes in a staging table:
   - `C001` moved region **East → West** (attribute changed)
   - `C002` unchanged (should be a no-op)
   - `C003` renamed **Sam → Samuel** (attribute changed)
   - `C004` brand-new customer
3. Apply the SCD Type 2 operation — **expire** the outgoing current rows and **insert** new versioned rows (plus insert the new customer).
4. Print the dimension **before and after**, then run **point-in-time queries** to prove history is preserved.

The key lesson: old rows are **closed out, not overwritten**, so a fact that referenced the old surrogate key still rolls up to the historically-correct attributes.

## Why DuckDB (and where BigQuery differs)

Everything runs in an **in-memory DuckDB** database, so it works offline with no cloud account — the pattern Day 4 established.

DuckDB has no multi-branch `MERGE`, so the demo uses the portable **two-statement transaction** pattern (UPDATE to expire, INSERT to add new versions). BigQuery *does* support `MERGE`; the idiomatic single-pass equivalent is in **`scd_type2_bigquery.sql`** for reference.

## Run it

```bash
cd 2440-W5/demos/501-scd-type2-merge

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scd_type2_demo.py
```

## Expected output (abridged)

```
=== BEFORE — initial dimension (3 current rows) ===
 customer_key customer_id       name region ... is_current
            1        C001 John Smith   East ...       True
            2        C002   Jane Doe   West ...       True
            3        C003 Sam Rivera  North ...       True

=== AFTER — SCD Type 2 applied ===
            1        C001    John Smith   East  ...  False   <- expired
            4        C001    John Smith   West  ...   True   <- new version
            2        C002      Jane Doe   West  ...   True   <- untouched
            3        C003    Sam Rivera  North  ...  False   <- expired
            5        C003 Samuel Rivera  North  ...   True   <- new version
            6        C004   Priya Patel  South  ...   True   <- new customer

=== Point-in-time queries ===
C001 region as of 2024-06-01 : East   (historically accurate)
C001 region right now        : West
Current customers: 4   |   Total versioned rows: 6
```

## Files

| File | Purpose |
|------|---------|
| `scd_type2_demo.py` | The runnable DuckDB demo (build → change → SCD2 → verify) |
| `scd_type2_bigquery.sql` | Equivalent BigQuery `MERGE` for reference |
| `requirements.txt` | `duckdb`, `pandas` |

## Try next

- Change a customer's `name` back to a prior value — a *new* version is still created (Type 2 does not deduplicate historical states).
- Add an `is_current = TRUE` unique-per-natural-key check as a data-quality gate (Note 506).
- Re-run `apply_scd_type2` twice on the same batch — the change-detection predicate makes the second run a no-op (idempotency, Note 506).

## Follow-Along Build Walkthrough

A "build it live with me" guide for teaching this demo. The goal is not to memorize syntax but to *watch* an SCD Type 2 update preserve history instead of overwriting it. Type the file up in front of the room, run it after each major step, and let the before/after output do the teaching.

### 1. Intro — what we build and why

We build a small **customer dimension table** (`dim_customer`) in an in-memory DuckDB database, seed it with three customers, then simulate a nightly source load where some attributes have changed. We apply the **SCD Type 2** rule: instead of updating a customer's row in place, we *close out* (expire) the old row and *insert a brand-new versioned row* for the changed customer. Nothing is ever overwritten or deleted.

The payoff is a **point-in-time query**: after the update we ask "what region was customer C001 in on 2024-06-01?" and still get the historically correct answer, even though C001's *current* region is now different. That is the whole reason Type 2 exists — a fact row that referenced last year's version of the customer still rolls up to last year's attributes.

Contrast this with SCD Type 1, which would simply `UPDATE dim_customer SET region = 'West'` and destroy the old value forever. By the end of the walkthrough associates should be able to explain, out loud, why the row count grew and why that is a feature, not a bug.

We also keep a reference **BigQuery `MERGE`** in `scd_type2_bigquery.sql`. DuckDB has no multi-branch `MERGE`, so the Python demo uses a portable two-statement pattern; the BigQuery file shows the idiomatic single-statement equivalent. We contrast the two at the end.

### 2. Step-by-step assembly

Build `scd_type2_demo.py` in the order below. Each function is small and self-contained; run `main()` (or a partial `main()`) after each milestone so the class sees state change on screen.

#### Step 0 — imports and stable constants

```python
from __future__ import annotations
import duckdb

# A fixed "load date" so demo output is stable/reproducible.
LOAD_DATE = "2025-06-15"
END_OF_TIME = "9999-12-31"
```

We hard-code `LOAD_DATE` instead of using "today" so the printed output is identical every time you run the demo — nobody wants the numbers shifting between rehearsal and class. `END_OF_TIME` is the sentinel `9999-12-31` that marks a row as "open" (still in effect). Using a far-future date instead of `NULL` for `end_date` keeps the point-in-time `BETWEEN`-style range check simple: every row always has a real, comparable end boundary.

#### Step 1 — create the dimension table and seed it

```python
def build_initial_dimension(con: duckdb.DuckDBPyConnection) -> None:
    """Create dim_customer with SCD-2 audit columns and seed 3 customers."""
    con.execute("CREATE SEQUENCE customer_key_seq START 1;")
    con.execute("""
        CREATE TABLE dim_customer (
            customer_key   BIGINT PRIMARY KEY,   -- surrogate key (per VERSION)
            customer_id    VARCHAR,              -- natural key (per CUSTOMER)
            name           VARCHAR,
            region         VARCHAR,
            effective_date DATE,
            end_date       DATE,
            is_current     BOOLEAN
        );
    """)
    # Seed rows: three customers, all current, effective from 2020.
    con.execute("""
        INSERT INTO dim_customer VALUES
            (nextval('customer_key_seq'), 'C001', 'John Smith',  'East',  DATE '2020-01-01', DATE '9999-12-31', TRUE),
            (nextval('customer_key_seq'), 'C002', 'Jane Doe',    'West',  DATE '2020-01-01', DATE '9999-12-31', TRUE),
            (nextval('customer_key_seq'), 'C003', 'Sam Rivera',  'North', DATE '2020-01-01', DATE '9999-12-31', TRUE);
    """)
```

- `CREATE SEQUENCE customer_key_seq START 1` gives us an auto-incrementing generator for surrogate keys. Each call to `nextval('customer_key_seq')` returns the next integer. We need this because **every version of a customer gets its own surrogate key**, not just every customer.
- The `CREATE TABLE` defines the two families of columns worth naming explicitly to the class:
  - `customer_key` — the **surrogate key**, unique *per version*. This is the primary key. Fact tables join to this.
  - `customer_id` — the **natural key** (the business identifier, e.g. `C001`), which stays the same across all versions of one customer.
  - The three **SCD-2 audit columns**: `effective_date` (when this version became true), `end_date` (when it stopped being true, or `9999-12-31` if still true), and `is_current` (a convenience boolean flag so "the row that is true right now" is a cheap lookup rather than a date comparison).
- The seed `INSERT` loads three customers. All start with `effective_date = 2020-01-01`, `end_date = 9999-12-31`, and `is_current = TRUE` — three open, current rows. Point out that `is_current` and `end_date = 9999-12-31` are *redundant on purpose*: the flag is a fast filter, the dates are the source of truth.

Run this plus `show(...)` (Step 4) now and you have the BEFORE picture.

#### Step 2 — introduce source changes in a staging table

```python
def load_source_batch(con: duckdb.DuckDBPyConnection) -> None:
    """Today's incoming source snapshot lands in a staging table."""
    con.execute("""
        CREATE TABLE stg_customer (customer_id VARCHAR, name VARCHAR, region VARCHAR);
        INSERT INTO stg_customer VALUES
            ('C001', 'John Smith',    'West'),
            ('C002', 'Jane Doe',      'West'),
            ('C003', 'Samuel Rivera', 'North'),
            ('C004', 'Priya Patel',   'South');
    """)
```

`stg_customer` is the **staging table** — the raw snapshot of "how customers look today" delivered by the upstream extract/load step. It has *no* audit columns; it is just the natural key and the tracked attributes. The four rows deliberately cover every case the SCD2 logic must handle:

- `C001` — region changed **East → West** → needs a new version.
- `C002` — identical to what we already have → must be a **no-op** (no new row).
- `C003` — name changed **Sam → Samuel** → needs a new version.
- `C004` — not in the dimension at all → **brand-new customer**, insert as current.

Emphasize that the staging table is a *full snapshot*, not a change feed. We do not get told what changed; we have to *detect* it by comparing staging to the current dimension rows. That detection is the heart of the next step.

#### Step 3 — apply the SCD Type 2 logic (expire, then insert)

```python
def apply_scd_type2(con: duckdb.DuckDBPyConnection) -> None:
    """The core SCD Type 2 operation: expire-then-insert, in one transaction."""
    con.execute("BEGIN")

    # STEP 1 — expire current rows whose tracked attributes changed.
    con.execute(f"""
        UPDATE dim_customer AS d
        SET end_date   = DATE '{LOAD_DATE}',
            is_current = FALSE
        FROM stg_customer AS s
        WHERE d.customer_id = s.customer_id
          AND d.is_current  = TRUE
          AND (d.name <> s.name OR d.region <> s.region);   -- change detection
    """)

    # STEP 2 — insert new current version for changed keys AND brand-new keys.
    con.execute(f"""
        INSERT INTO dim_customer
            (customer_key, customer_id, name, region, effective_date, end_date, is_current)
        SELECT
            nextval('customer_key_seq'),
            s.customer_id, s.name, s.region,
            DATE '{LOAD_DATE}', DATE '{END_OF_TIME}', TRUE
        FROM stg_customer s
        LEFT JOIN dim_customer d
               ON d.customer_id = s.customer_id AND d.is_current = TRUE
        WHERE d.customer_id IS NULL                          -- brand-new customer
           OR d.name <> s.name OR d.region <> s.region;      -- changed customer
    """)

    con.execute("COMMIT")
```

This is the demo's centerpiece. Two statements, wrapped in one transaction so the dimension is never seen half-updated.

**`BEGIN` / `COMMIT`** — the expire and the insert must both land or neither. If the UPDATE expired a row and then the INSERT failed, a customer would have *zero* current rows. The transaction makes the pair atomic.

**Statement 1 — the UPDATE (expire).** For every customer whose staging attributes differ from their *current* dimension row, we close out that row:
  - `SET end_date = LOAD_DATE` — the old version stopped being true today.
  - `SET is_current = FALSE` — it is no longer the live row.
  - The `WHERE` is the important part. `d.customer_id = s.customer_id` matches on the **natural key**. `d.is_current = TRUE` restricts us to the one live version (never touch already-expired history). `(d.name <> s.name OR d.region <> s.region)` is the **change-detection predicate**: only expire rows that *actually* changed. This is why `C002` (identical) is skipped and why re-running the load is idempotent.

**Statement 2 — the INSERT (new versions + new customers).** We `LEFT JOIN` staging to the *current* dimension rows and insert a fresh row when:
  - `d.customer_id IS NULL` — no current match, so this is a **brand-new customer** (`C004`), or
  - `d.name <> s.name OR d.region <> s.region` — a match exists but attributes changed, so this is a **new version** of an existing customer (`C001`, `C003`).
  - Each inserted row gets a **new surrogate key** from `nextval(...)`, `effective_date = LOAD_DATE`, `end_date = 9999-12-31`, and `is_current = TRUE` — a fresh open version.
  - Note the join is against `d.is_current = TRUE` on purpose: we compare staging to the *live* version, not to expired history. `C002` matches a current row with identical attributes, so both predicates are false and no row is inserted.

The mental model to say out loud: **"a changed customer expires one row and gains one row; a new customer just gains one row; an unchanged customer does nothing."**

#### Step 4 — show the dimension

```python
def show(con: duckdb.DuckDBPyConnection, title: str) -> None:
    print(f"\n=== {title} ===")
    df = con.execute("""
        SELECT customer_key, customer_id, name, region,
               effective_date, end_date, is_current
        FROM dim_customer
        ORDER BY customer_id, effective_date
    """).fetchdf()
    print(df.to_string(index=False))
```

A plain reporting helper. Ordering by `customer_id, effective_date` groups each customer's versions together in chronological order, so an expired row sits directly above its replacement — exactly what you want the class to see side by side.

#### Step 5 — the point-in-time query (the payoff)

```python
def point_in_time_examples(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Point-in-time queries (the payoff of Type 2) ===")

    region_2024 = con.execute("""
        SELECT region FROM dim_customer
        WHERE customer_id = 'C001'
          AND DATE '2024-06-01' >= effective_date
          AND DATE '2024-06-01' <  end_date
    """).fetchone()[0]
    print(f"C001 region as of 2024-06-01 : {region_2024}   (historically accurate)")

    region_now = con.execute("""
        SELECT region FROM dim_customer WHERE customer_id = 'C001' AND is_current
    """).fetchone()[0]
    print(f"C001 region right now        : {region_now}")

    n_current = con.execute(
        "SELECT COUNT(*) FROM dim_customer WHERE is_current").fetchone()[0]
    n_rows = con.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0]
    print(f"Current customers: {n_current}   |   Total versioned rows: {n_rows}")
```

- The **as-of query** finds the version that was in effect on a given date: `date >= effective_date AND date < end_date`. Because 2024-06-01 falls inside the *original* C001 row's window (2020-01-01 → 2025-06-15), it returns `East` — the historically correct answer. Note the boundary convention: `>=` on the start, `<` on the end, so windows are half-open and never overlap.
- The **current query** just filters `is_current` and returns `West` — the live value.
- The **counts** make the storage story concrete: 4 current customers, but 6 total rows. Two extra rows are the preserved history.

#### Step 6 — wire it together

```python
def main() -> None:
    con = duckdb.connect()  # in-memory
    build_initial_dimension(con)
    show(con, "BEFORE — initial dimension (3 current rows)")

    load_source_batch(con)
    apply_scd_type2(con)
    show(con, "AFTER — SCD Type 2 applied "
              "(C001 & C003 versioned, C004 added, C002 untouched)")

    point_in_time_examples(con)
    print("\nDone. Notice: no history was overwritten — old rows were closed out, "
          "not deleted.")
```

`duckdb.connect()` with no path is an **in-memory** database — nothing to install or clean up. The rest is the narrative arc: build → show BEFORE → land changes → apply SCD2 → show AFTER → prove history.

#### The BigQuery MERGE equivalent

BigQuery *does* have a multi-branch `MERGE`, so `scd_type2_bigquery.sql` collapses our two statements into one. The clever bit is the `USING` subquery, which **UNIONs the source to itself**:

```sql
MERGE mydataset.dim_customer AS d
USING (
    -- (A) rows that will MATCH the current version -> candidate to EXPIRE
    SELECT s.customer_id AS join_key, s.customer_id, s.name, s.region
    FROM mydataset.stg_customer s

    UNION ALL

    -- (B) rows that will NOT match (NULL join_key) -> INSERT new version
    SELECT CAST(NULL AS STRING) AS join_key, s.customer_id, s.name, s.region
    FROM mydataset.stg_customer s
    LEFT JOIN mydataset.dim_customer d
           ON d.customer_id = s.customer_id AND d.is_current
    WHERE d.customer_id IS NULL
       OR d.name <> s.name
       OR d.region <> s.region
) AS src
ON  d.customer_id = src.join_key
AND d.is_current
AND (d.name <> src.name OR d.region <> src.region)   -- only match when changed

WHEN MATCHED THEN
    UPDATE SET end_date = CURRENT_DATE(), is_current = FALSE

WHEN NOT MATCHED AND src.join_key IS NULL THEN
    INSERT (customer_key, customer_id, name, region,
            effective_date, end_date, is_current)
    VALUES (
        (SELECT COALESCE(MAX(customer_key), 0) + 1 FROM mydataset.dim_customer),
        src.customer_id, src.name, src.region,
        CURRENT_DATE(), DATE '9999-12-31', TRUE
    );
```

A single `MERGE` can only touch each target row once, so a *changed* customer needs to appear in the source **twice**: branch (A) carries a real `join_key` and matches the current row so `WHEN MATCHED` expires it; branch (B) carries a `NULL` `join_key` so it can never match, falling to `WHEN NOT MATCHED AND src.join_key IS NULL`, which inserts the new version. A brand-new customer appears only in branch (B).

**Contrast for the class:**

| | DuckDB (two statements) | BigQuery (`MERGE`) |
|---|---|---|
| Statements | UPDATE, then INSERT, in one `BEGIN`/`COMMIT` | One `MERGE` |
| Atomicity | You wrap it in a transaction yourself | The single statement is atomic by definition |
| Source shape | Staging table used directly by each statement | Staging **UNIONed to itself** so changed rows appear twice |
| Portability | Works on almost any SQL engine | Needs an engine with multi-branch `MERGE` |
| Readability | Two simple statements, easy to reason about | One dense statement; the self-UNION trick is non-obvious |

Neither is "better" — the two-statement pattern is more portable and easier to teach; the `MERGE` is more compact and atomic without ceremony. Same result, different tools.

### 3. How it fits together

The SCD Type 2 update is fundamentally an **expire-then-insert** sequence keyed on the natural key:

1. **Detect** which incoming rows differ from the current dimension version (compare staging to `is_current = TRUE` rows on the natural key).
2. **Expire** each changed customer's current row: stamp `end_date = load date` and flip `is_current = FALSE`. The row is not deleted — it becomes a closed historical version.
3. **Insert** a fresh current row for every changed customer *and* every brand-new customer: new surrogate key, `effective_date = load date`, `end_date = 9999-12-31`, `is_current = TRUE`.
4. Wrap steps 2–3 in one transaction so every natural key always has exactly one current row.

History is preserved because the old attribute values live on in the expired row, addressable by both the `is_current = FALSE` flag and the closed `[effective_date, end_date)` window. Any fact that pointed at the old surrogate key still resolves to the old attributes — that is the guarantee Type 2 buys you.

### 4. Demo Notes (instructor)

**What to run:** `python scd_type2_demo.py` (after `pip install -r requirements.txt`). It prints BEFORE, AFTER, and the point-in-time results in one shot. For a slower build, comment out `load_source_batch`/`apply_scd_type2`/`point_in_time_examples` in `main()` and reveal them one at a time.

**Expected BEFORE — three current rows:**

```
=== BEFORE — initial dimension (3 current rows) ===
 customer_key customer_id       name region ... is_current
            1        C001 John Smith   East ...       True
            2        C002   Jane Doe   West ...       True
            3        C003 Sam Rivera  North ...       True
```

**Expected AFTER — old rows expired (not overwritten), new current rows added:**

```
=== AFTER — SCD Type 2 applied ===
            1        C001    John Smith   East  ...  False   <- expired
            4        C001    John Smith   West  ...   True   <- new version
            2        C002      Jane Doe   West  ...   True   <- untouched
            3        C003    Sam Rivera  North  ...  False   <- expired
            5        C003 Samuel Rivera  North  ...   True   <- new version
            6        C004   Priya Patel  South  ...   True   <- new customer
```

Call out the four cases explicitly: C001 and C003 each show an expired row (`is_current = False`, `end_date = 2025-06-15`) *directly above* a brand-new current row with a fresh `customer_key`; C002 has exactly one unchanged row; C004 is a single new current row.

**Expected point-in-time result:**

```
=== Point-in-time queries ===
C001 region as of 2024-06-01 : East   (historically accurate)
C001 region right now        : West
Current customers: 4   |   Total versioned rows: 6
```

The `East` answer for 2024 despite the current region being `West` is the "aha" moment — pause there.

**Gotchas to flag:**

- **Match on natural key + current flag, not surrogate key.** The UPDATE and the INSERT's join both key on `customer_id` *and* `is_current = TRUE`. Forget `is_current` and you would re-expire (or compare against) already-closed history.
- **Change detection is what makes it safe and idempotent.** The `(name <> ... OR region <> ...)` predicate is why C002 is skipped and why running the same batch twice inserts nothing the second time. Delete that predicate and every customer gets a spurious new version every run.
- **Date boundaries are half-open: `>= effective_date AND < end_date`.** Using `<=` on the end date would make the expired and new versions *both* match on the boundary day (2025-06-15) and return two rows. The `9999-12-31` sentinel keeps open rows comparable without special-casing `NULL`.
- **Every version needs its own surrogate key.** The `nextval(...)` call on each insert is what lets facts pin to a specific point-in-time version. Reusing the natural key as the PK would make history unaddressable.
- **`LOAD_DATE` is hard-coded** for reproducible output; in production this is the actual load timestamp.

### 5. Discussion Topics

1. **SCD Types 0/1/2/3 trade-offs.** Type 0 (never change), Type 1 (overwrite, no history), Type 2 (new row per version, full history), Type 3 (add a "previous value" column, one step of history). When does each fit? Which one is our demo, and what would it take to turn it into a Type 1?
2. **Surrogate vs natural keys.** Why does the fact table join on `customer_key` (surrogate) rather than `customer_id` (natural)? What breaks in a Type 2 model if facts join on the natural key instead?
3. **Storage growth.** Our dimension went from 3 rows to 6 after a single load. Project that over years of daily loads on a wide, frequently-changing dimension. What controls the growth (which attributes you track), and what mitigations exist (mini-dimensions, snapshotting, Type 4 history tables)?
4. **When is Type 2 overkill?** For attributes nobody ever asks "what was it back then?" about (e.g. a corrected typo, a customer's last-login timestamp), Type 1 or not tracking at all is fine. How do you decide, per column, what deserves versioning?
5. **MERGE atomicity vs the two-statement pattern.** BigQuery's `MERGE` is atomic in one statement; DuckDB needs an explicit transaction around UPDATE + INSERT. What are the failure modes if you forget the transaction? When is the portability of two statements worth more than the elegance of one `MERGE`?
6. **Change detection and idempotency.** Why is comparing full attribute snapshots (rather than trusting an upstream "changed" flag) more robust? What happens to the dimension if the same daily batch is accidentally loaded twice — with, and without, the change-detection predicate?
