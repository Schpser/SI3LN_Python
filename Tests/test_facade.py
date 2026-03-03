"""
SI3LN Facade Unit Tests
=========================
Tests the ApiFacade security layer: sanitization, validation, rate limiting.
These tests run offline — no server needed.

Usage:
    python Tests/test_facade.py
"""

import os
import sys
import time

# Add API directory to path so we can import facade
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)
API_DIR = os.path.join(PROJECT_DIR, "api")
sys.path.insert(0, API_DIR)

# Setup Django settings before importing any Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "si3ln_api.settings")

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


# ── Import facade components ─────────────────────────────────────────────────

try:
    from game.facade import (
        _sanitize,
        _sanitize_dict,
        _safe_error,
        _validate_username,
        _validate_email,
        _check_rate_limit,
        _rate_limits,
        ApiFacade,
        SENSITIVE_FIELDS,
        SAFE_AUTH_FIELDS,
    )
    FACADE_AVAILABLE = True
except Exception as e:
    FACADE_AVAILABLE = False
    IMPORT_ERROR = str(e)


# ══════════════════════════════════════════════════════════════════════════════
#  1 · SANITIZATION
# ══════════════════════════════════════════════════════════════════════════════

def test_sanitize_removes_sensitive():
    """_sanitize strips sensitive fields from dict"""
    if not FACADE_AVAILABLE:
        fail("Sanitize sensitive fields", f"Import error: {IMPORT_ERROR}")
        return

    data = {
        "username": "testuser",
        "player_id": 1,
        "password": "secret123",
        "password_hash": "abc123hash",
        "secret": "top_secret",
        "private_key": "rsa_key",
        "refresh_token": "token123",
        "raw_token": "jwt_here",
    }
    result = _sanitize(data)

    # Should keep non-sensitive fields
    if result.get("username") != "testuser" or result.get("player_id") != 1:
        fail("Sanitize keeps safe fields", f"username/player_id missing")
        return

    # Should remove sensitive fields
    leaked = [k for k in SENSITIVE_FIELDS if k in result]
    if not leaked:
        ok("_sanitize removes all sensitive fields")
    else:
        fail("_sanitize sensitive fields", f"Still present: {leaked}")


def test_sanitize_recursive():
    """_sanitize recurses into nested dicts and lists"""
    if not FACADE_AVAILABLE:
        fail("Sanitize recursive", f"Import error: {IMPORT_ERROR}")
        return

    data = {
        "user": {
            "name": "test",
            "password": "should_be_removed",
            "settings": {
                "theme": "dark",
                "secret": "nested_secret",
            }
        },
        "items": [
            {"id": 1, "password": "in_list"},
            {"id": 2, "name": "safe"},
        ]
    }
    result = _sanitize(data)

    has_password = "password" in result.get("user", {})
    has_nested_secret = "secret" in result.get("user", {}).get("settings", {})
    has_list_password = any("password" in item for item in result.get("items", []))

    if not has_password and not has_nested_secret and not has_list_password:
        ok("_sanitize recursively removes sensitive fields")
    else:
        fail("_sanitize recursive", f"password={has_password}, secret={has_nested_secret}, list={has_list_password}")


def test_sanitize_dict_allow_filter():
    """_sanitize_dict with allow set keeps only allowed fields"""
    if not FACADE_AVAILABLE:
        fail("Sanitize dict allow", f"Import error: {IMPORT_ERROR}")
        return

    data = {
        "username": "test",
        "player_id": 1,
        "session_id": "abc",
        "role": "player",
        "internal_data": "should_be_removed",
        "extra": "also_removed",
    }
    result = _sanitize_dict(data, allow=SAFE_AUTH_FIELDS)

    if "username" in result and "player_id" in result and "role" in result:
        if "internal_data" not in result and "extra" not in result:
            ok("_sanitize_dict with allow filter keeps only safe fields")
        else:
            fail("_sanitize_dict allow", "Extra fields not filtered out")
    else:
        fail("_sanitize_dict allow", f"Missing expected fields: {result}")


