# Serving Data Through FastAPI

## Learning Objectives

- Structure a data API into **routes / services / models** layers and explain why
- Load a data source once at startup and query it per request
- Return tabular/pandas results as JSON with `df.to_dict(orient="records")`
- Add basic **pagination** (`limit` / `offset`) and query parameters to endpoints
- Trace one request from URL → service → DataFrame → JSON response

## Why This Matters

On **Day 1** you built FastAPI CRUD endpoints and consumed them with `httpx`. Today you connect that to the pandas skills from note 201: a data API's real job is to **take a dataset, compute something over it, and hand back JSON** that an app, dashboard, or another service can read.

This is the everyday shape of a data-serving backend: the warehouse or file holds the data, pandas does the shaping, FastAPI exposes it over HTTP. Demo `203-dataframe-api/` and exercise `203-serve-aggregates-api.md` build exactly this.

> Note 202 called JSON "the lingua franca of APIs." This note is where you actually emit it.

## Concept Explanation

### The layered structure (routes / services / models)

Don't cram database queries, business logic, and response shapes into one giant route function. Split responsibilities so each piece is testable and swappable:

```
        HTTP request
             │
             ▼
   ┌───────────────────┐   routes/   -> URL paths, query params, HTTP concerns.
   │      ROUTES        │               Thin. Delegates to a service.
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐   services/ -> the actual work: load data, filter,
   │     SERVICES       │               groupby, aggregate with pandas.
   └─────────┬─────────┘               Knows nothing about HTTP.
             ▼
   ┌───────────────────┐   models/   -> Pydantic schemas describing the
   │      MODELS        │               request/response shape (validation + docs).
   └───────────────────┘
             │
             ▼
     data source (CSV / DataFrame / BigQuery)
```

- **routes** — declare `@app.get(...)`, read query params, call a service, return the result. Keep it thin.
- **services** — the pandas/data logic. Pure functions over the data; no `Request`/`Response` here.
- **models** — Pydantic classes that define and validate the JSON shape (and auto-generate the `/docs` schema).

Why bother for a small app? Because when the data source changes from a CSV to BigQuery (Day 4), you only touch **services** — routes and models don't move.

### Load the data once, at startup

Don't `read_csv` on every request — that re-reads the file each time and kills performance. Load it **once** when the app starts and keep the DataFrame in memory.

```python
# services/data.py
import pandas as pd
from pathlib import Path

_DF: pd.DataFrame | None = None

def load_data() -> pd.DataFrame:
    """Read the CSV once; cache the DataFrame for the process lifetime."""
    global _DF
    if _DF is None:
        csv = Path(__file__).parent.parent / "data" / "sales.csv"
        _DF = pd.read_csv(csv, parse_dates=["order_date"])
    return _DF
```

The modern FastAPI way to trigger this at boot is a **lifespan** handler:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.data import load_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data()          # warm the cache before serving traffic
    yield                # app runs
    # (teardown/cleanup would go here)

app = FastAPI(lifespan=lifespan)
```

### Returning tabular data as JSON: `to_dict(orient="records")`

A pandas result isn't JSON — you must convert it. The `records` orientation gives you a **list of `{column: value}` dicts**, which is exactly what an API should return and what FastAPI serializes automatically.

```python
df = pd.DataFrame({"dept": ["Web", "Data"], "headcount": [3, 2]})

df.to_dict(orient="records")
# [{"dept": "Web", "headcount": 3}, {"dept": "Data", "headcount": 2}]
```

Compare the orientations so you pick deliberately:

| `orient=` | Shape | Use for |
|-----------|-------|---------|
| `"records"` | `[{col: val}, ...]` | **API responses** (default choice) |
| `"list"` | `{col: [vals]}` | column-oriented consumers |
| `"index"` | `{idx: {col: val}}` | keyed-by-row-id lookups |

> **Gotcha:** JSON has no `NaN`. If your DataFrame has missing values, `NaN` serializes to invalid JSON. Fix it before returning: `df = df.where(df.notna(), None)` (turns `NaN` into JSON `null`), or `df.fillna(...)`.
>
> **Gotcha:** after a `groupby`, the group key is the *index*, not a column. Call `.reset_index()` before `to_dict` or the key vanishes from the JSON.

### Query parameters and pagination

Function arguments on a route become **query parameters** automatically. Give them types and defaults; FastAPI validates and documents them.

```python
@app.get("/records")
def list_records(limit: int = 50, offset: int = 0, dept: str | None = None):
    df = load_data()
    if dept:                                   # optional filter (?dept=Web)
        df = df[df["dept"] == dept]
    total = len(df)
    page = df.iloc[offset : offset + limit]    # slice the page with iloc
    return {
        "total": total,                        # total matching rows (before paging)
        "limit": limit,
        "offset": offset,
        "results": page.to_dict(orient="records"),
    }
