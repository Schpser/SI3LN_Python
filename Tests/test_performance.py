"""
SI3LN Performance Tests
=======================
Tests response-time thresholds and concurrent-request handling
for every key API endpoint.

Usage:
    python Tests/test_performance.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_performance.py
"""

import os
import sys
import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE}/api"

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"

errors: list[str] = []
warnings: list[str] = []

# Thresholds (milliseconds)
FAST = 300       # simple GET
MEDIUM = 800     # DB writes
SLOW = 2000      # file upload


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


def timed_get(url, **kw):
    start = time.perf_counter()
    r = requests.get(url, timeout=15, **kw)
    ms = (time.perf_counter() - start) * 1000
    return r, ms


def timed_post(url, **kw):
    start = time.perf_counter()
    r = requests.post(url, timeout=15, **kw)
    ms = (time.perf_counter() - start) * 1000
    return r, ms


# ── Setup ─────────────────────────────────────────────────────────────────────

TS = int(time.time())
_token: str = ""
_player_id: int | None = None


def _auth():
    return {"Authorization": f"Bearer {_token}"}


def setup():
    global _token, _player_id
    section("Setup — Create test user")
    r = requests.post(
        f"{API}/auth/register",
        json={
            "username": f"perf_test_{TS}",
            "password": "SecureP@ss1",
            "email": f"perf_{TS}@test.com",
        },
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Created test user: perf_test_{TS}")
    else:
        print(f"  {FAIL} Setup failed: HTTP {r.status_code}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  1 · SINGLE-REQUEST LATENCY
# ══════════════════════════════════════════════════════════════════════════════

def _latency_check(label: str, url: str, threshold: int, headers=None):
    """Run 5 requests and check median latency."""
    times = []
    for _ in range(5):
        r, ms = timed_get(url, headers=headers or {})
        if r.status_code in range(200, 300):
            times.append(ms)
    if not times:
        fail(label, "all requests failed")
        return
    med = statistics.median(times)
    p95 = sorted(times)[int(len(times) * 0.95)]
    if med <= threshold:
        ok(f"{label} — median {med:.0f}ms (p95 {p95:.0f}ms)")
    elif med <= threshold * 2:
        warn(f"{label}", f"median {med:.0f}ms > {threshold}ms threshold")
    else:
        fail(f"{label}", f"median {med:.0f}ms (threshold {threshold}ms)")


def test_stats_latency():
    _latency_check("GET /game/stats", f"{API}/game/stats", FAST)


def test_leaderboard_latency():
    _latency_check("GET /game/leaderboard", f"{API}/game/leaderboard", FAST)


def test_players_latency():
    _latency_check("GET /game/players", f"{API}/game/players", FAST, _auth())


def test_profile_latency():
    _latency_check("GET /game/profile/me", f"{API}/game/profile/me", FAST, _auth())


def test_sessions_latency():
    _latency_check("GET /game/sessions", f"{API}/game/sessions", MEDIUM, _auth())


def test_login_latency():
    """Login involves password hashing — may be slower"""
    times = []
    for _ in range(5):
        r, ms = timed_post(
            f"{API}/auth/login",
            json={"username": f"perf_test_{TS}", "password": "SecureP@ss1"},
        )
        if r.status_code == 200:
            times.append(ms)
    if not times:
        fail("Login latency", "all requests failed")
        return
    med = statistics.median(times)
    if med <= MEDIUM:
        ok(f"POST /auth/login — median {med:.0f}ms")
    else:
        warn("Login latency", f"median {med:.0f}ms > {MEDIUM}ms")


def test_create_session_latency():
    """Write operation latency"""
    times = []
    for _ in range(5):
        r, ms = timed_post(
            f"{API}/game/sessions",
            json={"player_id": _player_id},
            headers=_auth(),
        )
        if r.status_code == 200:
            times.append(ms)
    if not times:
        fail("Create session latency", "all requests failed")
        return
    med = statistics.median(times)
    if med <= MEDIUM:
        ok(f"POST /game/sessions — median {med:.0f}ms")
    else:
        warn("Create session latency", f"median {med:.0f}ms > {MEDIUM}ms")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CONCURRENT REQUEST HANDLING
# ══════════════════════════════════════════════════════════════════════════════

def _concurrent_test(label, url, n=20, headers=None):
    """Fire n concurrent GET requests and check for failures."""
    def fetch(i):
        try:
            r = requests.get(url, timeout=15, headers=headers or {})
            return r.status_code, (time.perf_counter() - t0) * 1000
        except Exception as e:
            return 0, str(e)

    t0 = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(fetch, i) for i in range(n)]
        for f in as_completed(futures):
            results.append(f.result())

    successes = [r for r in results if isinstance(r[1], float) and r[0] in range(200, 300)]
    failures = len(results) - len(successes)
    if successes:
        times = [r[1] for r in successes]
        avg_ms = statistics.mean(times)
        max_ms = max(times)
    else:
        avg_ms = max_ms = 0

    if failures == 0:
        ok(f"{label} — {n} concurrent → all OK (avg {avg_ms:.0f}ms, max {max_ms:.0f}ms)")
    elif failures <= n * 0.1:
        warn(f"{label}", f"{failures}/{n} failed (avg {avg_ms:.0f}ms)")
    else:
        fail(f"{label}", f"{failures}/{n} failed")


def test_concurrent_stats():
    _concurrent_test("Concurrent /game/stats", f"{API}/game/stats", n=20)


def test_concurrent_leaderboard():
    _concurrent_test("Concurrent /game/leaderboard", f"{API}/game/leaderboard", n=20)


def test_concurrent_auth_endpoint():
    _concurrent_test("Concurrent /game/players", f"{API}/game/players", n=15, headers=_auth())


def test_concurrent_profile():
    _concurrent_test("Concurrent /game/profile/me", f"{API}/game/profile/me", n=15, headers=_auth())


# ══════════════════════════════════════════════════════════════════════════════
#  3 · LOAD / THROUGHPUT
# ══════════════════════════════════════════════════════════════════════════════

def test_throughput_public():
    """How many requests per second can the public stats endpoint handle?"""
    n = 50
    t0 = time.perf_counter()
    success = 0
    for _ in range(n):
        try:
            r = requests.get(f"{API}/game/stats", timeout=10)
            if r.status_code == 200:
                success += 1
        except Exception:
            pass
    elapsed = time.perf_counter() - t0
    rps = success / elapsed if elapsed > 0 else 0
    if rps >= 20:
        ok(f"Throughput /game/stats — {rps:.1f} req/s ({success}/{n} in {elapsed:.1f}s)")
    elif rps >= 5:
        warn(f"Throughput /game/stats", f"{rps:.1f} req/s (low)")
    else:
        fail(f"Throughput /game/stats", f"{rps:.1f} req/s")


def test_throughput_auth():
    """Authenticated endpoint throughput"""
    n = 30
    t0 = time.perf_counter()
    success = 0
    for _ in range(n):
        try:
            r = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
            if r.status_code == 200:
                success += 1
        except Exception:
            pass
    elapsed = time.perf_counter() - t0
    rps = success / elapsed if elapsed > 0 else 0
    if rps >= 10:
        ok(f"Throughput /game/profile/me — {rps:.1f} req/s ({success}/{n} in {elapsed:.1f}s)")
    elif rps >= 3:
        warn(f"Throughput auth endpoint", f"{rps:.1f} req/s (low)")
    else:
        fail(f"Throughput auth endpoint", f"{rps:.1f} req/s")


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Performance Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    setup()

    section("1 · Single-Request Latency")
    test_stats_latency()
    test_leaderboard_latency()
    test_players_latency()
    test_profile_latency()
    test_sessions_latency()
    test_login_latency()
    test_create_session_latency()

    section("2 · Concurrent Requests")
    test_concurrent_stats()
    test_concurrent_leaderboard()
    test_concurrent_auth_endpoint()
    test_concurrent_profile()

    section("3 · Throughput")
    test_throughput_public()
    test_throughput_auth()

    total = 13
    passed = total - len(errors)
    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{total} performance test(s) FAILED:")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  All {total} performance tests passed", end="")
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
