"""
SI3LN API Endpoints Tests — Full Coverage
==========================================
Tests every API endpoint: public, protected, edge cases, error handling.

Usage:
    python Tests/test_api_full.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_api_full.py
"""

import os
import sys
import time
import json
import requests

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE}/api"

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


# ── Shared state ──────────────────────────────────────────────────────────────

TS = int(time.time())
_token: str = ""
_player_id: int | None = None
_session_id: int | None = None
_second_session_id: int | None = None

TEST_USER = {
    "username": f"api_test_{TS}",
    "password": "ApiTestPass123!",
    "email": f"api_{TS}@test.com",
}


def _auth() -> dict:
    return {"Authorization": f"Bearer {_token}"}


def _setup_auth():
    """Register + login to get a valid token for tests."""
    global _token, _player_id
    r = requests.post(f"{API}/auth/register", json=TEST_USER, timeout=10)
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Test user registered: {TEST_USER['username']} (id={_player_id})")
    else:
        # Maybe user already exists — try login
        r2 = requests.post(
            f"{API}/auth/login",
            json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
            timeout=10,
        )
        if r2.status_code == 200:
            d = r2.json()
            _token = d["token"]
            _player_id = d["player_id"]
            print(f"  {INFO} Logged in as existing user: {TEST_USER['username']}")
        else:
            print(f"  {FAIL} Cannot authenticate — tests will be limited")


# ══════════════════════════════════════════════════════════════════════════════
#  1 · PUBLIC ENDPOINTS (no auth required)
# ══════════════════════════════════════════════════════════════════════════════

def test_stats():
    """GET /api/game/stats"""
    r = requests.get(f"{API}/game/stats", timeout=10)
    if r.status_code == 200:
        d = r.json()
        required = ["total_players", "total_sessions", "total_score", "average_score", "highest_score"]
        missing = [k for k in required if k not in d]
        if missing:
            fail("GET /game/stats", f"Missing fields: {missing}")
        else:
            ok(f"GET /game/stats (players={d['total_players']}, sessions={d['total_sessions']})")
    else:
        fail("GET /game/stats", f"HTTP {r.status_code}")


def test_leaderboard():
    """GET /api/game/leaderboard"""
    r = requests.get(f"{API}/game/leaderboard?limit=10", timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list), "Expected a list"
        if len(d) > 0:
            entry = d[0]
            required = ["rank", "player_username", "score"]
            missing = [k for k in required if k not in entry]
            if missing:
                fail("GET /game/leaderboard", f"Entry missing: {missing}")
            else:
                ok(f"GET /game/leaderboard ({len(d)} entries)")
        else:
            ok("GET /game/leaderboard (empty — no games yet)")
    else:
        fail("GET /game/leaderboard", f"HTTP {r.status_code}")


def test_leaderboard_limit():
    """GET /api/game/leaderboard with various limits"""
    for limit in [1, 5, 50]:
        r = requests.get(f"{API}/game/leaderboard?limit={limit}", timeout=10)
        if r.status_code == 200:
            d = r.json()
            assert len(d) <= limit, f"Got {len(d)} entries, expected <= {limit}"
        else:
            fail(f"GET /game/leaderboard?limit={limit}", f"HTTP {r.status_code}")
            return
    ok("GET /game/leaderboard (limit parameter works)")


def test_worlds():
    """GET /api/game/worlds"""
    r = requests.get(f"{API}/game/worlds", timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list), "Expected a list"
        ok(f"GET /game/worlds ({len(d)} worlds)")
    else:
        fail("GET /game/worlds", f"HTTP {r.status_code}")


def test_achievements():
    """GET /api/game/achievements"""
    r = requests.get(f"{API}/game/achievements", timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list), "Expected a list"
        ok(f"GET /game/achievements ({len(d)} achievements)")
    else:
        fail("GET /game/achievements", f"HTTP {r.status_code}")


