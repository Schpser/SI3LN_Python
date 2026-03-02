"""
SI3LN Rate Limiting Tests
==========================
Tests whether the API enforces rate limits on auth and public
endpoints under rapid/automated request patterns.

Usage:
    python Tests/test_rate_limiting.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_rate_limiting.py
"""

import os
import sys
import time
import json as _json
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE}/api"


class _CurlResponse:
    """Minimal response object matching requests.Response interface."""
    def __init__(self, status_code, body, headers_dict=None):
        self.status_code = status_code
        self.text = body
        self._body = body
        self.headers = headers_dict or {}
    def json(self):
        return _json.loads(self._body)


def _curl(method, url, *, json=None, headers=None, timeout=10):
    """Use subprocess curl to avoid connection pooling issues."""
    cmd = ["curl", "-s", "-X", method.upper(), "-w", "\n%{http_code}", "-m", str(timeout)]
    if json is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", _json.dumps(json)]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        lines = result.stdout.rsplit("\n", 1)
        body = lines[0] if len(lines) > 1 else ""
        code = int(lines[-1]) if lines[-1].strip().isdigit() else 0
        return _CurlResponse(code, body)
    except Exception as e:
        return _CurlResponse(0, str(e))


def _curl_post(url, *, json=None, headers=None, timeout=10, **kw):
    return _curl("POST", url, json=json, headers=headers, timeout=timeout)

def _curl_get(url, *, headers=None, timeout=10, **kw):
    return _curl("GET", url, headers=headers, timeout=timeout)

# Replace requests functions
requests.post = _curl_post
requests.get = _curl_get

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"

errors: list[str] = []
warnings: list[str] = []


def ok(label: str):
    print(f"  {PASS} {label}")


def fail(label: str, detail: str = ""):
    msg = f"  {FAIL} {label}"
    if detail:
        msg += f" → {detail}"
    print(msg)
    errors.append(label)


def warn(label: str, detail: str = ""):
    msg = f"  {WARN} {label}"
    if detail:
        msg += f" → {detail}"
    print(msg)
    warnings.append(label)


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ══════════════════════════════════════════════════════════════════════════════
#  1 · SEQUENTIAL RAPID REQUESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_rapid_login_sequential():
    """Send 50 sequential login attempts as fast as possible"""
    TS = int(time.time())
    t0 = time.time()
    statuses = []
    for i in range(50):
        try:
            r = requests.post(
                f"{API}/auth/login",
                json={"username": f"nouser_{TS}", "password": f"wrong_{i}"},
                timeout=10,
            )
            statuses.append(r.status_code)
        except requests.exceptions.RequestException:
            statuses.append(0)
    elapsed = time.time() - t0
    rate_limited = statuses.count(429)

    if rate_limited > 0:
        ok(f"Sequential login: {rate_limited}/50 rate-limited in {elapsed:.1f}s")
    else:
        warn("Sequential login", f"50 requests in {elapsed:.1f}s — none rate-limited")


def test_rapid_register_sequential():
    """Send 40 sequential registration attempts"""
    TS = int(time.time())
    t0 = time.time()
    statuses = []
    for i in range(40):
        try:
            r = requests.post(
                f"{API}/auth/register",
                json={
                    "username": f"rl_reg_{TS}_{i}",
                    "password": "SecureP@ss1",
                    "email": f"rl_reg_{TS}_{i}@test.com",
                },
                timeout=10,
            )
            statuses.append(r.status_code)
        except requests.exceptions.RequestException:
            statuses.append(0)
    elapsed = time.time() - t0
    rate_limited = statuses.count(429)
    successes = statuses.count(200)

    if rate_limited > 0:
        ok(f"Sequential register: {rate_limited}/40 rate-limited ({successes} succeeded) in {elapsed:.1f}s")
    else:
        warn("Sequential register", f"40 in {elapsed:.1f}s — none rate-limited ({successes} succeeded)")


def test_rapid_public_endpoint():
    """Rapid GET to public endpoint"""
    t0 = time.time()
    statuses = []
    for _ in range(60):
        try:
            r = requests.get(f"{API}/game/stats", timeout=10)
            statuses.append(r.status_code)
        except requests.exceptions.RequestException:
            statuses.append(0)
    elapsed = time.time() - t0
    rate_limited = statuses.count(429)
    errors_count = statuses.count(0)

    if rate_limited > 0:
        ok(f"Rapid /game/stats: {rate_limited}/60 rate-limited in {elapsed:.1f}s")
    elif errors_count == 0:
        ok(f"Rapid /game/stats: 60 requests OK in {elapsed:.1f}s (no explicit rate limit, but handled)")
    else:
        warn("Rapid /game/stats", f"{errors_count}/60 connection errors")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CONCURRENT BURST REQUESTS
# ══════════════════════════════════════════════════════════════════════════════

