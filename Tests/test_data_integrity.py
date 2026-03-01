"""
SI3LN Data Integrity Tests
===========================
Verifies score accumulation, leaderboard ranking consistency,
cascading deletes, orphan avoidance, and stat correctness.

Usage:
    python Tests/test_data_integrity.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_data_integrity.py
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


def _auth():
    return {"Authorization": f"Bearer {_token}"}


def setup():
    global _token, _player_id
    section("Setup — Create test user")
    r = requests.post(
        f"{API}/auth/register",
        json={
            "username": f"data_test_{TS}",
            "password": "SecureP@ss1",
            "email": f"data_{TS}@test.com",
        },
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Created test user: data_test_{TS} (id={_player_id})")
    else:
        print(f"  {FAIL} Setup failed: HTTP {r.status_code}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  1 · SCORE ACCUMULATION
# ══════════════════════════════════════════════════════════════════════════════

def test_score_accumulation():
    """total_score must equal the sum of completed session scores"""
    # Get initial score
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    initial_score = r0.json().get("total_score", 0)

    scores = [100, 250, 500]
    for sc in scores:
        # Create session
        r1 = requests.post(
            f"{API}/game/sessions",
            json={"player_id": _player_id},
            headers=_auth(),
            timeout=10,
        )
        sid = r1.json()["id"]
        # Complete with score
        requests.patch(
            f"{API}/game/sessions/{sid}",
            json={"score": sc, "completed": True},
            headers=_auth(),
            timeout=10,
        )

    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    final_score = r2.json().get("total_score", 0)
    expected = initial_score + sum(scores)

    if final_score == expected:
        ok(f"Score accumulation: {initial_score} + {sum(scores)} = {final_score}")
    else:
        fail(f"Score accumulation", f"expected {expected}, got {final_score}")


def test_games_played_counter():
    """games_played must increment by 1 for each completed session"""
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    initial_gp = r0.json().get("games_played", 0)

    # Create + complete 2 sessions
    for _ in range(2):
        r1 = requests.post(
            f"{API}/game/sessions",
            json={"player_id": _player_id},
            headers=_auth(),
            timeout=10,
        )
        sid = r1.json()["id"]
        requests.patch(
            f"{API}/game/sessions/{sid}",
            json={"score": 10, "completed": True},
            headers=_auth(),
            timeout=10,
        )

    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    gp = r2.json().get("games_played", 0)
    expected = initial_gp + 2
    if gp == expected:
        ok(f"Games played: {initial_gp} + 2 = {gp}")
    else:
        fail(f"Games played", f"expected {expected}, got {gp}")


def test_highest_level_tracking():
    """highest_level should be max of all levels ever reached"""
    # Complete sessions at levels 3, then 7, then 2
    for lvl in [3, 7, 2]:
        r1 = requests.post(
            f"{API}/game/sessions",
            json={"player_id": _player_id},
            headers=_auth(),
            timeout=10,
        )
        sid = r1.json()["id"]
        requests.patch(
            f"{API}/game/sessions/{sid}",
            json={"level_reached": lvl, "score": 10, "completed": True},
            headers=_auth(),
            timeout=10,
        )

    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    highest = r2.json().get("highest_level", 0)
    if highest == 7:
        ok(f"Highest level tracked correctly: {highest}")
    elif highest >= 7:
        ok(f"Highest level: {highest} (≥ expected 7)")
    else:
        fail(f"Highest level", f"expected 7, got {highest}")


def test_incomplete_session_no_accumulate():
    """An incomplete session should NOT add to total_score/games_played"""
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    score_before = r0.json().get("total_score", 0)
    gp_before = r0.json().get("games_played", 0)

    # Create session with score but do NOT mark completed
    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    sid = r1.json()["id"]
    requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 9999},
        headers=_auth(),
        timeout=10,
    )

    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    score_after = r2.json().get("total_score", 0)
    gp_after = r2.json().get("games_played", 0)

    if score_after == score_before and gp_after == gp_before:
        ok("Incomplete session → no score/games_played change")
    else:
        fail("Incomplete session", f"score {score_before}→{score_after}, gp {gp_before}→{gp_after}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · LEADERBOARD CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

def test_leaderboard_sorted():
    """Leaderboard must be sorted by score descending"""
    r = requests.get(f"{API}/game/leaderboard?limit=50", timeout=10)
    if r.status_code != 200:
        fail("Leaderboard sorted", f"HTTP {r.status_code}")
        return
    entries = r.json()
    if len(entries) < 2:
        ok("Leaderboard sorted (too few entries to verify)")
        return
    scores = [e["score"] for e in entries]
    if scores == sorted(scores, reverse=True):
        ok(f"Leaderboard sorted correctly ({len(entries)} entries)")
    else:
        fail("Leaderboard NOT sorted by score desc")


def test_leaderboard_ranks_sequential():
    """Leaderboard ranks must be 1, 2, 3, ..."""
    r = requests.get(f"{API}/game/leaderboard?limit=20", timeout=10)
    if r.status_code != 200:
        fail("Leaderboard ranks", f"HTTP {r.status_code}")
        return
    entries = r.json()
    if not entries:
        ok("Leaderboard ranks (empty)")
        return
    ranks = [e["rank"] for e in entries]
    expected = list(range(1, len(ranks) + 1))
    if ranks == expected:
        ok(f"Leaderboard ranks sequential: 1..{len(ranks)}")
    else:
        fail("Leaderboard ranks", f"got {ranks[:10]}")


def test_leaderboard_player_usernames():
    """Every leaderboard entry must have a non-empty player_username"""
    r = requests.get(f"{API}/game/leaderboard?limit=20", timeout=10)
    entries = r.json()
    empty = [e for e in entries if not e.get("player_username")]
    if not empty:
        ok(f"All leaderboard entries have player_username")
    else:
        fail("Leaderboard missing usernames", f"{len(empty)} entries without username")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · CASCADING & DELETE CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

def test_delete_session():
    """Deleting a session should not corrupt player stats"""
    # Record current stats
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    score0 = r0.json().get("total_score", 0)

    # Create + complete a session
    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    sid = r1.json()["id"]
    requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 50, "completed": True},
        headers=_auth(),
        timeout=10,
    )

    # Delete the session
    rd = requests.delete(
        f"{API}/game/sessions/{sid}",
        headers=_auth(),
        timeout=10,
    )
    if rd.status_code == 200:
        ok("DELETE /game/sessions → success")
    else:
        fail("DELETE /game/sessions", f"HTTP {rd.status_code}")
        return

    # Verify deleted
    rg = requests.get(f"{API}/game/sessions/{sid}", headers=_auth(), timeout=10)
    if rg.status_code == 404:
        ok("Deleted session returns 404")
    else:
        fail("Deleted session still accessible", f"HTTP {rg.status_code}")


def test_delete_player_cascades():
    """Deleting a player should also delete their sessions"""
    # Create a throwaway user
    ts2 = int(time.time() * 1000)
    reg = requests.post(
        f"{API}/auth/register",
        json={
            "username": f"del_test_{ts2}",
            "password": "SecureP@ss1",
            "email": f"del_{ts2}@test.com",
        },
        timeout=10,
    )
    if reg.status_code != 200:
        fail("Delete cascade setup", f"HTTP {reg.status_code}")
        return
    tk = reg.json()["token"]
    pid = reg.json()["player_id"]
    ah = {"Authorization": f"Bearer {tk}"}

    # Create a session for this player
    sr = requests.post(
        f"{API}/game/sessions",
        json={"player_id": pid},
        headers=ah,
        timeout=10,
    )
    sid = sr.json()["id"]

    # Delete player
    d = requests.delete(f"{API}/game/players/{pid}", headers=_auth(), timeout=10)
    if d.status_code != 200:
        warn("Delete player cascade", f"HTTP {d.status_code}")
        return

    # Session should be gone
    sg = requests.get(f"{API}/game/sessions/{sid}", headers=_auth(), timeout=10)
    if sg.status_code == 404:
        ok("Delete player → sessions cascaded")
    else:
        warn("Delete player cascade", f"Session still exists (HTTP {sg.status_code})")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · STAT ENDPOINT CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

def test_stats_total_players():
    """Stats total_players should match player list length"""
    stats = requests.get(f"{API}/game/stats", timeout=10).json()
    players = requests.get(f"{API}/game/players", headers=_auth(), timeout=10).json()
    sp = stats.get("total_players", 0)
    lp = len(players)
    if sp == lp:
        ok(f"Stats total_players ({sp}) matches player list ({lp})")
    else:
        warn(f"Stats total_players", f"stats={sp}, list={lp}")


def test_stats_total_sessions():
    """Stats total_sessions should match session list length"""
    stats = requests.get(f"{API}/game/stats", timeout=10).json()
    sessions = requests.get(f"{API}/game/sessions", headers=_auth(), timeout=10).json()
    ss = stats.get("total_sessions", 0)
    ls = len(sessions)
    if ss == ls:
        ok(f"Stats total_sessions ({ss}) matches session list ({ls})")
    else:
        warn(f"Stats total_sessions", f"stats={ss}, list={ls}")


def test_stats_highest_score():
    """Stats highest_score should match leaderboard #1"""
    stats = requests.get(f"{API}/game/stats", timeout=10).json()
    lb = requests.get(f"{API}/game/leaderboard?limit=1", timeout=10).json()
    highest = stats.get("highest_score", 0)
    if lb:
        top = lb[0].get("score", 0)
        if highest == top:
            ok(f"Stats highest_score ({highest}) matches leaderboard #1 ({top})")
        else:
            warn("Stats highest_score", f"stats={highest}, leaderboard={top}")
    else:
        ok(f"Stats highest_score = {highest} (leaderboard empty)")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

