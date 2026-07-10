# Demo 203 — DataFrame API

A small FastAPI app that loads a CSV into pandas **once at startup** and exposes
endpoints returning **pandas-computed aggregates as JSON**. This ties Day 1
(FastAPI) to today (pandas), and is the reference implementation behind
[`notes/204-serving-data-through-fastapi.md`](../../notes/204-serving-data-through-fastapi.md).

## Layout (routes / services / models)

```
203-dataframe-api/
├── data/sales.csv        20 sample sales rows
└── app/
    ├── main.py           FastAPI app + startup (lifespan) that warms the cache
    ├── routes.py         thin HTTP endpoints, query params  -> call services
    ├── services.py       ALL the pandas logic (load, groupby, aggregate, paginate)
    └── models.py         Pydantic response shapes (validation + /docs schema)
```

The point of the split: `services.py` is the only file that knows about the data
source. Swap the CSV for BigQuery (Day 4) and the routes/models don't change.

## Run

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open the auto-generated interactive docs: <http://127.0.0.1:8000/docs>

## Endpoints & example requests

```bash
# health check (also proves the CSV loaded)
curl "http://127.0.0.1:8000/health"
# -> {"status":"ok","rows":20}

# dataset-wide totals
curl "http://127.0.0.1:8000/summary"
# -> {"orders":20,"total_revenue":...,"avg_order_revenue":...,"customers":6}

# revenue aggregated per category (groupby + agg)
curl "http://127.0.0.1:8000/by-category"
# -> [{"category":"Widgets","orders":...,"total_revenue":...,"avg_revenue":...}, ...]

# raw orders, paginated + optional filter
curl "http://127.0.0.1:8000/orders?limit=5&offset=0"
curl "http://127.0.0.1:8000/orders?region=East&limit=3"
```

## What to observe

- **/summary** and **/by-category** are pandas aggregations (`sum`, `mean`,
  `nunique`, `groupby`) served straight out as JSON — no database involved.
- **/by-category** calls `.reset_index()` after the groupby so the group key
  becomes a real field in the JSON (a very common gotcha — see note 204).
- **/orders** shows `limit`/`offset` pagination and an optional `?region=`
  filter. Try `limit=999` — FastAPI rejects it with a 422 because the route
  caps it at 100 via `Query(le=100)`.