def test_sanitize_preserves_non_sensitive():
    """_sanitize leaves non-sensitive data untouched"""
    if not FACADE_AVAILABLE:
        fail("Sanitize preserves", f"Import error: {IMPORT_ERROR}")
        return

    data = {
        "id": 42,
        "username": "hero",
        "score": 1500,
        "level": 7,
        "items": [1, 2, 3],
        "nested": {"key": "value"},
    }
    result = _sanitize(data)

    if result == data:
        ok("_sanitize preserves non-sensitive data completely")
    else:
        fail("_sanitize preserves", f"Data changed: {result}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · VALIDATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def test_validate_username_valid():
    """_validate_username accepts valid usernames"""
    if not FACADE_AVAILABLE:
        fail("Validate username valid", f"Import error: {IMPORT_ERROR}")
        return

    valid = ["abc", "player_1", "TestUser123", "a_b_c", "x" * 30]
    all_ok = True
    for u in valid:
        if not _validate_username(u):
            fail(f"validate_username({u!r})", "Should be valid")
            all_ok = False
    if all_ok:
        ok(f"_validate_username accepts {len(valid)} valid usernames")


def test_validate_username_invalid():
    """_validate_username rejects invalid usernames"""
    if not FACADE_AVAILABLE:
        fail("Validate username invalid", f"Import error: {IMPORT_ERROR}")
        return

    invalid = [
        "",           # empty
        "ab",         # too short
        "x" * 31,    # too long
        "user name",  # space
        "user@name",  # special char
        "user<script>",  # XSS attempt
    ]
    all_ok = True
    for u in invalid:
        if _validate_username(u):
            warn(f"validate_username({u!r})", "Should be invalid")
            all_ok = False
    if all_ok:
        ok(f"_validate_username rejects {len(invalid)} invalid usernames")


def test_validate_email_valid():
    """_validate_email accepts valid emails"""
    if not FACADE_AVAILABLE:
        fail("Validate email valid", f"Import error: {IMPORT_ERROR}")
        return

    valid = ["a@b.com", "user@domain.co.uk", "test+tag@gmail.com"]
    all_ok = True
    for e in valid:
        if not _validate_email(e):
            fail(f"validate_email({e!r})", "Should be valid")
            all_ok = False
    if all_ok:
        ok(f"_validate_email accepts {len(valid)} valid emails")


def test_validate_email_invalid():
    """_validate_email rejects invalid emails"""
    if not FACADE_AVAILABLE:
        fail("Validate email invalid", f"Import error: {IMPORT_ERROR}")
        return

    invalid = ["", "notanemail", "@domain.com", "user@"]
    all_ok = True
    for e in invalid:
        if _validate_email(e):
            warn(f"validate_email({e!r})", "Should be invalid")
            all_ok = False
    if all_ok:
        ok(f"_validate_email rejects {len(invalid)} invalid emails")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · ApiFacade METHODS
# ══════════════════════════════════════════════════════════════════════════════

def test_facade_sanitize_login_response():
    """ApiFacade.sanitize_login_response strips JWT token"""
    if not FACADE_AVAILABLE:
        fail("Sanitize login response", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()
    raw = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature",
        "username": "testuser",
        "player_id": 42,
        "is_staff": False,
    }
    result = facade.sanitize_login_response(raw)

    if "token" not in result:
        if result.get("username") == "testuser" and result.get("player_id") == 42:
            if "session_id" in result and result.get("ok") is True:
                ok("sanitize_login_response → JWT stripped, session_id generated")
            else:
                warn("sanitize_login_response", f"Missing session_id or ok: {result}")
        else:
            fail("sanitize_login_response", f"Missing username/player_id: {result}")
    else:
        fail("sanitize_login_response", "JWT token still in response!")


def test_facade_sanitize_login_admin():
    """Admin user gets role='admin'"""
    if not FACADE_AVAILABLE:
        fail("Sanitize login admin", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()
    raw = {"token": "jwt", "username": "admin", "player_id": 1, "is_staff": True}
    result = facade.sanitize_login_response(raw)

    if result.get("role") == "admin":
        ok("Admin user gets role='admin'")
    else:
        fail("Admin role", f"role={result.get('role')}")


def test_facade_sanitize_leaderboard():
    """ApiFacade.sanitize_leaderboard strips extra fields"""
    if not FACADE_AVAILABLE:
        fail("Sanitize leaderboard", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()
    entries = [
        {"rank": 1, "player_username": "hero", "score": 5000, "internal_id": 42, "password": "oops"},
        {"rank": 2, "player_username": "villain", "score": 3000, "secret": "xxx"},
    ]
    result = facade.sanitize_leaderboard(entries)

    has_internal = any("internal_id" in e for e in result)
    has_password = any("password" in e for e in result)
    has_secret = any("secret" in e for e in result)
    has_required = all("rank" in e and "player_username" in e and "score" in e for e in result)

    if has_required and not has_internal and not has_password and not has_secret:
        ok("sanitize_leaderboard strips extra/sensitive fields")
    else:
        fail("sanitize_leaderboard", f"internal={has_internal}, password={has_password}")


def test_facade_sanitize_game_session():
    """ApiFacade.sanitize_game_session returns only safe fields"""
    if not FACADE_AVAILABLE:
        fail("Sanitize game session", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()
    session = {
        "id": 1, "player_id": 2, "world_id": 3, "score": 500,
        "level_reached": 5, "completed": True,
        "started_at": "2026-01-01", "ended_at": "2026-01-01",
        "internal_note": "debug_info", "password": "leak",
    }
    result = facade.sanitize_game_session(session)

    if "internal_note" not in result and "password" not in result:
        if result.get("id") == 1 and result.get("score") == 500:
            ok("sanitize_game_session returns only safe fields")
        else:
            fail("sanitize_game_session", f"Missing expected fields: {result}")
    else:
        fail("sanitize_game_session", "Sensitive fields leaked")


def test_facade_validate_login_input():
    """validate_login_input catches empty/long inputs"""
    if not FACADE_AVAILABLE:
        fail("Validate login input", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()

    # Valid
    if facade.validate_login_input("user", "pass123") is None:
        pass  # OK
    else:
        fail("validate_login_input valid", "Should return None for valid input")
        return

    # Missing
    if facade.validate_login_input("", "pass"):
        pass  # Returns error message
    else:
        fail("validate_login_input empty username", "Should return error")
        return

    if facade.validate_login_input("user", ""):
        pass
    else:
        fail("validate_login_input empty password", "Should return error")
        return

    # Too long
    if facade.validate_login_input("x" * 31, "pass"):
        pass
    else:
        fail("validate_login_input long username", "Should return error")
        return

    ok("validate_login_input catches all invalid inputs")


def test_facade_validate_signup_input():
    """validate_signup_input enforces password strength"""
    if not FACADE_AVAILABLE:
        fail("Validate signup input", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()

    # Valid
    valid = {"username": "testuser", "email": "test@test.com", "password": "SecurePass1!"}
    if facade.validate_signup_input(valid) is None:
        pass
    else:
        fail("validate_signup_input valid", f"Got error: {facade.validate_signup_input(valid)}")
        return

    # Short password
    short = {"username": "testuser", "email": "a@b.com", "password": "short"}
    err = facade.validate_signup_input(short)
    if err:
        pass
    else:
        fail("validate_signup_input short password", "Should return error")
        return

    # No uppercase
    no_upper = {"username": "testuser", "email": "a@b.com", "password": "alllowercase1"}
    err2 = facade.validate_signup_input(no_upper)
    if err2:
        pass
    else:
        fail("validate_signup_input no uppercase", "Should return error")
        return

    # No digit
    no_digit = {"username": "testuser", "email": "a@b.com", "password": "NoDigitsHere"}
    err3 = facade.validate_signup_input(no_digit)
    if err3:
        pass
    else:
        fail("validate_signup_input no digit", "Should return error")
        return

    ok("validate_signup_input enforces all password rules")


def test_facade_validate_search_query():
    """validate_search_query rejects short/long/injection queries"""
    if not FACADE_AVAILABLE:
        fail("Validate search query", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()

    # Valid
    if facade.validate_search_query("test player") is None:
        pass
    else:
        fail("validate_search_query valid", "Should return None")
        return

    # Too short
    if facade.validate_search_query("a"):
        pass
    else:
        fail("validate_search_query too short", "Should return error")
        return

    # Too long
    if facade.validate_search_query("x" * 101):
        pass
    else:
        fail("validate_search_query too long", "Should return error")
        return

    # Injection characters
    for query in ["<script>alert(1)</script>", "test{injection}", "path\\traversal"]:
        if facade.validate_search_query(query):
            pass
        else:
            fail(f"validate_search_query injection ({query[:20]})", "Should return error")
            return

    ok("validate_search_query catches all invalid patterns")


def test_facade_validate_report_input():
    """validate_report_input requires all fields"""
    if not FACADE_AVAILABLE:
        fail("Validate report input", f"Import error: {IMPORT_ERROR}")
        return

    facade = ApiFacade()

    # Valid
    valid = {"username": "bad_player", "reason": "cheating", "details": "Used speed hacks in game"}
    if facade.validate_report_input(valid) is None:
        pass
    else:
        fail("validate_report_input valid", f"Got error: {facade.validate_report_input(valid)}")
        return

    # Missing username
    if facade.validate_report_input({"reason": "spam", "details": "Spamming chat constantly"}):
        pass
    else:
        fail("validate_report_input no username", "Should return error")
        return

    # Short details
    if facade.validate_report_input({"username": "a", "reason": "x", "details": "short"}):
        pass
    else:
        fail("validate_report_input short details", "Should return error")
        return

    ok("validate_report_input validates all required fields")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · RATE LIMITING
# ══════════════════════════════════════════════════════════════════════════════

def test_rate_limit_allows_normal_traffic():
    """Rate limiter allows requests within the limit"""
    if not FACADE_AVAILABLE:
        fail("Rate limit normal", f"Import error: {IMPORT_ERROR}")
        return

    # Clear rate limits for this test IP
    test_ip = f"test_normal_{time.time()}"
    _rate_limits.pop(test_ip, None)

    # Should allow 30 requests
    all_ok = True
    for i in range(10):
        if not _check_rate_limit(test_ip):
            fail("Rate limit normal", f"Request {i+1} was blocked")
            all_ok = False
            break
    if all_ok:
        ok("Rate limiter allows 10 normal requests")


def test_rate_limit_blocks_excess():
    """Rate limiter blocks requests above the limit"""
    if not FACADE_AVAILABLE:
        fail("Rate limit excess", f"Import error: {IMPORT_ERROR}")
        return

    test_ip = f"test_excess_{time.time()}"
    _rate_limits.pop(test_ip, None)

    # Fill up the limit
    from game.facade import RATE_LIMIT_MAX
    for i in range(RATE_LIMIT_MAX):
        _check_rate_limit(test_ip)

    # Next request should be blocked
    if not _check_rate_limit(test_ip):
        ok(f"Rate limiter blocks request #{RATE_LIMIT_MAX + 1}")
    else:
        fail("Rate limit excess", "Request should have been blocked")


def test_safe_error():
    """_safe_error returns proper error envelope"""
    if not FACADE_AVAILABLE:
        fail("Safe error", f"Import error: {IMPORT_ERROR}")
        return

    result = _safe_error("Something went wrong", 500)
    if result.get("ok") is False and result.get("error") == "Something went wrong" and result.get("status") == 500:
        ok("_safe_error returns correct error envelope")
    else:
        fail("_safe_error", f"Unexpected: {result}")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Facade Unit Tests")
    print(f"  (Offline — no server needed)")
    print(f"{'═' * 60}")

    if not FACADE_AVAILABLE:
        print(f"\n  {FAIL} Cannot import facade: {IMPORT_ERROR}")
        print(f"  {INFO} Make sure Django is installed and DJANGO_SETTINGS_MODULE is set.")
        print(f"  {INFO} Try: cd api && pip install -r requirements.txt\n")
        return 1

    section("1 · Sanitization")
    test_sanitize_removes_sensitive()
    test_sanitize_recursive()
    test_sanitize_dict_allow_filter()
    test_sanitize_preserves_non_sensitive()

    section("2 · Validation Helpers")
    test_validate_username_valid()
    test_validate_username_invalid()
    test_validate_email_valid()
    test_validate_email_invalid()

    section("3 · ApiFacade Methods")
    test_facade_sanitize_login_response()
    test_facade_sanitize_login_admin()
    test_facade_sanitize_leaderboard()
    test_facade_sanitize_game_session()
    test_facade_validate_login_input()
    test_facade_validate_signup_input()
    test_facade_validate_search_query()
    test_facade_validate_report_input()

    section("4 · Rate Limiting")
    test_rate_limit_allows_normal_traffic()
    test_rate_limit_blocks_excess()
    test_safe_error()

    # Summary
    print(f"\n{'═' * 60}")
    total = 19
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} facade tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))")
        else:
            print()
    else:
        print(f"  \033[91m{failed}/{total} facade test(s) FAILED:\033[0m")
        for e in errors:
            print(f"    • {e}")
        if warned:
            print(f"  \033[93m{warned} warning(s)\033[0m")
    print(f"{'═' * 60}\n")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
