# Pydantic Models and Validation

## Learning Objectives
- Explain Pydantic's role inside FastAPI.
- Define data shapes with `BaseModel` and Python type hints.
- Add constraints and defaults with `Field`.
- Use separate **request** and **response** models.
- Understand how validation errors (`422`) are produced and returned.

## Why This Matters
Data pipelines break when bad data slips in. A missing `price`, a string where a number belongs, a negative quantity - any of these can corrupt a table or crash a downstream job. **Pydantic** is the gatekeeper that validates every incoming payload *before* your code touches it. FastAPI is built on Pydantic, so you get this validation almost for free: define the shape, and FastAPI enforces it and returns a clear `422` error to the caller when the data is wrong. This is one of the biggest reasons data engineers reach for FastAPI.

We use **Pydantic v2**, the current major version. If you find older tutorials using `.dict()`, `class Config`, or `@validator`, those are v1 spellings - the v2 equivalents are `.model_dump()`, `model_config`, and `@field_validator`.

## Concept Explanation

### What Is Pydantic?
Pydantic turns a class of type-hinted attributes into a validating data model. You describe *what valid data looks like*; Pydantic enforces it, coerces compatible types, and gives precise errors when it cannot.

```python
from pydantic import BaseModel

class Item(BaseModel):
    item_id: int
    name: str
    price: float
    active: bool = True          # default -> optional in input
    tags: list[str] = []         # default empty list
```

Construct one from a dict and it validates on the spot:

```python
Item(item_id="5", name="Widget", price="9.99")
# -> Item(item_id=5, name='Widget', price=9.99, active=True, tags=[])
#    Note: "5" was coerced to int 5, "9.99" to float 9.99.

Item(name="Widget", price="cheap")
# -> raises ValidationError:
#      item_id: Field required
#      price: Input should be a valid number
```

### How FastAPI Uses It
When you type-hint an endpoint argument with a Pydantic model, FastAPI:

1. Reads the request body as JSON.
2. Validates it against the model.
3. On success, hands your function a fully typed model instance.
4. On failure, short-circuits and returns a `422 Unprocessable Entity` with a per-field error list - **your function never runs**.

```
   JSON body  -->  Pydantic validation  -->  your function (clean data)
                          |
                     invalid?
                          |
                          v
                   422 response with field errors
```

### Adding Constraints with `Field`
Type hints check *types*; `Field` checks *values*. Use it for ranges, lengths, and documentation.

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0, description="Price in USD, must be positive")
    quantity: int = Field(default=0, ge=0)
```

Common `Field` constraints:

| Constraint | Applies to | Meaning |
|-----------|-----------|---------|
| `gt`, `ge` | numbers | greater than / greater-or-equal |
| `lt`, `le` | numbers | less than / less-or-equal |
| `min_length`, `max_length` | strings, lists | length bounds |
| `default` | any | value used when omitted |
| `description` | any | shows up in the auto docs |

### Request vs Response Models
A subtle but important pattern: the shape a client **sends** is usually not the shape you **return**. When creating an item, the client should not send an `item_id` - the server assigns it. So define two models.

```python
class ItemCreate(BaseModel):        # what the client POSTs
    name: str = Field(min_length=1)
    price: float = Field(gt=0)

class ItemOut(BaseModel):           # what the API returns
    item_id: int
    name: str
    price: float
```

Wiring the response model into the decorator (covered fully in note 104) makes FastAPI validate and filter the output too:

```python
@app.post("/items", response_model=ItemOut, status_code=201)
def create_item(item: ItemCreate):
    new = {"item_id": 1, **item.model_dump()}
    return new   # FastAPI shapes this into ItemOut and serializes to JSON
```

Benefits of splitting the models:
- Clients cannot inject server-controlled fields like `item_id`.
- You can hide internal fields (passwords, audit columns) from responses.
- The docs show accurate, separate input and output schemas.

### `model_dump()`: Model to Dict
When you need a plain dict from a model (to store it, merge it, or log it), call `.model_dump()`:

```python
item = ItemCreate(name="Widget", price=9.99)
item.model_dump()          # {'name': 'Widget', 'price': 9.99}
```

## Code Example

A complete, runnable snippet showing validation end to end:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Pydantic Demo")


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0, description="Must be positive")
    in_stock: bool = True


class ProductOut(BaseModel):
    product_id: int
    name: str
    price: float
    in_stock: bool


_DB: dict[int, dict] = {}
_next_id = 1


@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(product: ProductCreate):
    global _next_id
    record = {"product_id": _next_id, **product.model_dump()}
    _DB[_next_id] = record
    _next_id += 1
    return record
```

Try a valid and an invalid call:

```bash
uvicorn main:app --reload

# Valid -> 201 Created
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "price": 9.99}'

# Invalid (negative price) -> 422 with a clear field error
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "price": -5}'
```

The invalid call returns:
```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "price"],
      "msg": "Input should be greater than 0"
    }
  ]
}
```

## Key Takeaways
- Pydantic `BaseModel` turns type-hinted classes into self-validating data models.
- FastAPI validates request bodies automatically and returns `422` with per-field errors on failure - your handler only ever sees clean data.
- `Field(...)` adds value constraints (`gt`, `ge`, `min_length`, ...) and documentation on top of type checks.
- Use **separate request and response models** so clients cannot set server-controlled fields and so internal fields stay hidden.
- This is **Pydantic v2**: use `.model_dump()`, `model_config`, and `@field_validator`.

## Resources
- [FastAPI - Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI - Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Pydantic v2 - Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Pydantic v2 - Fields](https://docs.pydantic.dev/latest/concepts/fields/)
- [Pydantic - Migration Guide (v1 to v2)](https://docs.pydantic.dev/latest/migration/)
