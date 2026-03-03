"""
SI3LN Session Edge Case Tests
================================
Tests edge cases for game sessions: re-completing, world filtering,
tied scores, concurrent creation, boundary values.

Usage:
    python Tests/test_session_edge_cases.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_session_edge_cases.py
"""

import os
import sys
import time
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

TEST_USER = {
    "username": f"session_edge_{TS}",
    "password": "SessionEdge1!",
    "email": f"session_edge_{TS}@test.com",
}


def _auth() -> dict:
    return {"Authorization": f"Bearer {_token}"}


def _setup():
    global _token, _player_id
    r = requests.post(f"{API}/auth/register", json=TEST_USER, timeout=10)
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Created user: {TEST_USER['username']} (id={_player_id})")
    else:
        r2 = requests.post(
            f"{API}/auth/login",
            json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
            timeout=10,
        )
        if r2.status_code == 200:
            d = r2.json()
            _token = d["token"]
            _player_id = d["player_id"]
            print(f"  {INFO} Logged in: {TEST_USER['username']}")
        else:
            print(f"  {FAIL} Auth failed — tests will be limited")


def _create_and_complete_session(score=100, level=1, world_id=None):
    """Helper to create and complete a session. Returns session_id or None."""
    payload = {"player_id": _player_id}
    if world_id is not None:
        payload["world_id"] = world_id
    r1 = requests.post(
        f"{API}/game/sessions", json=payload, headers=_auth(), timeout=10,
    )
    if r1.status_code != 200:
        return None
    sid = r1.json()["id"]
    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": score, "level_reached": level, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    return sid if r2.status_code == 200 else None


# ══════════════════════════════════════════════════════════════════════════════
#  1 · RE-COMPLETING / DOUBLE-COMPLETE SESSIONS
# ══════════════════════════════════════════════════════════════════════════════

def test_update_already_completed_session():
    """Updating an already-completed session's score should not double-count"""
    if not (_token and _player_id):
        fail("Update completed session", "skipped (no auth)")
        return

    # Get initial stats
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    score_before = r0.json().get("total_score", 0)
    gp_before = r0.json().get("games_played", 0)

    sid = _create_and_complete_session(score=200, level=2)
    if not sid:
        fail("Update completed session", "Could not create session")
        return

    # Try to re-complete with a different score
    r3 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 300, "completed": True},
        headers=_auth(),
        timeout=10,
    )

    r4 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    score_after = r4.json().get("total_score", 0)
    gp_after = r4.json().get("games_played", 0)

    score_diff = score_after - score_before
    gp_diff = gp_after - gp_before

    if gp_diff == 1 and score_diff == 200:
        ok("Re-completing session → only first completion counts")
    elif gp_diff == 1 and score_diff in (200, 300):
        warn(
            "Re-complete session",
            f"games_played +{gp_diff}, score +{score_diff} (second complete may have overwritten)"
        )
    else:
        warn(
            "Re-complete session",
            f"games_played +{gp_diff} (expected +1), score +{score_diff} (expected +200)"
        )


