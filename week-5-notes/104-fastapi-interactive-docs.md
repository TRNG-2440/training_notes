# FastAPI Interactive Docs

## Learning Objectives
- Use the auto-generated Swagger UI (`/docs`) and ReDoc (`/redoc`).
- Understand the OpenAPI schema that powers them.
- Enrich docs with docstrings, `tags`, `summary`, and `response_model`.
- Set explicit `status_code`s for endpoints.
- Signal errors correctly with `HTTPException`.

## Why This Matters
An API nobody knows how to call is useless. Hand-written API docs rot the moment code changes. FastAPI eliminates the problem: it reads your routes, type hints, Pydantic models, and docstrings and generates **live, interactive documentation** that is always in sync with the code. For a data engineer publishing an internal API, this means a data analyst on another team can discover your endpoints, see the exact request/response shapes, and test them in the browser - without emailing you. Good docs also mean correct status codes and error messages, so callers can handle failures programmatically (which is exactly what you will do in note 105).

## Concept Explanation

### Two Doc Pages, One Schema
FastAPI generates an **OpenAPI** document - a machine-readable JSON description of your entire API - and serves two human-friendly renderings of it:

| URL | Tool | Best for |
|-----|------|----------|
| `/docs` | **Swagger UI** | Interactive testing ("Try it out" buttons) |
| `/redoc` | **ReDoc** | Clean, readable reference / print |
| `/openapi.json` | raw OpenAPI | Feeding codegen tools, other apps |

```
   Your code (routes,          FastAPI          /docs   (Swagger UI)
   type hints, models,   -->   builds     -->   /redoc  (ReDoc)
   docstrings)                 OpenAPI          /openapi.json (raw)
```

You get all three for free the moment you run the app. Everything below is about making them *better*.

### Docstrings Become Descriptions
The docstring of an endpoint function becomes its description in the docs. Markdown works.

```python
@app.get("/stats", tags=["analytics"], summary="Aggregate pipeline stats")
def get_stats():
    """
    Return high-level pipeline metrics.

    - **records_processed**: total rows handled today
    - **status**: `nominal` or `degraded`
    """
    return {"records_processed": 4_500_000, "status": "nominal"}
```

- `tags=[...]` groups endpoints into sections in the UI.
- `summary=...` is the short line shown in the endpoint list.
- The docstring is the expandable long description.

### `response_model`: Document and Enforce Output
Declaring `response_model` does three jobs at once: it documents the exact response shape, it filters the returned data to only those fields, and it validates your own output.

```python
from pydantic import BaseModel

class ItemOut(BaseModel):
    item_id: int
    name: str

@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int):
    # Even if this dict has extra keys, only item_id and name are returned.
    return {"item_id": item_id, "name": "Widget", "internal_flag": True}
```

### Explicit Status Codes
`GET` returns `200` by default, but other operations should say what they mean. A creation should return `201 Created`; a deletion that returns nothing should return `204 No Content`.

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(...): ...

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    ...
    return None   # 204 = empty body
```

Using the `status` constants (`status.HTTP_201_CREATED`) instead of bare numbers makes intent obvious and shows up correctly in the docs.

### Signaling Errors with `HTTPException`
When something goes wrong - a missing record, a bad request - do **not** return an error dict with a `200` status. That lies to the caller. Instead `raise HTTPException`, which produces the right status code and a standard `{"detail": ...}` body.

```python
from fastapi import HTTPException, status

@app.get("/items/{item_id}")
def get_item(item_id: int):
    item = _DB.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item
```

Response for a missing item:
```
HTTP/1.1 404 Not Found
Content-Type: application/json

{"detail": "Item 999 not found"}
```

The caller can now check `response.status_code == 404` and react. That reliability is the whole point of using real status codes.

## Code Example

A small, fully documented endpoint set:

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Well-Documented Items API",
    description="Demonstrates docstrings, tags, response models, and errors.",
    version="1.0.0",
)


class ItemOut(BaseModel):
    item_id: int
    name: str
    price: float


class ItemCreate(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


_DB: dict[int, dict] = {1: {"item_id": 1, "name": "Keyboard", "price": 49.99}}
_next_id = 2


@app.get("/items/{item_id}", response_model=ItemOut, tags=["items"],
         summary="Fetch one item")
def get_item(item_id: int):
    """Return a single item by its **item_id**, or `404` if it does not exist."""
    item = _DB.get(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Item {item_id} not found")
    return item


@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED,
          tags=["items"], summary="Create an item")
def create_item(item: ItemCreate):
    """Create a new item. The server assigns the **item_id**."""
    global _next_id
    record = {"item_id": _next_id, **item.model_dump()}
    _DB[_next_id] = record
    _next_id += 1
    return record
```

Run it and open the docs:

```bash
uvicorn main:app --reload
# then browse to:
#   http://127.0.0.1:8000/docs     (Swagger UI - click "Try it out")
#   http://127.0.0.1:8000/redoc    (ReDoc)
#   http://127.0.0.1:8000/openapi.json
```

In `/docs`, expand `POST /items`, click **Try it out**, edit the JSON body, and hit **Execute**. You will see the live request, the response body, and the status code - a full test loop without leaving the browser.

## Key Takeaways
- FastAPI auto-generates **Swagger UI** at `/docs`, **ReDoc** at `/redoc`, and the raw **OpenAPI** schema at `/openapi.json`.
- Docstrings, `tags`, and `summary` make those docs readable; write them.
- `response_model` documents, filters, and validates your output in one declaration.
- Set explicit `status_code`s (`201` for create, `204` for empty delete) using the `status` constants.
- Signal failures with `raise HTTPException(status_code=..., detail=...)` - never a fake `200` error dict.

## Resources
- [FastAPI - First Steps: Interactive API docs](https://fastapi.tiangolo.com/tutorial/first-steps/#interactive-api-docs)
- [FastAPI - Handling Errors (HTTPException)](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI - Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/)
- [FastAPI - Metadata and Docs URLs](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI Initiative](https://www.openapis.org/)
