# Consuming APIs with a Python HTTP Client

## Learning Objectives
- Make GET and POST requests from Python with `httpx`.
- Send query parameters, headers, and JSON bodies.
- Read a JSON response and check its status code.
- Fail fast with `raise_for_status()` and always set **timeouts**.
- Handle network and HTTP errors gracefully.
- Understand when to reach for the sync client vs the async client.

## Why This Matters
So far you have built APIs that *serve* data. The other half of a data engineer's day is *consuming* data: pulling from a vendor's REST API, a partner feed, an internal microservice, or a public dataset. Almost every ingestion pipeline starts with an HTTP call to somebody else's API. Doing that call *robustly* - with timeouts, error handling, and status checks - is the difference between a pipeline that runs unattended for months and one that hangs forever or silently ingests garbage at 3 a.m.

We use **`httpx`**, the modern Python HTTP client. It has the same friendly API as the older, hugely popular **`requests`** library, plus first-class timeouts, HTTP/2, and an async client. If you have seen `requests` code, `httpx` will look almost identical - most snippets work by changing `requests` to `httpx`.

## Concept Explanation

### Install
```bash
pip install "httpx>=0.28"
```

### The Simplest Request
`httpx.get(url)` returns a `Response` object. From it you read the status code and the body.

```python
import httpx

response = httpx.get("https://httpbin.org/get")

print(response.status_code)   # 200
print(response.json())        # parsed JSON as a Python dict
print(response.text)          # raw body as a string
```

Key `Response` attributes and methods:

| Access | Returns | Use for |
|--------|---------|---------|
| `response.status_code` | `int` | Did it work? (`200`, `404`, ...) |
| `response.json()` | dict / list | Parsed JSON body (the usual case) |
| `response.text` | `str` | Raw body (non-JSON, or debugging) |
| `response.headers` | mapping | Response metadata |
| `response.raise_for_status()` | `None` or raises | Turn a 4xx/5xx into an exception |

### Query Parameters
Do not hand-build query strings. Pass a `params` dict and `httpx` encodes it correctly (spaces, special characters, and all).

```python
response = httpx.get(
    "https://httpbin.org/get",
    params={"q": "data engineering", "limit": 5},
)
# Actual URL sent: https://httpbin.org/get?q=data+engineering&limit=5
```

### Headers
Pass a `headers` dict. Common ones: `Accept` (what format you want back) and, for authenticated APIs, `Authorization`.

```python
response = httpx.get(
    "https://api.github.com/repos/encode/httpx",
    headers={"Accept": "application/vnd.github+json"},
)
```

### Sending JSON with POST
Pass a Python dict as `json=...`. `httpx` serializes it and sets `Content-Type: application/json` for you. (Use `data=...` only for old-style form encoding.)

```python
response = httpx.post(
    "https://httpbin.org/post",
    json={"name": "Widget", "price": 9.99},
)
print(response.json()["json"])   # httpbin echoes back what it received
```

### Timeouts: Never Optional
By default a hung server can make your request wait *forever*, freezing your pipeline. **Always** set a timeout. `httpx` actually defaults to a 5-second timeout, but be explicit - and raise it for slow endpoints.

```python
# 10 seconds total; raises httpx.TimeoutException if exceeded
response = httpx.get("https://httpbin.org/delay/2", timeout=10.0)
```

### `raise_for_status()`: Fail Fast on Bad Status
A `404` or `500` is still a "successful" network round-trip, so `httpx` does **not** raise on its own. Call `raise_for_status()` to convert any 4xx/5xx into an `httpx.HTTPStatusError` you can catch.

```python
response = httpx.get("https://httpbin.org/status/404")
response.raise_for_status()   # raises httpx.HTTPStatusError for 404
```

### Error Handling: The Two Failure Modes
Two distinct things can go wrong, and they raise different exceptions:

| Failure | Example | Exception (base) |
|---------|---------|------------------|
| **Transport** - never reached / timed out | DNS fails, connection refused, timeout | `httpx.RequestError` |
| **HTTP status** - reached, but bad code | `404`, `429`, `500` | `httpx.HTTPStatusError` |

