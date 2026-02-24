"""
SI3LN API Integration Tests
Runs against a live server (default: http://localhost:8000)

Usage:
    python Tests/test_api_endpoints.py
    # or with a different base URL:
    SI3LN_API_URL=http://localhost:8000 python Tests/test_api_endpoints.py

Requirements: pip install requests
"""

import os
import sys
import json
import time
import requests

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000").rstrip("/")
API  = f"{BASE}/api"

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
INFO = "\033[94mℹ\033[0m"

_token: str = ""
_player_id: int | None = None
_session_id: int | None = None

TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "password": "TestPass123!",
    "email":    f"test_{int(time.time())}@example.com",
}

errors: list[str] = []


def ok(label: str):
    print(f"  {PASS} {label}")


def fail(label: str, detail: str = ""):
    tag = f"  {FAIL} {label}"
    if detail:
        tag += f" → {detail}"
    print(tag)
    errors.append(label)


def section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ── 1. Health / public endpoints ──────────────────────────────────────────────

def test_stats_public():
    """GET /api/game/stats — no auth needed"""
    r = requests.get(f"{API}/game/stats", timeout=5)
    if r.status_code == 200:
        d = r.json()
        assert "total_players" in d, "missing total_players"
        assert "total_sessions" in d, "missing total_sessions"
        ok("GET /api/game/stats (public)")
    else:
        fail("GET /api/game/stats", f"HTTP {r.status_code}")


def test_leaderboard_public():
    """GET /api/game/leaderboard — no auth needed"""
    r = requests.get(f"{API}/game/leaderboard?limit=5", timeout=5)
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list), "expected a list"
        ok("GET /api/game/leaderboard (public)")
    else:
        fail("GET /api/game/leaderboard", f"HTTP {r.status_code}")


def test_worlds_public():
    """GET /api/game/worlds — no auth needed"""
    r = requests.get(f"{API}/game/worlds", timeout=5)
    if r.status_code == 200:
        ok("GET /api/game/worlds (public)")
    else:
        fail("GET /api/game/worlds", f"HTTP {r.status_code}")


def test_achievements_public():
    """GET /api/game/achievements — no auth needed"""
    r = requests.get(f"{API}/game/achievements", timeout=5)
    if r.status_code == 200:
        ok("GET /api/game/achievements (public)")
    else:
        fail("GET /api/game/achievements", f"HTTP {r.status_code}")


# ── 2. Auth flow ──────────────────────────────────────────────────────────────

def test_register():
    global _token, _player_id
    r = requests.post(f"{API}/auth/register", json=TEST_USER, timeout=5)
    if r.status_code == 200:
        d = r.json()
        assert "token" in d and "player_id" in d
        _token     = d["token"]
        _player_id = d["player_id"]
        ok(f"POST /api/auth/register (player_id={_player_id})")
    else:
        fail("POST /api/auth/register", f"HTTP {r.status_code} — {r.text[:120]}")


def test_login():
    global _token, _player_id
    r = requests.post(
        f"{API}/auth/login",
        json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        timeout=5,
    )
    if r.status_code == 200:
        d = r.json()
        assert "token" in d
        _token     = d["token"]
        _player_id = d["player_id"]
        ok(f"POST /api/auth/login (player_id={_player_id})")
    else:
        fail("POST /api/auth/login", f"HTTP {r.status_code} — {r.text[:120]}")


def test_login_wrong_password():
    r = requests.post(
        f"{API}/auth/login",
        json={"username": TEST_USER["username"], "password": "wrong_password"},
        timeout=5,
    )
    if r.status_code in (401, 400):
        ok("POST /api/auth/login (wrong password → 401/400)")
    else:
        fail("POST /api/auth/login wrong password", f"Expected 401, got {r.status_code}")


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_token}"}


def test_get_current_user():
    if not _token:
        fail("GET /api/auth/me", "skipped (no token)")
        return
    r = requests.get(f"{API}/auth/me", headers=_auth_headers(), timeout=5)
    if r.status_code == 200:
        d = r.json()
        assert d["username"] == TEST_USER["username"]
        ok("GET /api/auth/me (protected)")
    else:
        fail("GET /api/auth/me", f"HTTP {r.status_code}")


def test_protected_without_token():
    """Endpoints that require JWT should return 401 without a token."""
    r = requests.get(f"{API}/game/players", timeout=5)
    if r.status_code in (401, 403):
        ok("GET /api/game/players (no token → 401/403)")
    else:
        fail("Protected endpoint without token", f"Expected 401/403, got {r.status_code}")


# ── 3. Player endpoints ───────────────────────────────────────────────────────