- The CSV is read **once** (in `main.py`'s lifespan, via `services.load_data()`),
  not per request. Restart with `--reload` and the first request is still snappy.

## How this connects to the rest of the week

- Uses the pandas ops from **note 201** (groupby/agg/filter).
- Emits JSON as described in **note 202 / 204** (`to_dict(orient="records")`).
- **Exercise 203** has you add your own aggregate endpoint on top of this pattern.

## Follow-Along Build Walkthrough

A "build it live with me" guide for teaching this demo from scratch. The audience
knows Python and SQL well, has minimal pandas, and saw FastAPI on Day 1. We build
the four files in the order a learner should meet them — data shapes first, data
logic second, HTTP third, wiring last.

### 1. Intro — what we're building and why

We're building a small FastAPI application that reads a CSV of sales orders into a
pandas DataFrame **once, at startup**, and then serves **pandas-computed aggregates
as JSON** over HTTP. No database — the whole dataset lives in memory as a DataFrame.

The teaching goal is to show a clean **three-layer split**:

- **models** — the *shapes* the API returns (Pydantic classes).
- **services** — all the *pandas/data logic* (load, groupby, aggregate, paginate).
  This layer knows nothing about HTTP.
- **routes** — thin HTTP endpoints that parse query params and delegate to services.

Because only `services.py` touches the data source, we could later swap the CSV for
a real database and the routes and models would not change. That separation is the
whole point of the demo; the pandas is the vehicle.

### 2. Step-by-step assembly

Start from an empty folder with this structure in mind:

```
203-dataframe-api/
├── data/sales.csv
└── app/
    ├── models.py
    ├── services.py
    ├── routes.py
    └── main.py
```

#### Step 0 — the data

Drop a CSV in `data/sales.csv`. It has one row per order with these columns:

```
order_id,order_date,customer,region,category,quantity,unit_price
1001,2026-01-05,Ada,East,Widgets,4,12.50
1002,2026-01-06,Linus,West,Gadgets,2,45.00
...
```

Note there is **no `revenue` column** — we compute that in pandas. That's
deliberate: it gives us a derived column to demonstrate, and it mirrors real life
where you enrich raw data after loading it.

#### Step 1 — `models.py` (the response shapes)

We start here because it forces us to answer "what does each endpoint return?"
before writing any logic. Each class is a Pydantic `BaseModel` — a typed contract
that FastAPI uses both to validate outgoing data and to generate the `/docs` schema.

```python
"""Pydantic response models — the shapes this API returns."""

from pydantic import BaseModel


class Summary(BaseModel):
    orders: int
    total_revenue: float
    avg_order_revenue: float
    customers: int


class CategoryAgg(BaseModel):
    category: str
    orders: int
    total_revenue: float
    avg_revenue: float


class OrderRecord(BaseModel):
    order_id: int
    order_date: str
    customer: str
    region: str
    category: str
    quantity: int
    unit_price: float
    revenue: float


class PagedOrders(BaseModel):
    total: int
    limit: int
    offset: int
    results: list[OrderRecord]
```

- `Summary` — dataset-wide totals (one object).
- `CategoryAgg` — one row of the per-category aggregation; the by-category endpoint
  returns a `list[CategoryAgg]`.
- `OrderRecord` — one raw order, including the derived `revenue` and `order_date`
  as a plain string (not a datetime — we format it before it leaves the service).
- `PagedOrders` — the pagination envelope: `total`/`limit`/`offset` plus the
  `results` list. This is what lets a client page through the data.

Why models first: naming the fields up front is the API contract. Everything
downstream (the pandas output, the endpoint responses) must produce exactly these
keys and types, so defining them first keeps the rest honest.

#### Step 2 — `services.py` (all the pandas)

This is the heart of the demo and where the pandas teaching happens. It knows
nothing about FastAPI, `Request`, or status codes — just DataFrames in, plain
Python dicts/lists out.

**Load once and cache** (the startup load):

```python
from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).parent.parent / "data" / "sales.csv"

_DF: pd.DataFrame | None = None


def load_data() -> pd.DataFrame:
    """Read the CSV once, cache it, and add a derived `revenue` column."""
    global _DF
    if _DF is None:
        df = pd.read_csv(DATA_FILE, parse_dates=["order_date"])
        df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
        _DF = df
    return _DF
```

`_DF` is a module-level cache. The first call reads the CSV, parses `order_date`
into real datetimes, and adds the `revenue = quantity * unit_price` column. Every
later call returns the same in-memory DataFrame. We call this at startup so no
request ever pays the file-read cost.

**A DataFrame-to-JSON helper** (used by the record-returning endpoints):

```python
def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list of dicts, with NaN turned into None (valid JSON)."""
    df = df.copy()
    if "order_date" in df.columns:
        df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    return df.where(df.notna(), None).to_dict(orient="records")
```

Two gotchas this handles for us: datetimes aren't JSON-serializable (so we format
them back to `YYYY-MM-DD` strings), and pandas `NaN` isn't valid JSON (so we turn
it into `None`, which becomes `null`). `to_dict(orient="records")` is the key move
that turns rows into a list of `{column: value}` dicts.

**The three data functions**, one per endpoint:

```python
def summary() -> dict:
    """Overall totals across the whole dataset."""
    df = load_data()
    return {
        "orders": int(len(df)),
        "total_revenue": round(float(df["revenue"].sum()), 2),
        "avg_order_revenue": round(float(df["revenue"].mean()), 2),
        "customers": int(df["customer"].nunique()),
    }


def by_category() -> list[dict]:
    """Aggregate revenue per category (GROUP BY category)."""
    df = load_data()
    agg = (
        df.groupby("category")
        .agg(orders=("order_id", "count"),
             total_revenue=("revenue", "sum"),
             avg_revenue=("revenue", "mean"))
        .round(2)
        .reset_index()                        # group key -> column
        .sort_values("total_revenue", ascending=False)
    )
    return _records(agg)


def orders_page(limit: int, offset: int, region: str | None) -> dict:
    """Paginated raw orders, with an optional region filter."""
    df = load_data()
    if region:
        df = df[df["region"] == region]
    total = len(df)
    page = df.iloc[offset:offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": _records(page),
    }
```