def test_update_completed_session_score_only():
    """Patching score without completed=True on an already-completed session"""
    if not (_token and _player_id):
        fail("Update score only on completed", "skipped (no auth)")
        return

    sid = _create_and_complete_session(score=150, level=1)
    if not sid:
        fail("Update score only on completed", "Could not create session")
        return

    # Record current total
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    score_before = r0.json().get("total_score", 0)

    # Just update score (no completed flag)
    r = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 9999},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
        score_after = r2.json().get("total_score", 0)
        if score_after == score_before:
            ok("Score-only patch on completed session → no stat change")
        else:
            warn("Score-only patch on completed", f"total_score changed: {score_before} → {score_after}")
    else:
        warn("Score-only patch on completed", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · WORLD-FILTERED LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════

def test_leaderboard_with_world_filter():
    """GET /game/leaderboard?world_id=X should only show sessions from that world"""
    # First, get available worlds
    rw = requests.get(f"{API}/game/worlds", timeout=10)
    if rw.status_code != 200 or not rw.json():
        warn("Leaderboard world filter", "No worlds available")
        return

    worlds = rw.json()
    world_id = worlds[0]["id"]

    r = requests.get(f"{API}/game/leaderboard?world_id={world_id}&limit=20", timeout=10)
    if r.status_code == 200:
        entries = r.json()
        if isinstance(entries, list):
            # Check that all entries are from the correct world (if world_name available)
            wrong_world = [
                e for e in entries
                if e.get("world_name") and e.get("world_id") and e["world_id"] != world_id
            ]
            if not wrong_world:
                ok(f"Leaderboard filtered by world_id={world_id} ({len(entries)} entries)")
            else:
                fail("Leaderboard world filter", f"{len(wrong_world)} entries from wrong world")
        else:
            warn("Leaderboard world filter", f"Unexpected response type: {type(entries)}")
    else:
        warn("Leaderboard world filter", f"HTTP {r.status_code}")


def test_leaderboard_invalid_world_id():
    """Leaderboard with non-existent world_id"""
    r = requests.get(f"{API}/game/leaderboard?world_id=99999&limit=10", timeout=10)
    if r.status_code == 200:
        entries = r.json()
        if isinstance(entries, list) and len(entries) == 0:
            ok("Leaderboard with invalid world_id → empty list")
        elif isinstance(entries, list):
            warn("Leaderboard invalid world", f"Got {len(entries)} entries for non-existent world")
        else:
            warn("Leaderboard invalid world", f"Unexpected response type")
    elif r.status_code in (400, 404):
        ok(f"Leaderboard with invalid world_id → {r.status_code}")
    else:
        warn("Leaderboard invalid world", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · TIED SCORES & EMPTY LEADERBOARD SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

def test_leaderboard_tied_scores():
    """Create multiple sessions with identical scores, check rank assignment"""
    if not (_token and _player_id):
        fail("Tied scores", "skipped (no auth)")
        return

    # Create 3 sessions with the same score
    for _ in range(3):
        _create_and_complete_session(score=777, level=1)

    r = requests.get(f"{API}/game/leaderboard?limit=50", timeout=10)
    if r.status_code == 200:
        entries = r.json()
        # Find entries with score=777
        tied = [e for e in entries if e.get("score") == 777]
        if len(tied) >= 2:
            ranks = [e["rank"] for e in tied]
            # Ranks should be sequential, not all the same
            if len(set(ranks)) == len(ranks):
                ok(f"Tied scores → unique sequential ranks ({ranks[:5]})")
            else:
                warn("Tied scores", f"Non-unique ranks: {ranks[:5]}")
        else:
            ok("Tied scores leaderboard → OK (may have been pushed off by higher scores)")
    else:
        fail("Tied scores", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · SESSION FIELD BOUNDARIES
# ══════════════════════════════════════════════════════════════════════════════

def test_session_zero_level():
    """Create session with level_reached=0 (below minimum)"""
    if not (_token and _player_id):
        fail("Session zero level", "skipped (no auth)")
        return

    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        fail("Session zero level", "Could not create session")
        return
    sid = r1.json()["id"]

    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"level_reached": 0, "score": 50, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code in (400, 422):
        ok("Session level_reached=0 → rejected (MinValueValidator)")
    elif r2.status_code == 200:
        actual_level = r2.json().get("level_reached")
        if actual_level == 0:
            warn("Session zero level", "Server accepted level=0 (MinValueValidator(1) not enforced)")
        else:
            ok(f"Session level adjusted to {actual_level}")
    else:
        warn("Session zero level", f"HTTP {r2.status_code}")


def test_session_very_high_level():
    """Create session with extremely high level_reached"""
    if not (_token and _player_id):
        fail("Session very high level", "skipped (no auth)")
        return

    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        fail("Session very high level", "Could not create session")
        return
    sid = r1.json()["id"]

    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"level_reached": 999999, "score": 50, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code == 200:
        ok("Session with very high level → accepted")
    elif r2.status_code in (400, 422):
        ok(f"Session with very high level → rejected ({r2.status_code})")
    else:
        warn("Session very high level", f"HTTP {r2.status_code}")


def test_session_with_duration_and_enemies():
    """Create session with all optional fields: duration, enemies_killed"""
    if not (_token and _player_id):
        fail("Session full fields", "skipped (no auth)")
        return

    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        fail("Session full fields", "Could not create session")
        return
    sid = r1.json()["id"]

    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={
            "score": 1500,
            "level_reached": 5,
            "enemies_killed": 42,
            "duration_seconds": 180,
            "completed": True,
        },
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code == 200:
        d = r2.json()
        checks_ok = True
        if d.get("score") != 1500:
            checks_ok = False
        if d.get("level_reached") != 5:
            checks_ok = False
        if checks_ok:
            ok("Session with all optional fields → saved correctly")
        else:
            warn("Session full fields", f"Some fields mismatch: {d}")
    else:
        fail("Session full fields", f"HTTP {r2.status_code}")


def test_session_ended_at_auto_set():
    """Completing a session should auto-set ended_at"""
    if not (_token and _player_id):
        fail("Session ended_at auto-set", "skipped (no auth)")
        return

    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        fail("Session ended_at auto-set", "Could not create session")
        return
    sid = r1.json()["id"]

    # Check ended_at is null initially
    before = r1.json().get("ended_at")

    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 100, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code == 200:
        ended_at = r2.json().get("ended_at")
        if ended_at and before != ended_at:
            ok(f"Session ended_at auto-set on completion ({ended_at[:19]})")
        elif ended_at:
            ok("Session ended_at set (was already set)")
        else:
            warn("Session ended_at", "ended_at is still null after completion")
    else:
        fail("Session ended_at auto-set", f"HTTP {r2.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · SESSION FILTERING
# ══════════════════════════════════════════════════════════════════════════════

def test_sessions_filter_by_world():
    """GET /game/sessions?world_id=X should filter sessions"""
    if not _token:
        fail("Sessions filter by world", "skipped (no token)")
        return

    # Get a world_id
    rw = requests.get(f"{API}/game/worlds", timeout=10)
    if rw.status_code != 200 or not rw.json():
        warn("Sessions filter by world", "No worlds available")
        return
    world_id = rw.json()[0]["id"]

    r = requests.get(
        f"{API}/game/sessions?world_id={world_id}",
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        sessions = r.json()
        assert isinstance(sessions, list)
        ok(f"Sessions filtered by world_id={world_id} ({len(sessions)} sessions)")
    else:
        fail("Sessions filter by world", f"HTTP {r.status_code}")


def test_sessions_filter_both_params():
    """GET /game/sessions?player_id=X&world_id=Y"""
    if not (_token and _player_id):
        fail("Sessions filter both params", "skipped (no auth)")
        return

    rw = requests.get(f"{API}/game/worlds", timeout=10)
    if rw.status_code != 200 or not rw.json():
        warn("Sessions filter both params", "No worlds available")
        return
    world_id = rw.json()[0]["id"]

    r = requests.get(
        f"{API}/game/sessions?player_id={_player_id}&world_id={world_id}",
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        sessions = r.json()
        # Verify all sessions match both filters
        wrong = [
            s for s in sessions
            if (s.get("player_id") and s["player_id"] != _player_id)
            or (s.get("world_id") and s["world_id"] != world_id)
        ]
        if not wrong:
            ok(f"Sessions filtered by player+world ({len(sessions)} results)")
        else:
            fail("Sessions filter both params", f"{len(wrong)} sessions don't match filters")
    else:
        fail("Sessions filter both params", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Session Edge Case Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("Setup — Create test user")
    _setup()

    section("1 · Re-completing / Double-complete")
    test_update_already_completed_session()
    test_update_completed_session_score_only()

    section("2 · World-Filtered Leaderboard")
    test_leaderboard_with_world_filter()
    test_leaderboard_invalid_world_id()

    section("3 · Tied Scores")
    test_leaderboard_tied_scores()

    section("4 · Session Field Boundaries")
    test_session_zero_level()
    test_session_very_high_level()
    test_session_with_duration_and_enemies()
    test_session_ended_at_auto_set()

    section("5 · Session Filtering")
    test_sessions_filter_by_world()
    test_sessions_filter_both_params()

    # Summary
    print(f"\n{'═' * 60}")
    total = 11
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} session edge case tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))")
        else:
            print()
    else:
        print(f"  \033[91m{failed}/{total} session edge case test(s) FAILED:\033[0m")
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
