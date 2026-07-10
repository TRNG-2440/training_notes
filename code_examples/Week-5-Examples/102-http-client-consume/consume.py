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


def demo_post_json() -> None:
    """POST a JSON body. httpbin echoes it back under 'json'."""
    print("\n=== POST with JSON body (httpbin) ===")
    payload = {"name": "Widget", "price": 9.99, "tags": ["hardware"]}
    resp = httpx.post("https://httpbin.org/post", json=payload, timeout=10.0)
    resp.raise_for_status()
    print("Status:", resp.status_code)
    print("Server received JSON:", resp.json()["json"])


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


def demo_timeout() -> None:
    """A deliberately short timeout against a slow endpoint raises TimeoutException."""
    print("\n=== Timeout ===")
    try:
        # httpbin/delay/3 waits 3s; we only allow 1s.
        httpx.get("https://httpbin.org/delay/3", timeout=1.0)
    except httpx.TimeoutException:
        print("TimeoutException: request exceeded the 1.0s budget (as expected)")


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


def main() -> None:
    _safe(demo_get_with_query_params)
    _safe(demo_post_json)
    _safe(demo_reusable_client)
    demo_error_handling()  # already handles its own errors internally
    _safe(demo_timeout)
    print("\nDone.")


if __name__ == "__main__":
    main()
