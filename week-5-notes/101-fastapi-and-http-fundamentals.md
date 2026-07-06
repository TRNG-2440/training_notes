# FastAPI and HTTP Fundamentals

## Learning Objectives
- Explain what an API is and why data engineers build them.
- Describe the anatomy of an HTTP request and response.
- Identify the common HTTP methods (GET/POST/PUT/PATCH/DELETE) and status code families.
- Understand JSON as the wire format for Data APIs.
- Distinguish ASGI from WSGI and explain the role of Uvicorn.
- Write and run your first `@app.get` FastAPI application.

## Why This Matters
Your pipelines produce clean, valuable data and land it in warehouses, lakes, and databases. But stored data that nobody can reach is dead data. An **API (Application Programming Interface)** is the doorway other programs use to *ask for* that data over the network. Dashboards, mobile apps, partner systems, and other services do not query your warehouse directly - they call an API you expose.

FastAPI has become the default choice for Python Data APIs because it is fast, it validates data automatically, and it generates its own documentation. Today you will learn both halves of the story: how to **serve** data with FastAPI, and (in note 105) how to **consume** other people's APIs from Python.

## Concept Explanation

### What Is an API?
An API is a contract. It says: "Send me a request shaped *this* way, and I will send you a response shaped *that* way." A **web API** (also called a REST API or HTTP API) uses HTTP as its transport, the same protocol your browser uses to load web pages.

```
   CLIENT                                       SERVER
 (browser,                                   (your FastAPI
  script,          HTTP request              app running on
  dashboard)  ----------------------->       Uvicorn)
                                                  |
                                             looks up data,
                                             runs your code
                                                  |
              <-----------------------
                    HTTP response
                    (JSON body)
```

The client and server can be written in completely different languages. They only have to agree on the HTTP + JSON contract. That is the whole point.

### Anatomy of an HTTP Request
Every request has four parts:

| Part | Example | Purpose |
|------|---------|---------|
| **Method** | `GET` | The *verb* - what action you want |
| **Path (URL)** | `/items/5?active=true` | The *resource* you want, plus query string |
| **Headers** | `Accept: application/json` | Metadata about the request |
| **Body** | `{"name": "Widget"}` | The payload (only for POST/PUT/PATCH) |

A raw GET request looks like this:

```
GET /items/5?active=true HTTP/1.1
Host: api.example.com
Accept: application/json
```

### Anatomy of an HTTP Response
Every response has three parts:

| Part | Example | Purpose |
|------|---------|---------|
| **Status code** | `200 OK` | Did it work? |
| **Headers** | `Content-Type: application/json` | Metadata about the response |
| **Body** | `{"item_id": 5, "name": "Widget"}` | The returned data |

```
HTTP/1.1 200 OK
Content-Type: application/json

{"item_id": 5, "name": "Widget"}
```

### HTTP Methods (Verbs)
REST APIs map CRUD operations onto HTTP methods. This mapping is a convention, and following it makes your API predictable.

| Method | CRUD | Meaning | Has a body? | Idempotent? |
|--------|------|---------|-------------|-------------|
| `GET` | Read | Fetch a resource or list | No | Yes |
| `POST` | Create | Make a new resource | Yes | No |
| `PUT` | Update | Replace a resource wholesale | Yes | Yes |
| `PATCH` | Update | Modify part of a resource | Yes | No |
| `DELETE` | Delete | Remove a resource | No | Yes |

*Idempotent* means calling it repeatedly has the same effect as calling it once. `GET`ting item 5 ten times is harmless; `POST`ing ten times creates ten records.

### HTTP Status Codes
The status code is the first thing a client checks. Codes are grouped by their first digit:

| Range | Family | Meaning | Common examples |
|-------|--------|---------|-----------------|
| **2xx** | Success | It worked | `200 OK`, `201 Created`, `204 No Content` |
| **3xx** | Redirect | Look elsewhere | `301 Moved Permanently`, `304 Not Modified` |
| **4xx** | Client error | *You* made a mistake | `400 Bad Request`, `404 Not Found`, `422 Unprocessable Entity` |
| **5xx** | Server error | *The server* broke | `500 Internal Server Error`, `503 Service Unavailable` |

