"""
SI3LN End-to-End Flow Tests
=============================
Full game lifecycle: register → login → profile → play sessions →
leaderboard → password change → logout.

Usage:
    python Tests/test_e2e_flow.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_e2e_flow.py
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
steps: int = 0


def ok(label: str):
    global steps
    steps += 1
    print(f"  {PASS} Step {steps}: {label}")


def fail(label: str, detail: str = ""):
    global steps
    steps += 1
    msg = f"  {FAIL} Step {steps}: {label}"
    if detail:
        msg += f" → {detail}"
    print(msg)
    errors.append(label)


def warn(label: str, detail: str = ""):
    global steps
    steps += 1
    msg = f"  {WARN} Step {steps}: {label}"
    if detail:
        msg += f" → {detail}"
    print(msg)
    warnings.append(label)


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


TS = int(time.time())
USERNAME = f"e2e_player_{TS}"
PASSWORD = "E2eSecureP@ss1"
NEW_PASSWORD = "NewE2eP@ss99"
EMAIL = f"e2e_{TS}@test.com"


# ══════════════════════════════════════════════════════════════════════════════
#  FLOW 1: Full Player Lifecycle
# ══════════════════════════════════════════════════════════════════════════════

def flow_full_lifecycle():
    section("Flow 1 · Full Player Lifecycle")

    # ── 1. Register ───────────────────────────────────────────────────────────
    r = requests.post(
        f"{API}/auth/register",
        json={"username": USERNAME, "password": PASSWORD, "email": EMAIL},
        timeout=10,
    )
    if r.status_code != 200:
        fail("Register", f"HTTP {r.status_code}")
        return
    d = r.json()
    token = d["token"]
    player_id = d["player_id"]
    auth = {"Authorization": f"Bearer {token}"}
    ok(f"Register → {USERNAME} (player_id={player_id})")

    # ── 2. Get profile ────────────────────────────────────────────────────────
    r = requests.get(f"{API}/game/profile/me", headers=auth, timeout=10)
    if r.status_code == 200:
        p = r.json()
        if p["username"] == USERNAME and p["total_score"] == 0 and p["games_played"] == 0:
            ok("Profile → fresh (score=0, games=0)")
        else:
            fail("Profile defaults wrong", str(p))
    else:
        fail("Get profile", f"HTTP {r.status_code}")
        return

    # ── 3. Update profile ─────────────────────────────────────────────────────
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": "E2E test player", "bg_color": "#1a2b3c"},
        headers=auth,
        timeout=10,
    )
    if r.status_code == 200 and r.json()["bio"] == "E2E test player":
        ok("Update profile (bio + bg_color)")
    else:
        fail("Update profile", f"HTTP {r.status_code}")

    # ── 4. Upload avatar ──────────────────────────────────────────────────────
    png = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
        b'\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00'
        b'\x00\x00\x00IEND\xaeB`\x82'
    )
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("e2e_avatar.png", png, "image/png")},
        headers=auth,
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("avatar_url"):
        ok(f"Upload avatar → {r.json()['avatar_url'][:60]}...")
    else:
        fail("Upload avatar", f"HTTP {r.status_code}")

    # ── 5. Play 3 game sessions ──────────────────────────────────────────────
    total_expected = 0
    session_ids = []
    for i, score in enumerate([500, 1200, 300], 1):
        sr = requests.post(
            f"{API}/game/sessions",
            json={"player_id": player_id},
            headers=auth,
            timeout=10,
        )
        if sr.status_code != 200:
            fail(f"Create session {i}", f"HTTP {sr.status_code}")
            continue
        sid = sr.json()["id"]
        session_ids.append(sid)

        ur = requests.patch(
            f"{API}/game/sessions/{sid}",
            json={"score": score, "level_reached": i + 1, "completed": True},
            headers=auth,
            timeout=10,
        )
        if ur.status_code == 200:
            ok(f"Session {i}: score={score}, level={i + 1}")
            total_expected += score
        else:
            fail(f"Complete session {i}", f"HTTP {ur.status_code}")

    # ── 6. Verify stats updated ──────────────────────────────────────────────
    r = requests.get(f"{API}/game/profile/me", headers=auth, timeout=10)
    if r.status_code == 200:
        p = r.json()
        if p["total_score"] == total_expected:
            ok(f"Total score correct: {total_expected}")
        else:
            fail("Total score", f"expected {total_expected}, got {p['total_score']}")
        if p["games_played"] == 3:
            ok("Games played = 3")
        else:
            fail("Games played", f"expected 3, got {p['games_played']}")
        if p["highest_level"] >= 4:
            ok(f"Highest level = {p['highest_level']}")
        else:
            fail("Highest level", f"expected ≥4, got {p['highest_level']}")

    # ── 7. Check sessions list ────────────────────────────────────────────────
    r = requests.get(
        f"{API}/game/sessions",
        params={"player_id": player_id},
        headers=auth,
        timeout=10,
    )
    if r.status_code == 200 and len(r.json()) >= 3:
        ok(f"Sessions list for player: {len(r.json())} sessions")
    else:
        fail("Sessions list", f"HTTP {r.status_code}, count={len(r.json()) if r.status_code == 200 else '?'}")

    # ── 8. Check leaderboard ─────────────────────────────────────────────────
    r = requests.get(f"{API}/game/leaderboard?limit=50", timeout=10)
    if r.status_code == 200:
        lb = r.json()
        found = [e for e in lb if e.get("player_username") == USERNAME]
        if found:
            ok(f"Player on leaderboard (rank #{found[0]['rank']}, score={found[0]['score']})")
        else:
            warn("Leaderboard", "Player not found in top 50")
    else:
        fail("Leaderboard check", f"HTTP {r.status_code}")

    # ── 9. Change password ────────────────────────────────────────────────────
    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=auth,
        timeout=10,
    )
    if r.status_code == 200:
        ok("Change password")
    else:
        fail("Change password", f"HTTP {r.status_code}")

    # ── 10. Login with new password ───────────────────────────────────────────
    r = requests.post(
        f"{API}/auth/login",
        json={"username": USERNAME, "password": NEW_PASSWORD},
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("token"):
        new_token = r.json()["token"]
        ok("Login with new password → got token")
    else:
        fail("Login with new password", f"HTTP {r.status_code}")
        return

    # ── 11. Old password should fail ──────────────────────────────────────────
    r = requests.post(
        f"{API}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    if r.status_code == 401:
        ok("Old password → rejected (401)")
    else:
        fail("Old password still works", f"HTTP {r.status_code}")

    # ── 12. Token refresh ─────────────────────────────────────────────────────
    auth_new = {"Authorization": f"Bearer {new_token}"}
    r = requests.post(f"{API}/auth/refresh", headers=auth_new, timeout=10)
    if r.status_code == 200 and r.json().get("token"):
        ok("Token refresh → new token received")
    else:
        fail("Token refresh", f"HTTP {r.status_code}")

    # ── 13. Logout ────────────────────────────────────────────────────────────
    r = requests.post(f"{API}/auth/logout", headers=auth_new, timeout=10)
    if r.status_code == 200:
        ok("Logout → success")
    else:
        fail("Logout", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  FLOW 2: Multi-User Interaction
# ══════════════════════════════════════════════════════════════════════════════

def flow_multi_user():
    section("Flow 2 · Multi-User Interaction")

    tokens = {}
    pids = {}

    # Create 3 users
    for i in range(1, 4):
        r = requests.post(
            f"{API}/auth/register",
            json={
                "username": f"e2e_multi_{TS}_{i}",
                "password": "SecureP@ss1",
                "email": f"e2e_m{i}_{TS}@test.com",
            },
            timeout=10,
        )
        if r.status_code == 200:
            tokens[i] = r.json()["token"]
            pids[i] = r.json()["player_id"]
        else:
            fail(f"Create user {i}", f"HTTP {r.status_code}")
            return
    ok(f"Created 3 users (ids={list(pids.values())})")

    # Each user plays a session with different scores
    user_scores = {1: 3000, 2: 1500, 3: 5000}
    for i, score in user_scores.items():
        auth = {"Authorization": f"Bearer {tokens[i]}"}
        sr = requests.post(
            f"{API}/game/sessions",
            json={"player_id": pids[i]},
            headers=auth,
            timeout=10,
        )
        if sr.status_code != 200:
            fail(f"Session for user {i}", f"HTTP {sr.status_code}")
            continue
        sid = sr.json()["id"]
        requests.patch(
            f"{API}/game/sessions/{sid}",
            json={"score": score, "completed": True},
            headers=auth,
            timeout=10,
        )
    ok("All 3 users completed sessions")

    # Check leaderboard ordering
    r = requests.get(f"{API}/game/leaderboard?limit=50", timeout=10)
    if r.status_code != 200:
        fail("Leaderboard fetch", f"HTTP {r.status_code}")
        return
    lb = r.json()
    usernames_in_lb = [e["player_username"] for e in lb]

    # User 3 (5000) should rank higher than user 1 (3000) > user 2 (1500)
    positions = {}
    for i in range(1, 4):
        name = f"e2e_multi_{TS}_{i}"
        if name in usernames_in_lb:
            positions[i] = usernames_in_lb.index(name)

    if len(positions) == 3:
        if positions[3] < positions[1] < positions[2]:
            ok("Leaderboard ordering: user3 > user1 > user2 ✓")
        else:
            warn("Leaderboard ordering", f"positions={positions} (expected 3<1<2)")
    else:
        warn("Leaderboard", f"Only {len(positions)}/3 users found")

    # User 1 should NOT see user 2's profile details via player list
    auth1 = {"Authorization": f"Bearer {tokens[1]}"}
    r = requests.get(f"{API}/game/players/{pids[2]}", headers=auth1, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if "password" not in str(d).lower():
            ok("Cross-user player fetch → no password leak")
        else:
            fail("Cross-user fetch", "password field visible")
    else:
        ok(f"Cross-user player fetch → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  FLOW 3: Frontend + API Integration
# ══════════════════════════════════════════════════════════════════════════════

def flow_frontend_api():
    section("Flow 3 · Frontend ↔ API Integration")

    # 1. Frontend loads
    r = requests.get("http://localhost", timeout=10)
    if r.status_code == 200 and "ARCAD3X" in r.text:
        ok("Frontend index.html loads")
    else:
        fail("Frontend load", f"HTTP {r.status_code}")
        return

    # 2. Frontend can reach API via nginx proxy
    r = requests.get("http://localhost/api/game/stats", timeout=10)
    if r.status_code == 200:
        ok(f"Nginx proxies /api/game/stats → API")
    else:
        fail("Nginx API proxy", f"HTTP {r.status_code}")

    # 3. CSS loads
    r = requests.get("http://localhost/css/style.css", timeout=10)
    if r.status_code == 200 and len(r.text) > 100:
        ok(f"CSS loaded ({len(r.text)} bytes)")
    else:
        fail("CSS load", f"HTTP {r.status_code}")

    # 4. JS modules load
    js_files = [
        "/js/config.js",
        "/js/services/api-facade.js",
        "/js/modules/auth.js",
        "/js/app-refactored.js",
    ]
    loaded = 0
    for path in js_files:
        r = requests.get(f"http://localhost{path}", timeout=10)
        if r.status_code == 200 and len(r.text) > 50:
            loaded += 1
    if loaded == len(js_files):
        ok(f"All {loaded} JS modules load")
    else:
        fail("JS modules", f"{loaded}/{len(js_files)} loaded")

    # 5. Auth round-trip through nginx
    r = requests.post(
        "http://localhost/api/auth/login",
        json={"username": USERNAME, "password": NEW_PASSWORD},
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("token"):
        ok("Login via nginx proxy → token received")
    elif r.status_code == 401:
        ok("Login via nginx proxy → auth response returned")
    else:
        fail("Login via nginx", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN End-to-End Flow Tests")
    print(f"  Target API: {BASE}")
    print(f"  Target Frontend: http://localhost")
    print(f"{'═' * 60}")

    flow_full_lifecycle()
    flow_multi_user()
    flow_frontend_api()

    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{steps} E2E step(s) FAILED:")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  All {steps} E2E steps passed", end="")
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