- `summary()` is straight aggregation: `sum`, `mean`, `nunique`. Note the
  `int(...)`/`float(...)` casts — pandas returns numpy scalars, and we hand back
  plain Python numbers. Keys match `Summary` exactly.
- `by_category()` is the SQL `GROUP BY category` translated to pandas: `groupby`
  then named `agg` (which names the output columns to match `CategoryAgg`), then
  `reset_index()` to promote the group key back into a real column, then sort. The
  `reset_index()` is the classic gotcha — without it, `category` is the index and
  won't appear in the JSON.
- `orders_page()` does the optional `region` filter (a boolean mask), counts the
  filtered `total`, then slices the page with `.iloc[offset:offset+limit]`. It
  returns the pagination envelope that matches `PagedOrders`.

Notice the layering: these return dicts and lists whose keys line up with the
models from Step 1, but nothing here imports FastAPI or the models. The service is
independently testable and swappable.

#### Step 3 — `routes.py` (the HTTP endpoints)

Now the thin HTTP layer. Each route maps a URL to a service call and declares its
`response_model` so FastAPI validates the output and documents it.

```python
from fastapi import APIRouter, Query

from . import services
from .models import CategoryAgg, PagedOrders, Summary

router = APIRouter()


@router.get("/summary", response_model=Summary)
def get_summary():
    """Dataset-wide totals."""
    return services.summary()


@router.get("/by-category", response_model=list[CategoryAgg])
def get_by_category():
    """Revenue aggregated per product category."""
    return services.by_category()


@router.get("/orders", response_model=PagedOrders)
def get_orders(
    limit: int = Query(10, ge=1, le=100, description="rows per page"),
    offset: int = Query(0, ge=0, description="rows to skip"),
    region: str | None = Query(None, description="filter by region, e.g. East"),
):
    """Raw orders, paginated, with optional ?region= filter."""
    return services.orders_page(limit=limit, offset=offset, region=region)
```

- The routes are one-liners: parse input, call the service, return. This is what
  "thin" means — no pandas here.
- `response_model=...` connects each endpoint to a model from Step 1. FastAPI
  coerces and validates the service's output against it.
- The `Query(...)` constraints on `/orders` are declarative validation done *by the
  framework, before your code runs*: `limit` defaults to 10 and must be `1..100`
  (`ge=1, le=100`), `offset` must be `>= 0`, and `region` is optional. Anything out
  of range gets an automatic **422** — we never write a manual check.

Concern separation, made concrete: URLs and query-param validation live here; the
data math lives in services; the shapes live in models.

#### Step 4 — `main.py` (app + router + startup load)

Finally, wire it together and warm the cache at startup.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import services
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    services.load_data()      # read + prep the DataFrame before serving traffic
    yield


