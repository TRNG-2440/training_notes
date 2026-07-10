# Demo 102 - Consuming APIs with httpx

The "consume" half of Day 1. A single script (`consume.py`) that pulls data
from two **no-auth public APIs** and shows how to do it robustly:

- **GET** with query parameters (`params={...}`)
- **POST** with a JSON body (`json={...}`)
- reading responses with `.json()` and `.status_code`
- a reusable `httpx.Client` with a shared base URL, headers, and timeout
- `raise_for_status()` to fail fast on 4xx/5xx
- **timeouts** so a slow server can't hang the script
- catching the two failure modes: `HTTPStatusError` vs `RequestError`

APIs used (no API key required):
- `https://httpbin.org` - echoes your request back so you can see exactly what was sent
- `https://api.github.com` - a real REST API returning structured JSON

Pairs with **notes/105-consuming-apis-with-python-http-client.md**.

## Setup
```bash
cd 102-http-client-consume
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python consume.py
```
(Requires internet access.)

## What to observe
- **Query params**: httpbin echoes them back under `args`, and shows the final
  encoded URL - proof that `httpx` built the query string for you.
- **POST JSON**: httpbin echoes your body back under `json`, confirming
  `httpx` serialized the dict and set `Content-Type: application/json`.
- **Reusable Client**: two calls to GitHub share one connection and one set of
  headers/timeout - the pattern you'll use in real ingestion code.
- **Error handling**: the 404 case raises `HTTPStatusError` (server reached,
  bad status); the bad-hostname case raises `RequestError` (never connected).
  These are handled differently on purpose.
- **Timeout**: the last section asks for a 3-second delay but only allows 1
  second, so it raises `TimeoutException` - demonstrating why every real
  request needs a timeout.

## A note on flaky services
`httpbin.org` is a free, best-effort service and sometimes returns `503` or
times out. The script wraps the httpbin demos so one flaky endpoint doesn't
crash the whole run - it prints `(skipped: ...)` and moves on. That is itself
the Day 1 lesson: **assume third-party APIs will sometimes fail, and code for
it.** The GitHub calls are more reliable and should always succeed.

## Try changing it
- Point `demo_reusable_client()` at your own favourite public repo.
- Change the timeout in `demo_timeout()` to `5.0` and watch it succeed instead.
- Add a call to `https://httpbin.org/status/500` and confirm it also raises
  via `raise_for_status()`.

## Follow-Along Build Walkthrough

### Intro
We are building a single Python script, `consume.py`, that consumes two public
web APIs with the `httpx` library. The end goal: by the time we finish, we will
be comfortable making GET and POST requests, reading JSON responses, reusing a
connection, setting timeouts, and handling the ways a network call can fail -
the everyday skills of pulling data into an ingestion pipeline.

### Step-by-step assembly
Start from a completely empty folder. We will add one file at a time and grow
`consume.py` function by function, introducing each new idea only when we hit it.

#### Step 1 - Declare the dependency
The only third-party package we need is `httpx`, an HTTP client for Python.
Create `requirements.txt`:

```
httpx>=0.28
```

Then make an environment and install it:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Why a pinned floor (`>=0.28`)? So everyone in the room gets a version new enough
to have the API we rely on. `httpx` is the modern successor to `requests`; it
has the same friendly feel but also supports connection pooling and async, which
matters later.

#### Step 2 - Create the file and its docstring
Create `consume.py`. Start with a module docstring that states what the script
does and the two services it talks to, then import the one library we need:

```python
"""Demo 102 - Consuming public APIs with httpx.

Runs against two no-auth public services:
  - https://httpbin.org  -> echoes requests back so you can SEE what you sent
  - https://api.github.com -> a real REST API returning structured JSON

Demonstrates: GET with query params, POST with a JSON body, reading responses,
status checks with raise_for_status(), timeouts, a reusable Client, and
robust error handling for both transport and HTTP-status failures.

Run:
    python consume.py
"""

import httpx
```

The docstring is documentation, not code, but it earns its place: it names our
two test targets. `httpbin.org` echoes back whatever we send, which is perfect
for *seeing* that our request was built correctly. `api.github.com` is a real
REST API, so we also get a taste of a genuine JSON response. `import httpx` is
the only import - everything below is built on it.

#### Step 3 - A GET request with query parameters
Add the first demo function. This is the simplest possible call: a GET with a
query string.

```python
def demo_get_with_query_params() -> None:
    """GET with query parameters. httpbin echoes them back under 'args'."""
    print("\n=== GET with query params (httpbin) ===")
    resp = httpx.get(
        "https://httpbin.org/get",
        params={"q": "data engineering", "limit": 5},
        timeout=10.0,
    )
    resp.raise_for_status()
    data = resp.json()
    print("Status:", resp.status_code)
    print("Server saw args:", data["args"])
    print("Final URL:", data["url"])
```

Line by line, this is the core pattern the whole script repeats:

- `httpx.get(url, ...)` performs an HTTP GET and returns a `Response` object.
- `params={"q": ..., "limit": 5}` - we hand `httpx` a plain dict; it builds the
  `?q=data%20engineering&limit=5` query string for us, URL-encoding as needed.
  We never assemble the query string by hand.