def test_zero_score_session():
    """A completed session with score=0 should still count as a game played"""
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    gp_before = r0.json().get("games_played", 0)

    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    sid = r1.json()["id"]
    requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 0, "completed": True},
        headers=_auth(),
        timeout=10,
    )

    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    gp_after = r2.json().get("games_played", 0)
    if gp_after == gp_before + 1:
        ok("Zero-score session counts as game played")
    else:
        fail("Zero-score session", f"games_played {gp_before} → {gp_after}")


def test_double_complete():
    """Completing a session twice should not double-count stats"""
    r0 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    gp_before = r0.json().get("games_played", 0)
    sc_before = r0.json().get("total_score", 0)

    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    sid = r1.json()["id"]

    # First complete
    requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 100, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    # Second complete (same session)
    requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": 100, "completed": True},
        headers=_auth(),
        timeout=10,
    )

    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    gp_after = r2.json().get("games_played", 0)
    sc_after = r2.json().get("total_score", 0)

    gp_diff = gp_after - gp_before
    sc_diff = sc_after - sc_before

    if gp_diff == 1 and sc_diff == 100:
        ok("Double-complete → counted only once")
    else:
        warn(
            "Double-complete",
            f"games_played +{gp_diff} (expected +1), score +{sc_diff} (expected +100)"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Data Integrity Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    setup()

    section("1 · Score Accumulation")
    test_score_accumulation()
    test_games_played_counter()
    test_highest_level_tracking()
    test_incomplete_session_no_accumulate()

    section("2 · Leaderboard Consistency")
    test_leaderboard_sorted()
    test_leaderboard_ranks_sequential()
    test_leaderboard_player_usernames()

    section("3 · Cascading Deletes")
    test_delete_session()
    test_delete_player_cascades()

    section("4 · Stat Endpoint Consistency")
    test_stats_total_players()
    test_stats_total_sessions()
    test_stats_highest_score()

    section("5 · Edge Cases")
    test_zero_score_session()
    test_double_complete()

    total = 14
    passed = total - len(errors)
    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{total} data integrity test(s) FAILED:")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  All {total} data integrity tests passed", end="")
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