Both inherit from `httpx.HTTPError`, so catch that for a general net. A robust fetch looks like this:

```python
import httpx

def fetch(url: str) -> dict | None:
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"Bad status {exc.response.status_code} from {url}")
    except httpx.RequestError as exc:
        print(f"Could not reach {url}: {exc}")
    return None
```

### Reuse Connections with a `Client`
Calling `httpx.get(...)` opens and closes a fresh connection each time. When you make many calls to the same host (the common pipeline case), use a `Client` as a context manager. It reuses the connection (faster) and lets you set shared config - base URL, headers, timeout - once.

```python
with httpx.Client(
    base_url="https://api.github.com",
    headers={"Accept": "application/vnd.github+json"},
    timeout=10.0,
) as client:
    repo = client.get("/repos/encode/httpx").json()
    issues = client.get("/repos/encode/httpx/issues", params={"per_page": 5}).json()
```

### Sync vs Async
`httpx` offers both a synchronous `Client` and an asynchronous `AsyncClient`.

| | `httpx.Client` (sync) | `httpx.AsyncClient` (async) |
|---|---|---|
| Style | plain functions | `async def` + `await` |
| One request at a time? | Yes - blocks until done | No - many concurrent in-flight |
| Reach for it when | scripts, simple ETL, sequential calls | fetching hundreds of URLs concurrently, or inside an async FastAPI endpoint |

For most ingestion scripts the **sync client is the right default** - simpler to write and debug. Use the async client when you need to fan out many requests at once and the wall-clock time matters.

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Fire three requests concurrently, wait for all.
        urls = ["https://httpbin.org/get"] * 3
        results = await asyncio.gather(*(client.get(u) for u in urls))
        print([r.status_code for r in results])

asyncio.run(main())
```

## Code Example

A complete, runnable consumer that pulls data, handles errors, and prints a structured result:

```python
import httpx


def get_repo_summary(owner: str, name: str) -> dict | None:
    """Fetch a public GitHub repo and return a trimmed summary, or None on failure."""
    with httpx.Client(
        base_url="https://api.github.com",
        headers={"Accept": "application/vnd.github+json"},
        timeout=10.0,
    ) as client:
        try:
            resp = client.get(f"/repos/{owner}/{name}")
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            print(f"GitHub returned {exc.response.status_code} for {owner}/{name}")
            return None
        except httpx.RequestError as exc:
            print(f"Network error reaching GitHub: {exc}")
            return None

        data = resp.json()
        return {
            "full_name": data["full_name"],
            "stars": data["stargazers_count"],
            "language": data["language"],
            "open_issues": data["open_issues_count"],
        }


if __name__ == "__main__":
    summary = get_repo_summary("encode", "httpx")
    if summary:
        print(summary)
    # -> {'full_name': 'encode/httpx', 'stars': ..., 'language': 'Python', ...}
```

## Key Takeaways
- `httpx` is the modern Python HTTP client; its API mirrors the older `requests` library.
- Pass query params as `params={...}`, JSON bodies as `json={...}`; read results with `response.json()`.
- **Always set a `timeout`** so a slow server cannot hang your pipeline.
- `raise_for_status()` turns 4xx/5xx into exceptions; catch `httpx.HTTPStatusError` (bad status) and `httpx.RequestError` (couldn't connect) separately.
- Use a `Client` context manager to reuse connections and share config across many calls.
- Default to the **sync client**; use `AsyncClient` only when concurrent fan-out matters.

## Resources
- [httpx - QuickStart](https://www.python-httpx.org/quickstart/)
- [httpx - Clients](https://www.python-httpx.org/advanced/clients/)
- [httpx - Timeouts](https://www.python-httpx.org/advanced/timeouts/)
- [httpx - Exceptions](https://www.python-httpx.org/exceptions/)
- [httpx - Async support](https://www.python-httpx.org/async/)
- [httpbin - request/response testing service](https://httpbin.org/)
- [GitHub REST API docs](https://docs.github.com/en/rest)
- [requests library (for comparison)](https://requests.readthedocs.io/)