def test_nonexistent_endpoint():
    """GET /api/game/doesnotexist should return 404"""
    r = requests.get(f"{API}/game/doesnotexist", timeout=10)
    if r.status_code in (404, 405):
        ok("GET /game/doesnotexist → 404/405")
    else:
        warn("Nonexistent endpoint", f"Expected 404, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · PLAYER ENDPOINTS (protected)
# ══════════════════════════════════════════════════════════════════════════════

def test_list_players():
    """GET /api/game/players (protected)"""
    if not _token:
        fail("GET /game/players", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/players", headers=_auth(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list), "Expected a list"
        ok(f"GET /game/players ({len(d)} players)")
    else:
        fail("GET /game/players", f"HTTP {r.status_code}")


def test_list_players_no_auth():
    """GET /api/game/players without token"""
    r = requests.get(f"{API}/game/players", timeout=10)
    if r.status_code in (401, 403):
        ok("GET /game/players (no auth → 401/403)")
    else:
        fail("GET /game/players no auth", f"Expected 401/403, got {r.status_code}")


def test_get_player():
    """GET /api/game/players/:id"""
    if not (_token and _player_id):
        fail("GET /game/players/:id", "skipped (no auth)")
        return
    r = requests.get(f"{API}/game/players/{_player_id}", headers=_auth(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert d["id"] == _player_id, "Player ID mismatch"
        assert d["username"] == TEST_USER["username"], "Username mismatch"
        ok(f"GET /game/players/{_player_id}")
    else:
        fail(f"GET /game/players/{_player_id}", f"HTTP {r.status_code}")


def test_get_player_not_found():
    """GET /api/game/players/99999 (non-existent)"""
    if not _token:
        fail("GET /game/players/99999", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/players/99999", headers=_auth(), timeout=10)
    if r.status_code in (404,):
        ok("GET /game/players/99999 → 404")
    else:
        fail("GET /game/players/99999", f"Expected 404, got {r.status_code}")


def test_update_player():
    """PUT /api/game/players/:id"""
    if not (_token and _player_id):
        fail("PUT /game/players/:id", "skipped (no auth)")
        return
    r = requests.put(
        f"{API}/game/players/{_player_id}",
        json={"username": TEST_USER["username"], "email": TEST_USER["email"]},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        ok(f"PUT /game/players/{_player_id}")
    else:
        fail(f"PUT /game/players/{_player_id}", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · PROFILE ENDPOINTS (protected)
# ══════════════════════════════════════════════════════════════════════════════

def test_get_my_profile():
    """GET /api/game/profile/me"""
    if not _token:
        fail("GET /game/profile/me", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        required = ["id", "username", "total_score", "games_played", "highest_level", "bio", "bg_color"]
        missing = [k for k in required if k not in d]
        if missing:
            fail("GET /game/profile/me", f"Missing fields: {missing}")
        else:
            ok("GET /game/profile/me")
    else:
        fail("GET /game/profile/me", f"HTTP {r.status_code}")


def test_update_my_profile_bio():
    """PATCH /api/game/profile/me — update bio"""
    if not _token:
        fail("PATCH /game/profile/me (bio)", "skipped (no token)")
        return
    new_bio = f"Test bio from API test at {TS}"
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": new_bio},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        if d.get("bio") == new_bio:
            ok("PATCH /game/profile/me (bio updated)")
        else:
            fail("PATCH /game/profile/me (bio)", "Bio not updated in response")
    else:
        fail("PATCH /game/profile/me (bio)", f"HTTP {r.status_code}")


def test_update_my_profile_bg_color():
    """PATCH /api/game/profile/me — update bg_color"""
    if not _token:
        fail("PATCH /game/profile/me (bg_color)", "skipped (no token)")
        return
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bg_color": "#1a2b3c"},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        if d.get("bg_color") == "#1a2b3c":
            ok("PATCH /game/profile/me (bg_color updated)")
        else:
            warn("PATCH /game/profile/me (bg_color)", "Color not reflected in response")
    else:
        fail("PATCH /game/profile/me (bg_color)", f"HTTP {r.status_code}")


def test_update_my_profile_show_scores():
    """PATCH /api/game/profile/me — toggle show_scores"""
    if not _token:
        fail("PATCH /game/profile/me (show_scores)", "skipped (no token)")
        return
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"show_scores": False},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        if d.get("show_scores") is False:
            ok("PATCH /game/profile/me (show_scores=false)")
        else:
            warn("PATCH /game/profile/me (show_scores)", "Field not toggled in response")
    else:
        fail("PATCH /game/profile/me (show_scores)", f"HTTP {r.status_code}")

    # Toggle back
    requests.patch(
        f"{API}/game/profile/me",
        json={"show_scores": True},
        headers=_auth(),
        timeout=10,
    )


def test_profile_no_auth():
    """GET /api/game/profile/me without token"""
    r = requests.get(f"{API}/game/profile/me", timeout=10)
    if r.status_code in (401, 403):
        ok("GET /game/profile/me (no auth → 401/403)")
    else:
        fail("GET /game/profile/me no auth", f"Expected 401/403, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · GAME SESSION ENDPOINTS (protected)
# ══════════════════════════════════════════════════════════════════════════════

def test_create_session():
    """POST /api/game/sessions"""
    global _session_id
    if not (_token and _player_id):
        fail("POST /game/sessions", "skipped (no auth)")
        return
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id, "world_id": None},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        _session_id = d["id"]
        assert d["player_id"] == _player_id or d.get("player", {}).get("id") == _player_id
        assert d["score"] == 0, "New session should have score=0"
        ok(f"POST /game/sessions (session_id={_session_id})")
    else:
        fail("POST /game/sessions", f"HTTP {r.status_code} — {r.text[:200]}")


def test_create_session_with_world():
    """POST /api/game/sessions with world_id"""
    global _second_session_id
    if not (_token and _player_id):
        fail("POST /game/sessions (with world)", "skipped (no auth)")
        return
    # Try to get a world ID first
    worlds_r = requests.get(f"{API}/game/worlds", timeout=10)
    world_id = None
    if worlds_r.status_code == 200:
        worlds = worlds_r.json()
        if worlds:
            world_id = worlds[0]["id"]

    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id, "world_id": world_id},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        _second_session_id = d["id"]
        ok(f"POST /game/sessions with world_id={world_id} (session={_second_session_id})")
    else:
        fail("POST /game/sessions with world", f"HTTP {r.status_code}")


def test_update_session():
    """PATCH /api/game/sessions/:id — end a session"""
    if not (_token and _session_id):
        fail("PATCH /game/sessions/:id", "skipped (no session)")
        return
    r = requests.patch(
        f"{API}/game/sessions/{_session_id}",
        json={"score": 2500, "level_reached": 5, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        assert d.get("score") == 2500, f"Score mismatch: {d.get('score')}"
        assert d.get("level_reached") == 5, f"Level mismatch: {d.get('level_reached')}"
        assert d.get("completed") is True, "Session not marked completed"
        ok(f"PATCH /game/sessions/{_session_id} (score=2500, level=5)")
    else:
        fail(f"PATCH /game/sessions/{_session_id}", f"HTTP {r.status_code}")


def test_update_session_partial():
    """PATCH /api/game/sessions/:id — partial update (just score)"""
    if not (_token and _second_session_id):
        fail("PATCH /game/sessions (partial)", "skipped (no second session)")
        return
    r = requests.patch(
        f"{API}/game/sessions/{_second_session_id}",
        json={"score": 800},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        assert d.get("score") == 800
        ok(f"PATCH /game/sessions/{_second_session_id} (partial score=800)")
    else:
        fail(f"PATCH /game/sessions/{_second_session_id} partial", f"HTTP {r.status_code}")


def test_get_session():
    """GET /api/game/sessions/:id"""
    if not (_token and _session_id):
        fail("GET /game/sessions/:id", "skipped (no session)")
        return
    r = requests.get(f"{API}/game/sessions/{_session_id}", headers=_auth(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert d["id"] == _session_id
        ok(f"GET /game/sessions/{_session_id}")
    else:
        fail(f"GET /game/sessions/{_session_id}", f"HTTP {r.status_code}")


def test_list_sessions():
    """GET /api/game/sessions"""
    if not _token:
        fail("GET /game/sessions", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/sessions", headers=_auth(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list)
        ok(f"GET /game/sessions ({len(d)} sessions)")
    else:
        fail("GET /game/sessions", f"HTTP {r.status_code}")


def test_list_sessions_by_player():
    """GET /api/game/sessions?player_id=X"""
    if not (_token and _player_id):
        fail("GET /game/sessions?player_id", "skipped (no auth)")
        return
    r = requests.get(
        f"{API}/game/sessions?player_id={_player_id}",
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list)
        ok(f"GET /game/sessions?player_id={_player_id} ({len(d)} sessions)")
    else:
        fail(f"GET /game/sessions?player_id={_player_id}", f"HTTP {r.status_code}")


def test_sessions_no_auth():
    """POST /api/game/sessions without token"""
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": 1},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("POST /game/sessions (no auth → 401/403)")
    else:
        fail("POST /game/sessions no auth", f"Expected 401/403, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · LEADERBOARD AFTER SESSIONS
# ══════════════════════════════════════════════════════════════════════════════

def test_leaderboard_after_sessions():
    """Check leaderboard contains our test user"""
    r = requests.get(f"{API}/game/leaderboard?limit=50", timeout=10)
    if r.status_code == 200:
        entries = r.json()
        found = any(e.get("player_username") == TEST_USER["username"] for e in entries)
        if found:
            ok("Leaderboard contains test user after session")
        else:
            warn("Leaderboard", "Test user not yet in leaderboard (may need score aggregation)")
    else:
        fail("GET /game/leaderboard (post session)", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  6 · ACHIEVEMENTS
# ══════════════════════════════════════════════════════════════════════════════

def test_player_achievements():
    """GET /api/game/players/:id/achievements"""
    if not (_token and _player_id):
        fail("GET /game/players/:id/achievements", "skipped (no auth)")
        return
    r = requests.get(
        f"{API}/game/players/{_player_id}/achievements",
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        assert isinstance(d, list)
        ok(f"GET /game/players/{_player_id}/achievements ({len(d)} achievements)")
    else:
        fail(f"GET /game/players/{_player_id}/achievements", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  7 · EDGE CASES & ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════

def test_invalid_player_id_type():
    """GET /api/game/players/abc (invalid ID)"""
    if not _token:
        fail("GET /game/players/abc", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/players/abc", headers=_auth(), timeout=10)
    if r.status_code in (400, 404, 422):
        ok("GET /game/players/abc → error (invalid ID type)")
    else:
        warn("GET /game/players/abc", f"Got {r.status_code}")


def test_create_session_invalid_player():
    """POST /api/game/sessions with non-existent player_id"""
    if not _token:
        fail("POST /game/sessions (invalid player)", "skipped (no token)")
        return
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": 999999},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 404, 422, 500):
        ok(f"POST /game/sessions (invalid player_id → {r.status_code})")
    else:
        warn("POST /game/sessions invalid player", f"Got {r.status_code}")


def test_large_score():
    """PATCH /game/sessions — very large score"""
    if not (_token and _second_session_id):
        fail("PATCH session large score", "skipped (no session)")
        return
    r = requests.patch(
        f"{API}/game/sessions/{_second_session_id}",
        json={"score": 999999999, "level_reached": 100, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        ok("PATCH session with large score → accepted")
    else:
        fail("PATCH session large score", f"HTTP {r.status_code}")


def test_negative_score():
    """Try to set a negative score"""
    if not _token:
        fail("Negative score test", "skipped (no token)")
        return
    # Create a new session
    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        warn("Negative score test", "Couldn't create session")
        return
    sid = r1.json()["id"]
    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": -100},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code in (400, 422):
        ok("Negative score → rejected by server")
    elif r2.status_code == 200:
        warn("Negative score", "Server accepted negative score (may want validation)")
    else:
        fail("Negative score", f"HTTP {r2.status_code}")


def test_cors_headers():
    """Check if CORS headers are present (for frontend compatibility)"""
    r = requests.options(
        f"{API}/game/stats",
        headers={"Origin": "http://localhost", "Access-Control-Request-Method": "GET"},
        timeout=10,
    )
    cors = r.headers.get("Access-Control-Allow-Origin", "")
    if cors:
        ok(f"CORS headers present (Allow-Origin: {cors})")
    else:
        warn("CORS headers", "Access-Control-Allow-Origin not set (may be handled by nginx)")


def test_content_type_json():
    """Verify API returns Content-Type: application/json"""
    r = requests.get(f"{API}/game/stats", timeout=10)
    ct = r.headers.get("Content-Type", "")
    if "application/json" in ct:
        ok("Content-Type: application/json")
    else:
        fail("Content-Type", f"Got: {ct}")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN API Full Endpoint Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("Setup — Authenticate test user")
    _setup_auth()

    section("1 · Public Endpoints")
    test_stats()
    test_leaderboard()
    test_leaderboard_limit()
    test_worlds()
    test_achievements()
    test_nonexistent_endpoint()

    section("2 · Player Endpoints (protected)")
    test_list_players()
    test_list_players_no_auth()
    test_get_player()
    test_get_player_not_found()
    test_update_player()

    section("3 · Profile Endpoints (protected)")
    test_get_my_profile()
    test_update_my_profile_bio()
    test_update_my_profile_bg_color()
    test_update_my_profile_show_scores()
    test_profile_no_auth()

    section("4 · Game Sessions (protected)")
    test_create_session()
    test_create_session_with_world()
    test_update_session()
    test_update_session_partial()
    test_get_session()
    test_list_sessions()
    test_list_sessions_by_player()
    test_sessions_no_auth()

    section("5 · Leaderboard After Sessions")
    test_leaderboard_after_sessions()

    section("6 · Achievements")
    test_player_achievements()

    section("7 · Edge Cases & Error Handling")
    test_invalid_player_id_type()
    test_create_session_invalid_player()
    test_large_score()
    test_negative_score()
    test_cors_headers()
    test_content_type_json()

    # Summary
    print(f"\n{'═' * 60}")
    total_tests = 30
    failed = len(errors)
    warned = len(warnings)
    passed = total_tests - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} API tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))", end="")
        print()
    else:
        print(f"  \033[91m{failed}/{total_tests} API test(s) FAILED:\033[0m")
        for e in errors:
            print(f"    • {e}")
        if warned:
            print(f"  \033[93m{warned} warning(s)\033[0m")
    print(f"{'═' * 60}\n")
    return failed


if __name__ == "__main__":
    try:
        sys.exit(run_all())
    except requests.exceptions.ConnectionError:
        print(f"\n  {FAIL} Cannot connect to {BASE}")
        print(f"  {INFO} Start the server first:\n"
              f"       docker compose -f Docker/docker-compose.yml up -d\n")
        sys.exit(1)