- `timeout=10.0` - a ceiling in seconds. If the server hasn't responded in 10s,
  the call raises instead of hanging forever. Every real request needs one.
- `resp.raise_for_status()` - if the response was a 4xx or 5xx, this raises an
  exception. It is how we "fail fast" instead of silently processing an error
  page as if it were data.
- `resp.json()` - parses the JSON response body into a Python dict.
- `resp.status_code` is the numeric HTTP status (200 here). Because httpbin
  echoes what it received, `data["args"]` is our params reflected back, and
  `data["url"]` is the final encoded URL - visible proof `httpx` did the work.

This one function introduces GET, `params`, `timeout`, `raise_for_status()`,
`.json()`, and `.status_code` - the vocabulary reused everywhere below.

#### Step 4 - A POST with a JSON body
Now the write direction. Add:

```python
def demo_post_json() -> None:
    """POST a JSON body. httpbin echoes it back under 'json'."""
    print("\n=== POST with JSON body (httpbin) ===")
    payload = {"name": "Widget", "price": 9.99, "tags": ["hardware"]}
    resp = httpx.post("https://httpbin.org/post", json=payload, timeout=10.0)
    resp.raise_for_status()
    print("Status:", resp.status_code)
    print("Server received JSON:", resp.json()["json"])
```

The new idea is `json=payload`. We pass a Python dict and `httpx` does two
things automatically: it serializes the dict to a JSON string, and it sets the
`Content-Type: application/json` header. (Contrast with `params=`, which goes in
the URL; `json=` goes in the request *body*.) httpbin echoes the parsed body
back under the `"json"` key, so `resp.json()["json"]` shows exactly what the
server received. Same `raise_for_status()` and `timeout` discipline as before.

#### Step 5 - A reusable Client against a real API
So far each call was a one-off `httpx.get(...)`. When you make several calls to
the same service, open a `Client` once and reuse it. Add:

```python
def demo_reusable_client() -> None:
    """Use a Client to reuse the connection and share config across calls."""
    print("\n=== Reusable Client against GitHub ===")
    with httpx.Client(
        base_url="https://api.github.com",
        headers={"Accept": "application/vnd.github+json"},
        timeout=10.0,
    ) as client:
        repo = client.get("/repos/encode/httpx")
        repo.raise_for_status()
        data = repo.json()
        print(f"{data['full_name']}: "
              f"{data['stargazers_count']} stars, "
              f"language={data['language']}, "
              f"open_issues={data['open_issues_count']}")
```

What is new and why it matters:

- `httpx.Client(...)` creates a client that pools the underlying TCP/TLS
  connection, so repeated calls to the same host are faster.
- We use it in a `with` block so the connection is cleaned up automatically when
  we are done - the same reason you use `with open(...)` for files.
- `base_url=` lets us pass just the path, `client.get("/repos/encode/httpx")`,
  instead of the full URL each time.
- `headers={"Accept": "application/vnd.github+json"}` is sent on *every* call
  through this client - the GitHub-recommended header, set once, shared.
- `timeout=10.0` on the client is the default for all its requests, so we do not
  repeat it per call.

The response is GitHub's real JSON, and we pull specific fields
(`full_name`, `stargazers_count`, `language`, `open_issues_count`) out of the
dict. This is the pattern real ingestion code uses: configure a client once,
then fire many requests through it.

#### Step 6 - Handling the two ways a call fails
A request can fail in two fundamentally different ways, and they need different
handling. Add:

```python
def demo_error_handling() -> None:
    """Show the two failure modes: bad HTTP status vs. cannot connect."""
    print("\n=== Error handling ===")

    # 1) A reachable server that returns a bad status code (404).
    try:
        resp = httpx.get("https://httpbin.org/status/404", timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"HTTPStatusError: server returned {exc.response.status_code}")

    # 2) A host that cannot be reached at all (transport error).
    try:
        httpx.get("https://this-host-does-not-exist.example", timeout=5.0)
    except httpx.RequestError as exc:
        print(f"RequestError: could not reach host ({type(exc).__name__})")
```

The distinction is the lesson:

- `HTTPStatusError` - we *did* reach the server and got a response, but it was a
  bad status (here `/status/404` forces a 404). This only surfaces because we
  call `raise_for_status()`; from `exc.response` we can inspect what came back.
- `RequestError` - we never got a valid HTTP response at all: DNS failed, the
  host is down, the connection dropped. The hostname here does not resolve, so
  the request never completes.

Treat them differently in real code: a 404 might mean "skip this record," while
a connection error might mean "retry later." Note this function catches its own
errors internally, so unlike the others it is safe to call directly.

#### Step 7 - Timeouts in action
We have set `timeout=` everywhere; now let us prove what it does. Add:

```python
def demo_timeout() -> None:
    """A deliberately short timeout against a slow endpoint raises TimeoutException."""
    print("\n=== Timeout ===")
    try:
        # httpbin/delay/3 waits 3s; we only allow 1s.
        httpx.get("https://httpbin.org/delay/3", timeout=1.0)
    except httpx.TimeoutException:
        print("TimeoutException: request exceeded the 1.0s budget (as expected)")
```

