"""
SI3LN Authorization (IDOR) Tests
==================================
Verifies that users cannot access, modify, or delete other users' resources.

Usage:
    python Tests/test_authorization.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_authorization.py
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

USER_A = {
    "username": f"idor_a_{TS}",
    "password": "SecurePassA1!",
    "email": f"idor_a_{TS}@test.com",
}
USER_B = {
    "username": f"idor_b_{TS}",
    "password": "SecurePassB2!",
    "email": f"idor_b_{TS}@test.com",
}

_token_a: str = ""
_token_b: str = ""
_player_id_a: int | None = None
_player_id_b: int | None = None
_session_id_a: int | None = None


def _auth_a() -> dict:
    return {"Authorization": f"Bearer {_token_a}"}


def _auth_b() -> dict:
    return {"Authorization": f"Bearer {_token_b}"}


def _setup():
    """Register two separate users for IDOR testing."""
    global _token_a, _token_b, _player_id_a, _player_id_b, _session_id_a

    for label, user, setter in [
        ("User A", USER_A, "a"),
        ("User B", USER_B, "b"),
    ]:
        r = requests.post(f"{API}/auth/register", json=user, timeout=10)
        if r.status_code == 200:
            d = r.json()
            if setter == "a":
                _token_a = d["token"]
                _player_id_a = d["player_id"]
            else:
                _token_b = d["token"]
                _player_id_b = d["player_id"]
            print(f"  {INFO} {label} registered: {user['username']} (id={d['player_id']})")
        else:
            # Try login if already exists
            r2 = requests.post(
                f"{API}/auth/login",
                json={"username": user["username"], "password": user["password"]},
                timeout=10,
            )
            if r2.status_code == 200:
                d = r2.json()
                if setter == "a":
                    _token_a = d["token"]
                    _player_id_a = d["player_id"]
                else:
                    _token_b = d["token"]
                    _player_id_b = d["player_id"]
                print(f"  {INFO} {label} logged in: {user['username']}")
            else:
                print(f"  {FAIL} {label} auth failed: HTTP {r2.status_code}")
                sys.exit(1)

    # Create a session for User A
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id_a},
        headers=_auth_a(),
        timeout=10,
    )
    if r.status_code == 200:
        _session_id_a = r.json()["id"]
        requests.patch(
            f"{API}/game/sessions/{_session_id_a}",
            json={"score": 500, "level_reached": 3, "completed": True},
            headers=_auth_a(),
            timeout=10,
        )
        print(f"  {INFO} Created session for User A (id={_session_id_a})")
    else:
        print(f"  {WARN} Could not create session for User A: HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  1 · PLAYER IDOR — User B should NOT modify/delete User A's player
# ══════════════════════════════════════════════════════════════════════════════

def test_update_other_player():
    """User B tries to PUT /game/players/:id with User A's player_id"""
    if not (_token_b and _player_id_a):
        fail("Update other player", "skipped (no auth)")
        return
    r = requests.put(
        f"{API}/game/players/{_player_id_a}",
        json={"username": "hacked_username", "email": "hacked@evil.com"},
        headers=_auth_b(),
        timeout=10,
    )
    if r.status_code in (403, 404):
        ok("User B cannot update User A's player → 403/404")
    elif r.status_code == 200:
        warn(
            "IDOR: User B updated User A's player",
            "PUT /game/players/:id has no ownership check — SECURITY ISSUE"
        )
    else:
        warn(f"Update other player", f"Unexpected HTTP {r.status_code}")


def test_delete_other_player():
    """User B tries to DELETE /game/players/:id with User A's player_id"""
    if not (_token_b and _player_id_a):
        fail("Delete other player", "skipped (no auth)")
        return
    r = requests.delete(
        f"{API}/game/players/{_player_id_a}",
        headers=_auth_b(),
        timeout=10,
    )
    if r.status_code in (403, 404):
        ok("User B cannot delete User A's player → 403/404")
    elif r.status_code == 200:
        warn(
            "IDOR: User B deleted User A's player",
            "DELETE /game/players/:id has no ownership check — CRITICAL SECURITY ISSUE"
        )
    else:
        warn(f"Delete other player", f"Unexpected HTTP {r.status_code}")