app = FastAPI(
    title="DataFrame API",
    description="Serves pandas-computed aggregates from a CSV as JSON.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "rows": len(services.load_data())}
```

- The `lifespan` context manager runs `services.load_data()` **before** the app
  accepts requests — that's the startup load. Everything before `yield` runs once
  on startup; anything after would run on shutdown.
- `app.include_router(router)` mounts all the endpoints from Step 3.
- `/health` is a tiny liveness check that also proves the CSV loaded by returning
  the row count.

### 3. How it fits together — tracing a request

Follow `GET /by-category`:

1. **HTTP in.** Request hits FastAPI, matched to `get_by_category()` in `routes.py`.
2. **Route delegates.** The route does no work itself; it calls
   `services.by_category()`.
3. **Service runs pandas.** `by_category()` calls `load_data()` (returns the
   already-cached DataFrame — no file read), does `groupby("category").agg(...)`,
   `reset_index()`, `sort_values(...)`, then `_records(...)` to convert the result
   to a list of dicts with JSON-safe values.
4. **Back through the model.** The list of dicts returns to the route, where
   `response_model=list[CategoryAgg]` validates each dict has `category`, `orders`,
   `total_revenue`, `avg_revenue` with the right types.
5. **JSON out.** FastAPI serializes the validated models to a JSON array and sends
   it back.

Every layer touched exactly one concern: routes (HTTP), services (pandas), models
(shape/validation).

### 4. Demo Notes (instructor)

**What to run** (from inside the `203-dataframe-api/` folder):

```bash
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000/docs> — the interactive Swagger UI. Point out that
every endpoint, its query params, and its response schema are auto-documented from
the models and `Query(...)` declarations. Drive the demo from `/docs` rather than
curl if you want it visual.

**Example requests and expected JSON:**

```bash
curl "http://127.0.0.1:8000/health"
# -> {"status":"ok","rows":20}

curl "http://127.0.0.1:8000/summary"
# -> {"orders":20,"total_revenue":...,"avg_order_revenue":...,"customers":6}
#    (6 distinct customers: Ada, Linus, Grace, Guido, Bjarne, Margaret)

curl "http://127.0.0.1:8000/by-category"
# -> [{"category":"Widgets","orders":...,"total_revenue":...,"avg_revenue":...},
#     {"category":"Gadgets",...}, {"category":"Gizmos",...}]
#    (sorted by total_revenue descending)

curl "http://127.0.0.1:8000/orders?limit=3&offset=0"
# -> {"total":20,"limit":3,"offset":0,"results":[ {order_id 1001...}, 1002, 1003 ]}
#    each result has a computed "revenue" field (e.g. 4 * 12.50 = 50.0)

curl "http://127.0.0.1:8000/orders?region=East&limit=3"
# -> {"total":11,"limit":3,"offset":0,"results":[ ...only East rows... ]}
```

**Show the 422.** This is the money moment for framework validation:

```bash
curl "http://127.0.0.1:8000/orders?limit=999"
# -> HTTP 422 Unprocessable Entity
#    {"detail":[{"loc":["query","limit"],"msg":"Input should be less than or
#     equal to 100", ...}]}
```

We never wrote that check — `Query(le=100)` produced it. Same happens for
`limit=0` (`ge=1`) or `offset=-1` (`ge=0`).

**Why load-at-startup vs per-request.** Reading and prepping the CSV on every
request would be wasteful and slow; the file doesn't change between requests. The
`lifespan` load reads it exactly once, so the first real request is already fast.
You can demonstrate this by noting `/health` returns instantly. (Trade-off: the
data is frozen until restart — see Discussion.)

**Common gotchas to call out:**
- Forgetting `reset_index()` after `groupby` — `category` stays as the index and
  vanishes from the JSON.
- numpy scalars: returning `df["revenue"].sum()` directly can serialize oddly;
  cast with `float(...)`/`int(...)`.
- `NaN` is not valid JSON — the `_records` helper converts it to `None`.
- datetimes aren't JSON-serializable — we format `order_date` to a string.
- Run `uvicorn` from the demo folder so `app.main:app` and the relative
  `data/sales.csv` path both resolve.

### 5. Discussion Topics

1. **Why split into routes / services / models?** What breaks if you put the pandas
   directly inside the route functions? How does the split help testing and
   swapping the data source?
2. **Load-at-startup trade-offs.** We cache the DataFrame for the life of the
   process. What are the upsides (speed) and downsides (stale data, memory,
   no hot-reload of the CSV)? When would per-request or a TTL cache be better?
3. **Pagination design.** Why return a `total`/`limit`/`offset` envelope instead of
   a bare list? What are the limits of offset-based pagination on large datasets,
   and what is cursor-based pagination?
4. **DataFrame-to-dict serialization.** Why do we need `_records()` at all? Discuss
   `NaN` -> `null`, datetime formatting, and numpy vs Python scalar types.
5. **Scaling beyond in-memory.** This works because the CSV is tiny. What changes
   when the data is 50 GB? How does the routes/services/models split make moving to
   a database (Day 4) a one-file change?
6. **Framework vs hand-rolled validation.** We got the 422 for free from
   `Query(le=100)`. When is declarative validation enough, and when do you need
   custom logic in the service layer?
