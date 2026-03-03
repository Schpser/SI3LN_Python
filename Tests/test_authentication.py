"""
SI3LN Authentication Tests
============================
Comprehensive tests for auth flow: register, login, token, permissions.

Usage:
    python Tests/test_auth.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_auth.py
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


# ── Test Data ──────────────────────────────────────────────────────────────────

TS = int(time.time())
VALID_USER = {
    "username": f"auth_test_{TS}",
    "password": "SecurePass123!",
    "email": f"auth_{TS}@test.com",
}

_token: str = ""
_player_id: int | None = None


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_token}"}


# ══════════════════════════════════════════════════════════════════════════════
#  1 · REGISTRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_register_valid():
    """Register a new user with valid data"""
    global _token, _player_id
    r = requests.post(f"{API}/auth/register", json=VALID_USER, timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert "token" in d, "Response missing 'token'"
        assert "player_id" in d, "Response missing 'player_id'"
        assert d["username"] == VALID_USER["username"], "Username mismatch"
        _token = d["token"]
        _player_id = d["player_id"]
        ok(f"Register valid user (player_id={_player_id})")
    else:
        fail("Register valid user", f"HTTP {r.status_code} — {r.text[:200]}")


def test_register_duplicate_username():
    """Attempt to register with an already-taken username"""
    r = requests.post(f"{API}/auth/register", json=VALID_USER, timeout=10)
    if r.status_code in (400, 409, 422):
        ok("Register duplicate username → rejected")
    else:
        fail("Register duplicate username", f"Expected 400/409/422, got {r.status_code}")


def test_register_missing_username():
    """Register without username field"""
    r = requests.post(
        f"{API}/auth/register",
        json={"password": "Test1234!", "email": "no_user@test.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Register missing username → rejected")
    else:
        fail("Register missing username", f"Expected 400/422, got {r.status_code}")


def test_register_missing_password():
    """Register without password field"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"nopass_{TS}", "email": "nopass@test.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Register missing password → rejected")
    else:
        fail("Register missing password", f"Expected 400/422, got {r.status_code}")


def test_register_empty_body():
    """Register with empty body"""
    r = requests.post(f"{API}/auth/register", json={}, timeout=10)
    if r.status_code in (400, 422):
        ok("Register empty body → rejected")
    else:
        fail("Register empty body", f"Expected 400/422, got {r.status_code}")