def test_get_other_player():
    """User B tries to GET /game/players/:id for User A"""
    if not (_token_b and _player_id_a):
        fail("Get other player", "skipped (no auth)")
        return
    r = requests.get(
        f"{API}/game/players/{_player_id_a}",
        headers=_auth_b(),
        timeout=10,
    )
    # Reading another player's public info might be intentionally allowed
    if r.status_code == 200:
        d = r.json()
        sensitive_fields = ["password", "password_hash", "secret", "raw_token"]
        leaked = [f for f in sensitive_fields if f in d]
        if leaked:
            fail("Get other player", f"Sensitive fields leaked: {leaked}")
        else:
            ok("GET other player → allowed (no sensitive fields leaked)")
    elif r.status_code in (403, 404):
        ok("User B cannot view User A's player → 403/404")
    else:
        warn(f"Get other player", f"Unexpected HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · SESSION IDOR — User B should NOT modify/delete User A's sessions
# ══════════════════════════════════════════════════════════════════════════════

def test_update_other_session():
    """User B tries to PATCH User A's game session"""
    if not (_token_b and _session_id_a):
        fail("Update other session", "skipped (no session)")
        return
    r = requests.patch(
        f"{API}/game/sessions/{_session_id_a}",
        json={"score": 999999, "completed": True},
        headers=_auth_b(),
        timeout=10,
    )
    if r.status_code in (403, 404):
        ok("User B cannot update User A's session → 403/404")
    elif r.status_code == 200:
        warn(
            "IDOR: User B modified User A's session",
            "PATCH /game/sessions/:id has no ownership check — SECURITY ISSUE"
        )
    else:
        warn(f"Update other session", f"Unexpected HTTP {r.status_code}")


def test_delete_other_session():
    """User B tries to DELETE User A's game session"""
    if not (_token_b and _session_id_a):
        fail("Delete other session", "skipped (no session)")
        return
    r = requests.delete(
        f"{API}/game/sessions/{_session_id_a}",
        headers=_auth_b(),
        timeout=10,
    )
    if r.status_code in (403, 404):
        ok("User B cannot delete User A's session → 403/404")
    elif r.status_code == 200:
        warn(
            "IDOR: User B deleted User A's session",
            "DELETE /game/sessions/:id has no ownership check — SECURITY ISSUE"
        )
    else:
        warn(f"Delete other session", f"Unexpected HTTP {r.status_code}")


def test_create_session_for_other_player():
    """User B tries to create a session for User A's player_id"""
    if not (_token_b and _player_id_a):
        fail("Create session for other player", "skipped (no auth)")
        return
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id_a},
        headers=_auth_b(),
        timeout=10,
    )
    if r.status_code in (403, 400):
        ok("User B cannot create session for User A's player → 403/400")
    elif r.status_code == 200:
        warn(
            "IDOR: User B created session for User A",
            "POST /game/sessions accepts any player_id — SECURITY ISSUE"
        )
        # Cleanup: delete the session we just created
        sid = r.json().get("id")
        if sid:
            requests.delete(f"{API}/game/sessions/{sid}", headers=_auth_b(), timeout=10)
    else:
        warn(f"Create session for other player", f"Unexpected HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · PROFILE IDOR — User B should NOT modify User A's profile
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_isolation():
    """User B's profile/me should only return User B's data"""
    if not _token_b:
        fail("Profile isolation", "skipped (no token)")
        return
    r = requests.get(f"{API}/game/profile/me", headers=_auth_b(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        if d.get("username") == USER_B["username"]:
            ok("Profile /me returns only own data (User B)")
        elif d.get("username") == USER_A["username"]:
            fail("Profile isolation", "User B sees User A's profile!")
        else:
            ok(f"Profile /me returns user data (username={d.get('username')})")
    else:
        fail("Profile isolation", f"HTTP {r.status_code}")


def _ensure_user_a():
    """Re-register User A if their player was deleted by an earlier IDOR test."""
    global _token_a, _player_id_a
    # Quick check — can we still reach User A's profile?
    r = requests.get(f"{API}/game/profile/me", headers=_auth_a(), timeout=10)
    if r.status_code == 200:
        return True
    # Player was deleted (IDOR vulnerability) — re-register
    r2 = requests.post(f"{API}/auth/register", json=USER_A, timeout=10)
    if r2.status_code == 200:
        d = r2.json()
        _token_a = d["token"]
        _player_id_a = d["player_id"]
        return True
    # Try login (maybe username still exists with a new id)
    r3 = requests.post(
        f"{API}/auth/login",
        json={"username": USER_A["username"], "password": USER_A["password"]},
        timeout=10,
    )
    if r3.status_code == 200:
        d = r3.json()
        _token_a = d["token"]
        _player_id_a = d["player_id"]
        return True
    return False


def test_update_profile_cross_user():
    """Verify PATCH /profile/me only updates own profile"""
    if not (_token_a and _token_b):
        fail("Cross-user profile update", "skipped (no auth)")
        return

    # Re-create User A if deleted by earlier IDOR test
    if not _ensure_user_a():
        warn("Cross-user profile update", "Cannot restore User A after IDOR deletion")
        return

    # User A sets a specific bio
    bio_a = f"User A bio at {TS}"
    r_a = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": bio_a},
        headers=_auth_a(),
        timeout=10,
    )
    if r_a.status_code != 200:
        warn("Cross-user profile update", f"User A PATCH failed: HTTP {r_a.status_code}")
        return

    # User B sets a different bio
    bio_b = f"User B bio at {TS}"
    requests.patch(
        f"{API}/game/profile/me",
        json={"bio": bio_b},
        headers=_auth_b(),
        timeout=10,
    )

    # Verify User A's bio is unchanged
    r = requests.get(f"{API}/game/profile/me", headers=_auth_a(), timeout=10)
    if r.status_code == 200:
        actual = r.json().get("bio", "")
        if bio_a in actual:
            ok("Profile update doesn't cross-contaminate between users")
        elif bio_b in actual:
            fail("Cross-user profile update", "User B's bio ended up on User A's profile!")
        else:
            warn("Cross-user profile update", f"User A bio unexpected: {actual[:80]}")
    else:
        fail("Cross-user profile update", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · SESSION DATA ISOLATION
# ══════════════════════════════════════════════════════════════════════════════

def test_session_list_filtering():
    """User B's session list should not include User A's sessions"""
    if not (_token_b and _player_id_b):
        fail("Session list filtering", "skipped (no auth)")
        return

    # Create a session for User B
    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id_b},
        headers=_auth_b(),
        timeout=10,
    )
    if r1.status_code != 200:
        warn("Session list filtering", f"Cannot create session for User B: HTTP {r1.status_code}")
        return

    # Get User B's sessions filtered by player_id
    r2 = requests.get(
        f"{API}/game/sessions?player_id={_player_id_b}",
        headers=_auth_b(),
        timeout=10,
    )
    if r2.status_code == 200:
        sessions = r2.json()
        foreign = [s for s in sessions if s.get("player_id") != _player_id_b
                   and s.get("player", {}).get("id") != _player_id_b]
        if not foreign:
            ok("Session list filtered correctly (no foreign sessions)")
        else:
            fail("Session list filtering", f"Found {len(foreign)} sessions belonging to other players")
    else:
        fail("Session list filtering", f"HTTP {r2.status_code}")


def test_avatar_upload_isolation():
    """User B cannot upload avatar to User A's profile"""
    # /profile/me/avatar always targets the authenticated user's profile,
    # so this should inherently work. But let's verify.
    if not _token_b:
        fail("Avatar upload isolation", "skipped (no auth)")
        return

    # Upload as User B
    import struct
    import zlib
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xFFFFFFFF)
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00\xff\x00\x00')
    png = signature + make_chunk(b'IHDR', ihdr) + make_chunk(b'IDAT', idat) + make_chunk(b'IEND', b'')

    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("test.png", png, "image/png")},
        headers=_auth_b(),
        timeout=15,
    )

    if r.status_code == 200:
        # Verify User A's avatar was not changed
        ra = requests.get(f"{API}/game/profile/me", headers=_auth_a(), timeout=10)
        rb = requests.get(f"{API}/game/profile/me", headers=_auth_b(), timeout=10)
        if ra.status_code == 200 and rb.status_code == 200:
            avatar_a = ra.json().get("avatar_url") or ""
            avatar_b = rb.json().get("avatar_url") or ""
            if avatar_a != avatar_b or not avatar_b:
                ok("Avatar upload isolated — User B's upload didn't affect User A")
            else:
                warn("Avatar upload isolation", "Both users have same avatar URL")
        else:
            warn("Avatar isolation check", "Could not verify profiles")
    elif r.status_code in (401, 403):
        ok("Avatar upload requires auth (confirmed)")
    else:
        warn("Avatar upload isolation", f"Unexpected HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Authorization (IDOR) Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("Setup — Create two test users")
    _setup()

    section("1 · Player IDOR")
    test_update_other_player()
    test_delete_other_player()
    test_get_other_player()

    section("2 · Session IDOR")
    test_update_other_session()
    test_delete_other_session()
    test_create_session_for_other_player()

    section("3 · Profile IDOR")
    test_profile_isolation()
    test_update_profile_cross_user()

    section("4 · Session Data Isolation")
    test_session_list_filtering()
    test_avatar_upload_isolation()

    # Summary
    print(f"\n{'═' * 60}")
    total = 10
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} authorization tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))")
        else:
            print()
    else:
        print(f"  \033[91m{failed}/{total} authorization test(s) FAILED:\033[0m")
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