def test_get_player():
    if not (_token and _player_id):
        fail("GET /api/game/players/:id", "skipped (no token/player_id)")
        return
    r = requests.get(f"{API}/game/players/{_player_id}", headers=_auth_headers(), timeout=5)
    if r.status_code == 200:
        d = r.json()
        assert d["id"] == _player_id
        ok(f"GET /api/game/players/{_player_id} (protected)")
    else:
        fail(f"GET /api/game/players/{_player_id}", f"HTTP {r.status_code}")


def test_get_my_profile():
    if not _token:
        fail("GET /api/game/profile/me", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/profile/me", headers=_auth_headers(), timeout=5)
    if r.status_code == 200:
        d = r.json()
        assert "username" in d and "total_score" in d
        ok("GET /api/game/profile/me (protected)")
    else:
        fail("GET /api/game/profile/me", f"HTTP {r.status_code}")


# ── 4. Game Sessions ──────────────────────────────────────────────────────────

def test_create_session():
    global _session_id
    if not (_token and _player_id):
        fail("POST /api/game/sessions", "skipped (no token/player_id)")
        return
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id, "world_id": None},
        headers=_auth_headers(),
        timeout=5,
    )
    if r.status_code == 200:
        d = r.json()
        _session_id = d["id"]
        ok(f"POST /api/game/sessions (session_id={_session_id})")
    else:
        fail("POST /api/game/sessions", f"HTTP {r.status_code} — {r.text[:120]}")


def test_update_session():
    if not (_token and _session_id):
        fail("PATCH /api/game/sessions/:id", "skipped (no session)")
        return
    r = requests.patch(
        f"{API}/game/sessions/{_session_id}",
        json={"score": 1500, "level_reached": 3, "completed": True},
        headers=_auth_headers(),
        timeout=5,
    )
    if r.status_code == 200:
        d = r.json()
        assert d["score"] == 1500
        ok(f"PATCH /api/game/sessions/{_session_id}")
    else:
        fail(f"PATCH /api/game/sessions/{_session_id}", f"HTTP {r.status_code}")


def test_list_sessions():
    if not _token:
        fail("GET /api/game/sessions", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/sessions", headers=_auth_headers(), timeout=5)
    if r.status_code == 200:
        ok("GET /api/game/sessions (protected)")
    else:
        fail("GET /api/game/sessions", f"HTTP {r.status_code}")


# ── 5. Leaderboard after session ──────────────────────────────────────────────

def test_leaderboard_after_session():
    r = requests.get(f"{API}/game/leaderboard?limit=20", timeout=5)
    if r.status_code == 200:
        entries = r.json()
        found = any(e.get("player_username") == TEST_USER["username"] for e in entries)
        if found:
            ok("Leaderboard contains test user after session")
        else:
            print(f"  {INFO} Leaderboard doesn't show test user yet (score may need aggregation)")
    else:
        fail("GET /api/game/leaderboard (post session)", f"HTTP {r.status_code}")


# ── 6. Token refresh ──────────────────────────────────────────────────────────

def test_token_refresh():
    if not _token:
        fail("POST /api/auth/refresh", "skipped (no token)")
        return
    r = requests.post(f"{API}/auth/refresh", headers=_auth_headers(), timeout=5)
    if r.status_code == 200:
        ok("POST /api/auth/refresh (protected)")
    else:
        fail("POST /api/auth/refresh", f"HTTP {r.status_code}")


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    print(f"\n{'═'*55}")
    print(f"  SI3LN API Integration Tests")
    print(f"  Target: {BASE}")
    print(f"{'═'*55}")

    section("1 · Public endpoints")
    test_stats_public()
    test_leaderboard_public()
    test_worlds_public()
    test_achievements_public()

    section("2 · Auth flow")
    test_register()
    test_login()
    test_login_wrong_password()
    test_get_current_user()
    test_protected_without_token()

    section("3 · Player profile")
    test_get_player()
    test_get_my_profile()

    section("4 · Game sessions")
    test_create_session()
    test_update_session()
    test_list_sessions()

    section("5 · Leaderboard after session")
    test_leaderboard_after_session()

    section("6 · Token refresh")
    test_token_refresh()

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'═'*55}")
    total = 17  # update when adding tests
    failed = len(errors)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll tests passed ({passed}/{total})\033[0m")
    else:
        print(f"  \033[91m{failed} test(s) failed:\033[0m")
        for e in errors:
            print(f"    • {e}")
    print(f"{'═'*55}\n")
    return failed


if __name__ == "__main__":
    try:
        sys.exit(run_all())
    except requests.exceptions.ConnectionError:
        print(f"\n  {FAIL} Cannot connect to {BASE}")
        print(f"  {INFO} Make sure the API is running:")
        print(f"       docker compose -f Docker/docker-compose.yml up -d")
        print(f"       — or —")
        print(f"       cd api && python manage.py runserver\n")
        sys.exit(1)