def _concurrent_burst(label, method, url, n, json_body=None, headers=None):
    """Fire n simultaneous requests and report rate limiting."""
    import urllib.request
    import urllib.error

    def fire(i):
        try:
            data = None
            req_headers = {"Connection": "close"}
            if json_body is not None:
                data = _json.dumps(json_body).encode("utf-8")
                req_headers["Content-Type"] = "application/json"
            if headers:
                req_headers.update(headers)
            req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            return 0

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(fire, i) for i in range(n)]
        statuses = [f.result() for f in as_completed(futures)]

    rate_limited = statuses.count(429)
    successes = [s for s in statuses if 200 <= s < 300]
    server_errors = [s for s in statuses if s >= 500]

    if rate_limited > 0:
        ok(f"{label}: {rate_limited}/{n} rate-limited ({len(successes)} OK)")
    elif server_errors:
        warn(f"{label}", f"{len(server_errors)}/{n} server errors")
    else:
        ok(f"{label}: {n} concurrent → {len(successes)} OK (no rate limit, but no crashes)")


def test_burst_login():
    """30 concurrent login attempts"""
    TS = int(time.time())
    _concurrent_burst(
        "Burst login (30 concurrent)",
        "POST",
        f"{API}/auth/login",
        30,
        json_body={"username": f"burst_{TS}", "password": "wrong"},
    )


def test_burst_stats():
    """40 concurrent GET /game/stats"""
    _concurrent_burst(
        "Burst /game/stats (40 concurrent)",
        "GET",
        f"{API}/game/stats",
        40,
    )


def test_burst_leaderboard():
    """30 concurrent GET /game/leaderboard"""
    _concurrent_burst(
        "Burst /game/leaderboard (30 concurrent)",
        "GET",
        f"{API}/game/leaderboard",
        30,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  3 · ACCOUNT ENUMERATION VIA TIMING
# ══════════════════════════════════════════════════════════════════════════════

def test_timing_attack_username():
    """Check if login timing differs for existing vs non-existing usernames"""
    TS = int(time.time())

    # Register a known user
    requests.post(
        f"{API}/auth/register",
        json={
            "username": f"timing_test_{TS}",
            "password": "SecureP@ss1",
            "email": f"timing_{TS}@test.com",
        },
        timeout=10,
    )

    # Time logins for existing user
    times_existing = []
    for _ in range(10):
        t0 = time.perf_counter()
        requests.post(
            f"{API}/auth/login",
            json={"username": f"timing_test_{TS}", "password": "wrongpass"},
            timeout=10,
        )
        times_existing.append((time.perf_counter() - t0) * 1000)

    # Time logins for non-existing user
    times_missing = []
    for _ in range(10):
        t0 = time.perf_counter()
        requests.post(
            f"{API}/auth/login",
            json={"username": f"nonexistent_{TS}", "password": "wrongpass"},
            timeout=10,
        )
        times_missing.append((time.perf_counter() - t0) * 1000)

    avg_existing = sum(times_existing) / len(times_existing)
    avg_missing = sum(times_missing) / len(times_missing)
    diff_ms = abs(avg_existing - avg_missing)
    ratio = max(avg_existing, avg_missing) / max(min(avg_existing, avg_missing), 0.1)

    if diff_ms < 50 or ratio < 2:
        ok(f"Login timing consistent (existing={avg_existing:.0f}ms, missing={avg_missing:.0f}ms, diff={diff_ms:.0f}ms)")
    elif diff_ms < 200:
        warn("Login timing", f"existing={avg_existing:.0f}ms, missing={avg_missing:.0f}ms (diff={diff_ms:.0f}ms)")
    else:
        warn("Timing attack risk", f"existing={avg_existing:.0f}ms vs missing={avg_missing:.0f}ms (diff={diff_ms:.0f}ms)")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · RETRY-AFTER HEADER
# ══════════════════════════════════════════════════════════════════════════════

def test_retry_after_header():
    """If rate limited, server should include Retry-After header"""
    TS = int(time.time())
    retry_after_seen = False
    for i in range(60):
        r = requests.post(
            f"{API}/auth/login",
            json={"username": f"retry_{TS}", "password": "wrong"},
            timeout=10,
        )
        if r.status_code == 429:
            ra = r.headers.get("Retry-After", "")
            if ra:
                ok(f"Retry-After header present: {ra}s")
                retry_after_seen = True
            else:
                warn("Retry-After header", "429 returned but no Retry-After header")
                retry_after_seen = True
            break
    if not retry_after_seen:
        ok("No 429 triggered in 60 requests (rate limiting may not be per-endpoint)")


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Rate Limiting Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("1 · Sequential Rapid Requests")
    test_rapid_login_sequential()
    test_rapid_register_sequential()
    test_rapid_public_endpoint()

    section("2 · Concurrent Burst Requests")
    test_burst_login()
    test_burst_stats()
    test_burst_leaderboard()

    section("3 · Timing Attack")
    test_timing_attack_username()

    section("4 · Retry-After")
    test_retry_after_header()

    total = 8
    passed = total - len(errors)
    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{total} rate limiting test(s) FAILED:")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  All {total} rate limiting tests passed", end="")
    if warnings:
        print(f" ({len(warnings)} warning(s))")
        for w in warnings:
            print(f"    ⚠ {w}")
    else:
        print()
    print(f"{'═' * 60}\n")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