```

Request: `GET /records?dept=Web&limit=10&offset=20` → the third page of 10 Web rows.

**Why paginate?** Returning a million rows in one response is slow and can OOM the client. `limit`/`offset` lets callers walk the data in pages. Always return the `total` so the client knows how many pages exist.

Use `Query(...)` to add validation and docs:

```python
from fastapi import Query

@app.get("/records")
def list_records(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    ...
# limit is now clamped to 1..500; bad values get an automatic 422 error.
```

## Code Example

A complete, runnable single-file data API. It loads a CSV at startup and exposes raw (paginated), summary, and grouped-aggregate endpoints. (The demo splits this into routes/services/models folders; here it's one file so you can run it immediately.)

```python
# app.py
from contextlib import asynccontextmanager
from pathlib import Path
import io
import pandas as pd
from fastapi import FastAPI, Query, HTTPException

DF: pd.DataFrame | None = None

# A tiny inline dataset so this runs with zero setup.
# In the demo this is a real CSV loaded via read_csv.
SAMPLE_CSV = """order_id,dept,region,amount
1,Web,East,120.50
2,Data,West,300.00
3,Web,West,90.25
4,Ops,East,45.00
5,Data,East,275.75
6,Web,East,60.00
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    global DF
    DF = pd.read_csv(io.StringIO(SAMPLE_CSV))   # load ONCE at startup
    yield

app = FastAPI(title="DataFrame API", lifespan=lifespan)

def clean(df: pd.DataFrame) -> list[dict]:
    """NaN -> None so the JSON is valid, then to records."""
    return df.where(df.notna(), None).to_dict(orient="records")

@app.get("/health")
def health():
    return {"status": "ok", "rows": len(DF)}

@app.get("/records")
def records(limit: int = Query(50, ge=1, le=500),
            offset: int = Query(0, ge=0),
            dept: str | None = None):
    df = DF if dept is None else DF[DF["dept"] == dept]
    page = df.iloc[offset : offset + limit]
    return {"total": len(df), "limit": limit, "offset": offset,
            "results": clean(page)}

@app.get("/summary")
def summary():
    """Overall stats — like SELECT COUNT(*), SUM(amount), AVG(amount)."""
    return {
        "orders": int(len(DF)),
        "total_amount": round(float(DF["amount"].sum()), 2),
        "avg_amount": round(float(DF["amount"].mean()), 2),
    }

@app.get("/by-dept")
def by_dept():
    """Aggregate per department -> JSON. GROUP BY dept."""
    agg = (DF.groupby("dept")
             .agg(orders=("order_id", "count"),
                  total_amount=("amount", "sum"),
                  avg_amount=("amount", "mean"))
             .round(2)
             .reset_index())            # <- turn the group key back into a column
    return {"results": clean(agg)}

@app.get("/by-dept/{dept}")
def one_dept(dept: str):
    sub = DF[DF["dept"] == dept]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No orders for dept '{dept}'")
    return {"dept": dept, "orders": clean(sub)}
```

Run and try it:

```bash
pip install fastapi uvicorn pandas
uvicorn app:app --reload

# then, in another terminal:
curl "http://127.0.0.1:8000/summary"
curl "http://127.0.0.1:8000/by-dept"
curl "http://127.0.0.1:8000/records?dept=Web&limit=2&offset=0"
# interactive docs (auto-generated): http://127.0.0.1:8000/docs
```

## Key Takeaways

- Split a data API into **routes** (HTTP), **services** (pandas/data logic), **models** (Pydantic shapes) — so the data source can change without touching the routes.
- **Load the dataset once at startup** (lifespan handler), not on every request.
- Convert results with **`df.to_dict(orient="records")`** — a list of `{column: value}` dicts, the natural JSON shape.
- After `groupby`, call **`.reset_index()`**; and turn **`NaN` into `None`** or the JSON is invalid.
- Add **`limit`/`offset` pagination** and typed query params; return `total` so clients can page.
- FastAPI turns typed function args into validated, self-documenting query parameters (`/docs`).

## Resources

- FastAPI query parameters: <https://fastapi.tiangolo.com/tutorial/query-params/>
- FastAPI lifespan events: <https://fastapi.tiangolo.com/advanced/events/>
- pandas `DataFrame.to_dict`: <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_dict.html>
- Cross-reference: `notes/201-pandas-refresher.md` (groupby/agg) · `demos/203-dataframe-api/` · `exercises/203-serve-aggregates-api.md`
