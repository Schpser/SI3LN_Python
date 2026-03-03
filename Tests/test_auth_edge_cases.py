"""
SI3LN Auth Edge Case Tests
============================
Tests edge cases for authentication: change-password success flow,
token invalidation, consecutive refreshes, password strength.

Usage:
    python Tests/test_auth_edge_cases.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_auth_edge_cases.py
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

ORIGINAL_PASSWORD = "OriginalPass1!"
NEW_PASSWORD = "NewSecurePass2!"

TEST_USER = {
    "username": f"auth_edge_{TS}",
    "password": ORIGINAL_PASSWORD,
    "email": f"auth_edge_{TS}@test.com",
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


# ══════════════════════════════════════════════════════════════════════════════
#  1 · CHANGE PASSWORD — FULL SUCCESS FLOW
# ══════════════════════════════════════════════════════════════════════════════

def test_change_password_success():
    """Change password with correct old password → login with new password"""
    global _token
    if not _token:
        fail("Change password success", "skipped (no token)")
        return

    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": ORIGINAL_PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        ok("Change password → success (HTTP 200)")
    else:
        fail("Change password success", f"HTTP {r.status_code} — {r.text[:200]}")
        return

    # Login with new password
    r2 = requests.post(
        f"{API}/auth/login",
        json={"username": TEST_USER["username"], "password": NEW_PASSWORD},
        timeout=10,
    )
    if r2.status_code == 200:
        _token = r2.json()["token"]
        ok("Login with new password → success")
    else:
        fail("Login with new password", f"HTTP {r2.status_code}")


def test_old_password_rejected_after_change():
    """After changing password, old password should be rejected"""
    r = requests.post(
        f"{API}/auth/login",
        json={"username": TEST_USER["username"], "password": ORIGINAL_PASSWORD},
        timeout=10,
    )
    if r.status_code in (401, 400):
        ok("Old password rejected after change → 401/400")
    elif r.status_code == 200:
        fail("Old password still works after change", "Password was not actually changed!")
    else:
        warn("Old password after change", f"Unexpected HTTP {r.status_code}")


def test_change_password_restore():
    """Restore original password for other tests"""
    global _token
    if not _token:
        fail("Restore password", "skipped (no token)")
        return

    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": NEW_PASSWORD, "new_password": ORIGINAL_PASSWORD},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        ok("Password restored to original")
        # Re-login to get fresh token
        r2 = requests.post(
            f"{API}/auth/login",
            json={"username": TEST_USER["username"], "password": ORIGINAL_PASSWORD},
            timeout=10,
        )
        if r2.status_code == 200:
            _token = r2.json()["token"]
    else:
        warn("Restore password", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · PASSWORD STRENGTH DURING CHANGE
# ══════════════════════════════════════════════════════════════════════════════

def test_change_password_empty_new():
    """Change password with empty new password"""
    if not _token:
        fail("Change password empty new", "skipped (no token)")
        return
    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": ORIGINAL_PASSWORD, "new_password": ""},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Change password (empty new) → rejected")
    elif r.status_code == 200:
        warn("Change password empty new", "Server accepted empty password")
        # Restore
        requests.post(
            f"{API}/auth/change-password",
            json={"old_password": "", "new_password": ORIGINAL_PASSWORD},
            headers=_auth(),
            timeout=10,
        )
    else:
        warn("Change password empty new", f"HTTP {r.status_code}")


def test_change_password_too_short():
    """Change password to a very short new password"""
    if not _token:
        fail("Change password too short", "skipped (no token)")
        return
    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": ORIGINAL_PASSWORD, "new_password": "ab"},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Change password (too short) → rejected")
    elif r.status_code == 200:
        warn("Change password too short", "Server accepted 2-char password")
        # Restore
        requests.post(
            f"{API}/auth/change-password",
            json={"old_password": "ab", "new_password": ORIGINAL_PASSWORD},
            headers=_auth(),
            timeout=10,
        )
    else:
        warn("Change password too short", f"HTTP {r.status_code}")


def test_change_password_same_as_old():
    """Change password to the same old password"""
    if not _token:
        fail("Change password same as old", "skipped (no token)")
        return
    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": ORIGINAL_PASSWORD, "new_password": ORIGINAL_PASSWORD},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Change password (same as old) → rejected")
    elif r.status_code == 200:
        # Not necessarily wrong, but might want to warn users
        warn("Change password same as old", "Server accepted same password (no reuse policy)")
    else:
        warn("Change password same as old", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · TOKEN REFRESH EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

def test_consecutive_token_refreshes():
    """Refresh token multiple times in a row"""
    global _token
    if not _token:
        fail("Consecutive refreshes", "skipped (no token)")
        return

    current_token = _token
    tokens_seen = {current_token}
    all_ok = True

    for i in range(3):
        r = requests.post(
            f"{API}/auth/refresh",
            headers={"Authorization": f"Bearer {current_token}"},
            timeout=10,
        )
        if r.status_code == 200:
            new_token = r.json().get("token", "")
            if new_token:
                tokens_seen.add(new_token)
                current_token = new_token
            else:
                fail(f"Refresh #{i+1}", "No token in response")
                all_ok = False
                break
        else:
            fail(f"Refresh #{i+1}", f"HTTP {r.status_code}")
            all_ok = False
            break

    if all_ok:
        _token = current_token  # keep global token current
        ok(f"3 consecutive token refreshes → all succeeded ({len(tokens_seen)} unique tokens)")


def test_refresh_with_old_token_after_refresh():
    """After refreshing, the old token may or may not still work"""
    global _token
    if not _token:
        fail("Old token after refresh", "skipped (no token)")
        return

    old_token = _token

    # Refresh to get new token
    r = requests.post(
        f"{API}/auth/refresh",
        headers={"Authorization": f"Bearer {old_token}"},
        timeout=10,
    )
    if r.status_code != 200:
        fail("Old token test setup", f"Refresh failed: HTTP {r.status_code}")
        return

    new_token = r.json().get("token", "")
    _token = new_token  # keep global token current

    # Try using old token
    r2 = requests.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {old_token}"},
        timeout=10,
    )
    if r2.status_code == 200:
        warn("Old token after refresh", "Old token still works (no token rotation/blacklist)")
    elif r2.status_code in (401, 403):
        ok("Old token invalidated after refresh")
    else:
        warn("Old token after refresh", f"Unexpected HTTP {r2.status_code}")


def test_token_after_logout():
    """After logout, the token should ideally be invalidated"""
    if not _token:
        fail("Token after logout", "skipped (no token)")
        return

    # Login fresh to get a token we can sacrifice
    r0 = requests.post(
        f"{API}/auth/login",
        json={"username": TEST_USER["username"], "password": ORIGINAL_PASSWORD},
        timeout=10,
    )
    if r0.status_code != 200:
        fail("Token after logout setup", f"Login failed: HTTP {r0.status_code}")
        return

    logout_token = r0.json()["token"]

    # Logout
    requests.post(
        f"{API}/auth/logout",
        headers={"Authorization": f"Bearer {logout_token}"},
        timeout=10,
    )

    # Try using the token after logout
    r2 = requests.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {logout_token}"},
        timeout=10,
    )
    if r2.status_code in (401, 403):
        ok("Token invalidated after logout")
    elif r2.status_code == 200:
        warn("Token after logout", "Token still valid after logout (no server-side blacklist)")
    else:
        warn("Token after logout", f"Unexpected HTTP {r2.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · UPDATE ACCOUNT EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

def test_update_account_first_last_name():
    """PATCH /api/auth/update-account — update first_name/last_name"""
    if not _token:
        fail("Update account names", "skipped (no token)")
        return
    r = requests.patch(
        f"{API}/auth/update-account",
        json={"first_name": "Test", "last_name": "User"},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        if d.get("first_name") == "Test" and d.get("last_name") == "User":
            ok("Update first_name/last_name → saved")
        else:
            warn("Update account names", "Fields not reflected in response")
    elif r.status_code in (400, 422):
        ok("Update account names → rejected (fields not supported)")
    else:
        warn("Update account names", f"HTTP {r.status_code}")


def test_update_account_duplicate_email():
    """PATCH /api/auth/update-account with an email that belongs to another user"""
    if not _token:
        fail("Update account duplicate email", "skipped (no token)")
        return

    # Register another user with a known email
    ts2 = int(time.time() * 1000)
    other_email = f"other_{ts2}@test.com"
    requests.post(
        f"{API}/auth/register",
        json={"username": f"other_{ts2}", "password": "OtherPass1!", "email": other_email},
        timeout=10,
    )

    # Try to set our email to the other user's email
    r = requests.patch(
        f"{API}/auth/update-account",
        json={"email": other_email},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 409, 422):
        ok("Update account with duplicate email → rejected")
    elif r.status_code == 200:
        warn("Update account duplicate email", "Server accepted duplicate email (no uniqueness check)")
    else:
        warn("Update account duplicate email", f"HTTP {r.status_code}")


def test_register_very_long_username():
    """Register with a very long username (boundary test)"""
    long_user = {
        "username": "x" * 200,
        "password": "LongUserPass1!",
        "email": f"longuser_{TS}@test.com",
    }
    r = requests.post(f"{API}/auth/register", json=long_user, timeout=10)
    if r.status_code in (400, 422):
        ok("Very long username (200 chars) → rejected")
    elif r.status_code == 200:
        warn("Very long username", "Server accepted 200-char username")
    else:
        warn("Very long username", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Auth Edge Case Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("Setup — Create test user")
    _setup()

    section("1 · Change Password — Full Flow")
    test_change_password_success()
    test_old_password_rejected_after_change()
    test_change_password_restore()

    section("2 · Password Strength During Change")
    test_change_password_empty_new()
    test_change_password_too_short()
    test_change_password_same_as_old()

    section("3 · Token Refresh Edge Cases")
    test_consecutive_token_refreshes()
    test_refresh_with_old_token_after_refresh()
    test_token_after_logout()

    section("4 · Account Update Edge Cases")
    test_update_account_first_last_name()
    test_update_account_duplicate_email()
    test_register_very_long_username()

    # Summary
    print(f"\n{'═' * 60}")
    total = 12
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} auth edge case tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))")
        else:
            print()
    else:
        print(f"  \033[91m{failed}/{total} auth edge case test(s) FAILED:\033[0m")
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