def test_register_invalid_json():
    """Register with invalid JSON"""
    r = requests.post(
        f"{API}/auth/register",
        data="not json",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Register invalid JSON → rejected")
    else:
        warn("Register invalid JSON", f"Got {r.status_code} (expected 400/422)")


def test_register_without_email():
    """Register without email (should work — email is optional)"""
    user = {
        "username": f"noemail_{TS}",
        "password": "ValidPass123!",
    }
    r = requests.post(f"{API}/auth/register", json=user, timeout=10)
    if r.status_code == 200:
        ok("Register without email → accepted (optional field)")
    elif r.status_code in (400, 422):
        ok("Register without email → rejected (email required by server)")
    else:
        fail("Register without email", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · LOGIN TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_login_valid():
    """Login with correct credentials"""
    global _token, _player_id
    r = requests.post(
        f"{API}/auth/login",
        json={"username": VALID_USER["username"], "password": VALID_USER["password"]},
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        assert "token" in d, "Response missing token"
        assert "player_id" in d, "Response missing player_id"
        _token = d["token"]
        _player_id = d["player_id"]
        ok(f"Login valid credentials (player_id={_player_id})")
    else:
        fail("Login valid credentials", f"HTTP {r.status_code} — {r.text[:200]}")


def test_login_wrong_password():
    """Login with wrong password"""
    r = requests.post(
        f"{API}/auth/login",
        json={"username": VALID_USER["username"], "password": "WrongPassword999!"},
        timeout=10,
    )
    if r.status_code in (401, 400):
        ok("Login wrong password → 401/400")
    else:
        fail("Login wrong password", f"Expected 401/400, got {r.status_code}")


def test_login_nonexistent_user():
    """Login with a username that doesn't exist"""
    r = requests.post(
        f"{API}/auth/login",
        json={"username": "nonexistent_user_xyz_99999", "password": "Whatever123!"},
        timeout=10,
    )
    if r.status_code in (401, 400):
        ok("Login nonexistent user → 401/400")
    else:
        fail("Login nonexistent user", f"Expected 401/400, got {r.status_code}")


def test_login_missing_fields():
    """Login with missing username or password"""
    # Missing password
    r1 = requests.post(
        f"{API}/auth/login",
        json={"username": VALID_USER["username"]},
        timeout=10,
    )
    # Missing username
    r2 = requests.post(
        f"{API}/auth/login",
        json={"password": VALID_USER["password"]},
        timeout=10,
    )
    if r1.status_code in (400, 422) and r2.status_code in (400, 422):
        ok("Login missing fields → rejected")
    else:
        fail("Login missing fields", f"Got {r1.status_code} and {r2.status_code}")


def test_login_empty_body():
    """Login with empty body"""
    r = requests.post(f"{API}/auth/login", json={}, timeout=10)
    if r.status_code in (400, 422):
        ok("Login empty body → rejected")
    else:
        fail("Login empty body", f"Expected 400/422, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · TOKEN / AUTH TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_get_current_user():
    """GET /api/auth/me with valid token"""
    if not _token:
        fail("GET /api/auth/me", "skipped (no token)")
        return
    r = requests.get(f"{API}/auth/me", headers=_auth_headers(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert d["username"] == VALID_USER["username"], "Username mismatch"
        assert "player_id" in d, "Missing player_id"
        assert "role" in d, "Missing role"
        ok("GET /api/auth/me (valid token)")
    else:
        fail("GET /api/auth/me", f"HTTP {r.status_code}")


def test_me_without_token():
    """GET /api/auth/me without token should be rejected"""
    r = requests.get(f"{API}/auth/me", timeout=10)
    if r.status_code in (401, 403):
        ok("GET /api/auth/me (no token → 401/403)")
    else:
        fail("GET /api/auth/me no token", f"Expected 401/403, got {r.status_code}")


def test_me_with_invalid_token():
    """GET /api/auth/me with garbage token"""
    r = requests.get(
        f"{API}/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("GET /api/auth/me (invalid token → 401/403)")
    else:
        fail("GET /api/auth/me invalid token", f"Expected 401/403, got {r.status_code}")


def test_me_with_expired_token():
    """GET /api/auth/me with an expired JWT (crafted)"""
    # Craft a JWT that is technically valid format but expired
    import base64
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b'=').decode()
    payload = base64.urlsafe_b64encode(
        b'{"user_id":1,"exp":1000000000,"iat":999999900}'
    ).rstrip(b'=').decode()
    fake_sig = base64.urlsafe_b64encode(b'fakesig').rstrip(b'=').decode()
    expired_token = f"{header}.{payload}.{fake_sig}"

    r = requests.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("GET /api/auth/me (expired token → 401/403)")
    else:
        fail("GET /api/auth/me expired token", f"Expected 401/403, got {r.status_code}")


def test_token_refresh():
    """POST /api/auth/refresh with valid token"""
    if not _token:
        fail("POST /api/auth/refresh", "skipped (no token)")
        return
    r = requests.post(f"{API}/auth/refresh", headers=_auth_headers(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        assert "token" in d, "Missing token in refresh response"
        ok("POST /api/auth/refresh (valid)")
    else:
        fail("POST /api/auth/refresh", f"HTTP {r.status_code}")


def test_token_refresh_no_auth():
    """POST /api/auth/refresh without token"""
    r = requests.post(f"{API}/auth/refresh", timeout=10)
    if r.status_code in (401, 403):
        ok("POST /api/auth/refresh (no token → 401/403)")
    else:
        fail("POST /api/auth/refresh no auth", f"Expected 401/403, got {r.status_code}")


def test_logout():
    """POST /api/auth/logout"""
    r = requests.post(f"{API}/auth/logout", timeout=10)
    if r.status_code == 200:
        ok("POST /api/auth/logout")
    else:
        fail("POST /api/auth/logout", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · CHANGE PASSWORD TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_change_password_wrong_old():
    """Change password with wrong old password"""
    if not _token:
        fail("Change password (wrong old)", "skipped (no token)")
        return
    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": "WrongOldPass!", "new_password": "NewPass999!"},
        headers=_auth_headers(),
        timeout=10,
    )
    if r.status_code in (400, 403):
        ok("Change password (wrong old → rejected)")
    else:
        fail("Change password wrong old", f"Expected 400/403, got {r.status_code}")


def test_change_password_no_auth():
    """Change password without authentication"""
    r = requests.post(
        f"{API}/auth/change-password",
        json={"old_password": "anything", "new_password": "anything"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Change password (no auth → 401/403)")
    else:
        fail("Change password no auth", f"Expected 401/403, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · PROTECTED ENDPOINT ACCESS TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_protected_endpoints_without_token():
    """Various protected endpoints should return 401/403 without a token"""
    protected = [
        ("GET", "/game/players"),
        ("GET", "/game/sessions"),
        ("GET", "/game/profile/me"),
    ]
    all_ok = True
    for method, endpoint in protected:
        if method == "GET":
            r = requests.get(f"{API}{endpoint}", timeout=10)
        elif method == "POST":
            r = requests.post(f"{API}{endpoint}", json={}, timeout=10)
        else:
            r = requests.get(f"{API}{endpoint}", timeout=10)

        if r.status_code not in (401, 403):
            fail(f"Protected {method} {endpoint}", f"Expected 401/403, got {r.status_code}")
            all_ok = False

    if all_ok:
        ok("All protected endpoints reject unauthenticated requests")


def test_protected_endpoints_with_token():
    """Protected endpoints should succeed with valid token"""
    if not _token:
        fail("Protected endpoints with token", "skipped (no token)")
        return
    endpoints = [
        "/game/profile/me",
    ]
    all_ok = True
    for endpoint in endpoints:
        r = requests.get(f"{API}{endpoint}", headers=_auth_headers(), timeout=10)
        if r.status_code != 200:
            fail(f"GET {endpoint} with token", f"HTTP {r.status_code}")
            all_ok = False

    if all_ok:
        ok("Protected endpoints return 200 with valid token")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Authentication Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("1 · Registration")
    test_register_valid()
    test_register_duplicate_username()
    test_register_missing_username()
    test_register_missing_password()
    test_register_empty_body()
    test_register_invalid_json()
    test_register_without_email()

    section("2 · Login")
    test_login_valid()
    test_login_wrong_password()
    test_login_nonexistent_user()
    test_login_missing_fields()
    test_login_empty_body()

    section("3 · Token & Auth")
    test_get_current_user()
    test_me_without_token()
    test_me_with_invalid_token()
    test_me_with_expired_token()
    test_token_refresh()
    test_token_refresh_no_auth()
    test_logout()

    section("4 · Change Password")
    test_change_password_wrong_old()
    test_change_password_no_auth()

    section("5 · Protected Endpoint Access")
    test_protected_endpoints_without_token()
    test_protected_endpoints_with_token()

    # Summary
    print(f"\n{'═' * 60}")
    total = 21
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} auth tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))", end="")
        print()
    else:
        print(f"  \033[91m{failed}/{total} auth test(s) FAILED:\033[0m")
        for e in errors:
            print(f"    • {e}")
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