`httpbin.org/delay/3` deliberately waits 3 seconds before replying, but we only
allow `timeout=1.0`. `httpx` gives up at 1 second and raises
`TimeoutException`. This is why a timeout is not optional: without it a slow or
hung server would freeze the entire script indefinitely.

#### Step 8 - A safety wrapper for flaky endpoints
The httpbin demos hit a free, best-effort service that occasionally returns 503
or times out. We do not want one flaky endpoint to abort the whole run. Add a
small helper:

```python
def _safe(fn) -> None:
    """Run a demo, but don't let one flaky public endpoint kill the whole run.

    httpbin.org is a free, best-effort service and occasionally returns 503 or
    times out. In real ingestion code you'd retry; here we just report and move
    on so the other demos still run. This is itself a lesson in consuming
    third-party APIs: assume they will sometimes fail.
    """
    try:
        fn()
    except httpx.HTTPError as exc:
        print(f"  (skipped: {type(exc).__name__}: {exc})")
```

`_safe` takes a function, runs it, and catches `httpx.HTTPError` - the base
class that both `HTTPStatusError`, `RequestError`, and `TimeoutException` inherit
from, so it covers any httpx failure. On failure it prints a `(skipped: ...)`
note and returns normally, letting the run continue. This is "graceful
degradation," and it is itself a real-world lesson: assume third-party APIs will
sometimes fail.

#### Step 9 - The entry point
Finally, wire everything together and make the file runnable:

```python
def main() -> None:
    _safe(demo_get_with_query_params)
    _safe(demo_post_json)
    _safe(demo_reusable_client)
    demo_error_handling()  # already handles its own errors internally
    _safe(demo_timeout)
    print("\nDone.")


if __name__ == "__main__":
    main()
```

`main()` calls each demo in order. The httpbin-dependent ones are wrapped in
`_safe` so a flaky endpoint just prints a skip note. `demo_error_handling()` is
called directly because it already catches its own errors internally (wrapping
it would be redundant). The `if __name__ == "__main__":` guard means `main()`
runs when we execute `python consume.py`, but not if the module is imported
elsewhere - standard Python practice.

### How it fits together
Execution starts at the bottom: the `__main__` guard calls `main()`. `main()`
then runs the five demos in sequence. Four of them (`demo_get_with_query_params`,
`demo_post_json`, `demo_reusable_client`, `demo_timeout`) are routed through
`_safe`, which shields the run from a flaky call; `demo_error_handling` runs
directly. Each demo builds a request with `httpx`, checks the result with
`raise_for_status()` where a good status is expected, and reads JSON with
`.json()`. The script finishes by printing `Done.`. The through-line is the same
request/check/read cycle repeated with slight variations - GET vs POST, one-off
call vs reusable Client, success path vs each failure path.

### Demo Notes (instructor)
- **Run it:** `python consume.py` (needs internet access and the venv from
  Step 1).
- **Expected output:** five sections separated by `=== ... ===` headers, then
  `Done.`. The GET section prints the echoed `args` and the final encoded URL;
  the POST section prints the received JSON; the GitHub section prints something
  like `encode/httpx: <N> stars, language=Python, open_issues=<N>`; the error
  section prints one `HTTPStatusError: server returned 404` line and one
  `RequestError: could not reach host (...)` line; the timeout section prints
  `TimeoutException: request exceeded the 1.0s budget (as expected)`.
- **Point out live:** in the GET output, show that `data["url"]` contains the
  encoded query string you never typed - `httpx` built it. In the POST output,
  contrast `params` (in URL) with `json` (in body). Emphasize that the GitHub
  numbers are live and will differ from run to run.
- **Common gotchas:** httpbin is free and flaky - if you see `(skipped: ...)`
  lines, that is the `_safe` wrapper working as designed, not a bug; just rerun.
  The GitHub calls are far more reliable. GitHub also rate-limits unauthenticated
  requests (60/hour per IP), so repeated live demos can hit a 403 - worth
  mentioning. The `demo_timeout` section takes ~1 second on purpose. If you are
  behind a corporate proxy, the "cannot reach host" case may look different.

### Discussion Topics
1. **API reliability:** we saw `_safe` swallow failures and move on. When is
   "skip and continue" the right call, and when do you actually need the run to
   stop and alert someone?
2. **Retries and backoff:** the comment in `_safe` says "in real ingestion code
   you'd retry." How would you add retries without hammering a struggling
   server? What is exponential backoff and why jitter?
3. **Sync vs async:** these calls run one after another. `httpx` also has an
   async client. When would consuming many APIs concurrently be worth the added
   complexity?
4. **Authentication:** both APIs here are no-auth. How would the code change for
   an API needing an API key or bearer token, and where should that secret live
   (never in the source)?
5. **Rate limits:** GitHub caps unauthenticated requests. How do you detect you
   have been rate-limited (status codes, headers like `Retry-After`) and respond
   politely?
6. **Timeouts:** we used a flat `timeout=10.0`. What are the risks of a timeout
   that is too short vs too long, and would you set different budgets for connect
   vs read?