As a data engineer you will see `404` (resource missing), `422` (FastAPI's "your JSON failed validation"), and `500` (an unhandled exception in your code) constantly. Learn to read them.

### JSON: The Wire Format
**JSON (JavaScript Object Notation)** is how structured data travels over HTTP. It looks almost exactly like a Python dict:

```json
{
  "item_id": 5,
  "name": "Widget",
  "price": 9.99,
  "tags": ["hardware", "sale"],
  "in_stock": true
}
```

FastAPI does the JSON translation for you. When you `return` a Python dict or a Pydantic model, FastAPI **serializes** it to JSON automatically. You do **not** call `json.dumps()` yourself - returning a dict is enough. (You will see this mistake in older code; today we avoid it.)

### ASGI vs WSGI, and Where Uvicorn Fits
Older Python web frameworks (Flask, classic Django) speak **WSGI** (Web Server Gateway Interface). WSGI is *synchronous*: one request occupies a worker until it finishes. If that request is waiting on a slow database or a remote API, the worker sits idle.

FastAPI speaks **ASGI** (Asynchronous Server Gateway Interface). ASGI supports `async`/`await`, so one worker can start a slow query, set it aside, and serve other requests while it waits. For data-heavy workloads with lots of I/O, this is a big throughput win.

| | WSGI | ASGI |
|---|------|------|
| Model | Synchronous | Asynchronous-capable |
| Concurrency | One request per worker at a time | Many concurrent requests per worker |
| Frameworks | Flask, classic Django | FastAPI, Starlette |
| Good for | CPU-bound, simple apps | I/O-bound, high-concurrency APIs |

```
  Your code            The ASGI server           The network
  (FastAPI app)  <-->  (Uvicorn)          <-->   (HTTP clients)
   defines routes       runs the app,             browsers,
   and logic            handles the socket,       scripts,
                        speaks ASGI               other services
```

**FastAPI is the framework; Uvicorn is the server that runs it.** You write the app object; Uvicorn listens on a port, accepts connections, and calls your app. You need both installed.

## Code Example

### Install
```bash
pip install "fastapi>=0.135" "uvicorn>=0.42"
```

### `main.py` - your first API
```python
from fastapi import FastAPI

# 1. Create the application instance. This 'app' object is what Uvicorn runs.
app = FastAPI(
    title="First API",
    description="A smoke-test API to prove the server runs.",
    version="0.1.0",
)


# 2. Map a Python function to GET requests at the root path "/".
@app.get("/")
def read_root():
    # 3. Return a plain dict. FastAPI serializes it to JSON for us.
    #    No json.dumps() needed!
    return {"message": "Hello, Data Engineers"}


@app.get("/health")
def health_check():
    """A conventional endpoint monitors hit to confirm the app is alive."""
    return {"status": "ok", "version": "0.1.0"}
```

### Run it
```bash
uvicorn main:app --reload
```
- `main` -> the file `main.py`
- `app` -> the `app` variable inside it
- `--reload` -> restart automatically when you edit the file (development only)

Uvicorn prints something like `Uvicorn running on http://127.0.0.1:8000`.

### Try it
Open a browser or a second terminal:

```bash
# In a browser: http://127.0.0.1:8000/
# Or with curl:
curl http://127.0.0.1:8000/
# -> {"message":"Hello, Data Engineers"}

curl http://127.0.0.1:8000/health
# -> {"status":"ok","version":"0.1.0"}
```

Now visit **`http://127.0.0.1:8000/docs`** in your browser. FastAPI already built you an interactive documentation page for free. We cover that in note 104.

## Key Takeaways
- An API is a contract for exchanging data between programs over HTTP.
- A request has a **method**, **path**, **headers**, and (sometimes) a **body**; a response has a **status code**, **headers**, and a **body**.
- Methods map to CRUD: `GET`=read, `POST`=create, `PUT`/`PATCH`=update, `DELETE`=delete.
- Status codes: **2xx** success, **4xx** your fault, **5xx** server's fault.
- **JSON** is the wire format; FastAPI serializes returned dicts/models automatically - never call `json.dumps()` on your return value.
- **ASGI** enables async concurrency; **Uvicorn** is the ASGI server that runs your FastAPI `app`.

## Resources
- [FastAPI - First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [MDN - An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview)
- [MDN - HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
- [MDN - HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [Uvicorn documentation](https://www.uvicorn.org/)
- [What is JSON (json.org)](https://www.json.org/json-en.html)
