# FastAPI Routing and Parameters

## Learning Objectives
- Define routes for different HTTP methods with `@app` decorators.
- Capture **path parameters** to select a specific resource.
- Accept **query parameters** for filtering, sorting, and pagination.
- Receive **request bodies** on POST/PUT/PATCH.
- Organize endpoints with `APIRouter`, using `prefix` and `tags`.

## Why This Matters
Routes are the address system of your API. A dashboard asking for "sales record 42" and a report asking for "the first 20 active items" are hitting different routes with different parameters. Getting routing and parameters right is what lets a single API serve many tailored slices of data instead of one giant dump. As your API grows past a handful of endpoints, `APIRouter` keeps it from collapsing into one unreadable file - the same way you would split a large Python program into modules.

## Concept Explanation

### Three Ways Data Enters an Endpoint
When a client calls your API, data arrives through three channels. FastAPI decides which is which from how you declare your function's arguments.

| Channel | Where it lives | Declared as | Typical use |
|---------|---------------|-------------|-------------|
| **Path parameter** | Inside the URL path: `/items/5` | Name matches `{...}` in the route | Identify one specific resource |
| **Query parameter** | After `?`: `/items?limit=20&active=true` | Function arg *not* in the path | Filter, sort, paginate |
| **Request body** | JSON payload of the request | A Pydantic model arg | Send new/updated data (note 103) |

```
GET  /items/5?active=true
         |  |     |
         |  |     +-- query parameter:  active=true
         |  +-------- path parameter:   item_id = 5
         +----------- the collection ("items")
```

### Path Parameters
Path parameters are the parts of the URL that vary. You mark them with curly braces in the route string and add a matching function argument with a type hint. FastAPI casts the incoming text to that type and returns a `422` if it cannot.

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    # A request to /items/5 gives you item_id == 5 (an int, not "5")
    return {"item_id": item_id}
```

### Query Parameters
Any function argument that is **not** named in the path becomes a query parameter. Give it a default value to make it optional; omit the default to make it required.

```python
@app.get("/items")
def list_items(limit: int = 20, offset: int = 0, active: bool | None = None):
    # /items                       -> limit=20, offset=0, active=None
    # /items?limit=5&active=true   -> limit=5,  offset=0, active=True
    return {"limit": limit, "offset": offset, "active": active}
```

Note that FastAPI parses `?active=true` into a real Python `bool`, and `?limit=5` into an `int`. Type hints do double duty as parsing rules and validation rules.

### Request Bodies (preview)
To *receive* JSON, you declare a Pydantic model argument. FastAPI reads the request body, validates it, and hands you a typed object. Full treatment is in note 103; here is the shape:

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    price: float

@app.post("/items")
def create_item(item: ItemCreate):
    # 'item' is a validated ItemCreate object
    return {"created": item.name, "price": item.price}
```

### Organizing with `APIRouter`
Putting every endpoint in `main.py` works for a demo and falls apart for a real service. `APIRouter` lets you group related endpoints in their own module, give them a shared URL **prefix** and documentation **tags**, then plug the whole group into the app with one line.

```
project/
+-- app/
    +-- main.py              # creates FastAPI(), includes routers
    +-- routers/
        +-- items.py         # APIRouter for everything under /items
```

A router is used exactly like the `app` object - `@router.get(...)`, `@router.post(...)` - but its routes are scoped under the prefix.

## Code Example

### `app/routers/items.py`
```python
from fastapi import APIRouter, HTTPException

# Every route below is automatically prefixed with /items,
# and grouped under the "items" tag in the docs.
router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Item not found"}},
)

# A tiny in-memory store so the demo runs without a database.
_ITEMS = {
    1: {"item_id": 1, "name": "Keyboard", "price": 49.99, "active": True},
    2: {"item_id": 2, "name": "Mouse", "price": 19.99, "active": False},
}


# GET /items  -> list, with query params for paging + filtering
@router.get("")
def list_items(limit: int = 20, offset: int = 0, active: bool | None = None):
    rows = list(_ITEMS.values())
    if active is not None:
        rows = [r for r in rows if r["active"] == active]
    return rows[offset : offset + limit]


# GET /items/{item_id}  -> one resource, selected by path param
@router.get("/{item_id}")
def get_item(item_id: int):
    item = _ITEMS.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item
```

### `app/main.py`
```python
from fastapi import FastAPI
from .routers import items

app = FastAPI(title="Items API", version="0.1.0")

# Mount the router. Its routes now live under /items.
app.include_router(items.router)


@app.get("/")
def read_root():
    return {"message": "Items API. See /docs for the interactive docs."}
```

### Run and try it
```bash
uvicorn app.main:app --reload
```
```bash
curl "http://127.0.0.1:8000/items"                 # list all
curl "http://127.0.0.1:8000/items?active=true"     # filter
curl "http://127.0.0.1:8000/items?limit=1&offset=1" # paginate
curl "http://127.0.0.1:8000/items/1"               # one item
curl "http://127.0.0.1:8000/items/999"             # -> 404 with detail
```

## Key Takeaways
- **Path params** (`/items/{id}`) select one resource; **query params** (`?limit=20`) filter/sort/page; **bodies** carry JSON payloads.
- An argument named in the route path is a path param; any other argument is a query param (or, if it is a Pydantic model, a body).
- Type hints parse *and* validate incoming values automatically.
- `APIRouter` groups endpoints under a shared `prefix` and `tags`; `app.include_router(...)` mounts them.
- Prefer `raise HTTPException(status_code=404, ...)` over returning ad-hoc error dicts - see note 104.

## Resources
- [FastAPI - Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI - Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI - Bigger Applications (APIRouter)](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [MDN - HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
