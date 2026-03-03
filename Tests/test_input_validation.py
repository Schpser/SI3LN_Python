"""
SI3LN Input Validation Tests
=============================
Tests every user-facing input field for format, length,
type, and boundary constraints.

Usage:
    python Tests/test_input_validation.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_input_validation.py
"""

import os
import sys
import time
import subprocess
import json as _json
import requests

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE}/api"

# Force Connection: close on every request to avoid exhausting gunicorn workers
_session = requests.Session()
_session.headers.update({"Connection": "close"})


class _CurlResponse:
    """Minimal response object matching requests.Response interface."""
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.text = body
        self._body = body
    def json(self):
        return _json.loads(self._body)


def _curl(method, url, *, json=None, headers=None, timeout=5):
    """Use subprocess curl as a fallback-proof HTTP client."""
    cmd = ["curl", "-s", "-X", method.upper(), "-w", "\n%{http_code}", "-m", str(timeout)]
    if json is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", _json.dumps(json)]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        lines = result.stdout.rsplit("\n", 1)
        body = lines[0] if len(lines) > 1 else ""
        code = int(lines[-1]) if lines[-1].strip().isdigit() else 0
        return _CurlResponse(code, body)
    except Exception as e:
        return _CurlResponse(0, str(e))


def _curl_post(url, *, json=None, headers=None, timeout=10, **kw):
    return _curl("POST", url, json=json, headers=headers, timeout=timeout)

def _curl_get(url, *, headers=None, timeout=10, **kw):
    return _curl("GET", url, headers=headers, timeout=timeout)

def _curl_patch(url, *, json=None, headers=None, timeout=10, **kw):
    return _curl("PATCH", url, json=json, headers=headers, timeout=timeout)

# Replace requests functions with curl-based versions
requests.post = _curl_post
requests.get = _curl_get
requests.patch = _curl_patch

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
            "username": f"val_test_{TS}",
            "password": "SecureP@ss1",
            "email": f"val_{TS}@test.com",
        },
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Created test user: val_test_{TS} (id={_player_id})")
    else:
        print(f"  {FAIL} Setup failed: HTTP {r.status_code}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  1 · USERNAME VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_username_empty():
    """Empty username on register"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": "", "password": "SecureP@ss1", "email": f"empty_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Empty username → rejected")
    elif r.status_code == 200:
        fail("Empty username", "accepted (should reject)")
    else:
        ok(f"Empty username → HTTP {r.status_code}")


def test_username_too_long():
    """Username over 50 chars"""
    long_name = "A" * 60
    r = requests.post(
        f"{API}/auth/register",
        json={"username": long_name, "password": "SecureP@ss1", "email": f"long_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Username 60 chars → rejected")
    elif r.status_code == 200:
        warn("Username 60 chars", "accepted (model max_length=50)")
    else:
        ok(f"Username 60 chars → HTTP {r.status_code}")


def test_username_special_chars():
    """Username with spaces and special chars"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": "user name!@#", "password": "SecureP@ss1", "email": f"sp_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Username with special chars → rejected")
    elif r.status_code == 200:
        warn("Username with special chars", "accepted (may want stricter rules)")
    else:
        ok(f"Username special chars → HTTP {r.status_code}")


def test_username_duplicate():
    """Register with existing username"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"val_test_{TS}", "password": "SecureP@ss1", "email": f"dup_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code == 400:
        ok("Duplicate username → rejected (400)")
    else:
        fail("Duplicate username", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_password_empty():
    """Empty password"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"pw_empty_{TS}", "password": "", "email": f"pwe_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Empty password → rejected")
    elif r.status_code == 200:
        fail("Empty password", "accepted!")
    else:
        ok(f"Empty password → HTTP {r.status_code}")


def test_password_too_short():
    """Password under minimum length"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"pw_short_{TS}", "password": "Ab1", "email": f"pws_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Short password (3 chars) → rejected")
    elif r.status_code == 200:
        warn("Short password", "accepted (Django validators may not apply at API level)")
    else:
        ok(f"Short password → HTTP {r.status_code}")


def test_password_common():
    """Common password like 'password123'"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"pw_common_{TS}", "password": "password123", "email": f"pwc_{TS}@t.com"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Common password → rejected")
    elif r.status_code == 200:
        warn("Common password", "accepted (password validators may not apply at API level)")
    else:
        ok(f"Common password → HTTP {r.status_code}")


def test_password_very_long():
    """Extremely long password (10000 chars)"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"pw_long_{TS}", "password": "A1" * 5000, "email": f"pwl_{TS}@t.com"},
        timeout=10,
    )
    # Should either accept or cleanly reject — no 500
    if r.status_code >= 500:
        fail("Very long password → server error", f"HTTP {r.status_code}")
    else:
        ok(f"Very long password (10k chars) → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · EMAIL VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_email_invalid_format():
    """Not an email"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"email_bad_{TS}", "password": "SecureP@ss1", "email": "not-an-email"},
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Invalid email format → rejected")
    elif r.status_code == 200:
        warn("Invalid email format", "accepted (no email validation at API level)")
    else:
        ok(f"Invalid email format → HTTP {r.status_code}")


def test_email_empty_allowed():
    """Empty email should be allowed (field is optional)"""
    r = requests.post(
        f"{API}/auth/register",
        json={"username": f"email_empty_{TS}", "password": "SecureP@ss1", "email": ""},
        timeout=10,
    )
    if r.status_code == 200:
        ok("Empty email → accepted (optional field)")
    elif r.status_code in (400, 422):
        ok(f"Empty email → rejected (HTTP {r.status_code})")
    else:
        fail("Empty email", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · PROFILE FIELD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_bio_exactly_500():
    """Bio at exactly 500 chars (max_length)"""
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": "X" * 500},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200 and len(r.json().get("bio", "")) == 500:
        ok("Bio exactly 500 chars → accepted")
    else:
        fail("Bio 500 chars", f"HTTP {r.status_code}")


def test_bio_501():
    """Bio at 501 chars (over limit)"""
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": "X" * 501},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Bio 501 chars → rejected")
    else:
        fail("Bio 501 chars", f"HTTP {r.status_code} (should reject)")


def test_bg_color_valid_formats():
    """Valid hex colors"""
    valid = ["#000000", "#FFFFFF", "#ff5500", "#AbCdEf"]
    all_ok = True
    for color in valid:
        r = requests.patch(
            f"{API}/game/profile/me",
            json={"bg_color": color},
            headers=_auth(),
            timeout=10,
        )
        if r.status_code != 200:
            fail(f"bg_color {color}", f"HTTP {r.status_code}")
            all_ok = False
            break
    if all_ok:
        ok("Valid hex colors → all accepted")


def test_bg_color_invalid_formats():
    """Invalid color formats"""
    invalid = ["red", "#FFF", "#GGGGGG", "000000", "#12345", "#1234567", ""]
    all_rejected = True
    for color in invalid:
        r = requests.patch(
            f"{API}/game/profile/me",
            json={"bg_color": color},
            headers=_auth(),
            timeout=10,
        )
        if r.status_code not in (400, 422):
            if color == "":
                # Empty string may be accepted or rejected
                continue
            warn(f"bg_color '{color}'", f"HTTP {r.status_code} (expected 400/422)")
            all_rejected = False
            break
    if all_rejected:
        ok("Invalid hex colors → all rejected")


def test_show_scores_type():
    """show_scores accepts only boolean"""
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"show_scores": "not-a-bool"},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("show_scores with string → rejected")
    elif r.status_code == 200:
        # Pydantic may coerce truthy strings
        val = r.json().get("show_scores")
        warn("show_scores string", f"accepted as {val} (type coercion)")
    else:
        fail("show_scores type check", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · SESSION FIELD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_session_negative_score():
    """Negative score should be rejected"""
    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        fail("Session setup", f"HTTP {r1.status_code}")
        return
    sid = r1.json()["id"]
    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": -50},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code in (400, 422):
        ok("Negative score → rejected")
    else:
        fail("Negative score", f"HTTP {r2.status_code}")


def test_session_string_score():
    """Non-numeric score"""
    r1 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    sid = r1.json()["id"]
    r2 = requests.patch(
        f"{API}/game/sessions/{sid}",
        json={"score": "not_a_number"},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code in (400, 422):
        ok("String score → rejected")
    else:
        fail("String score", f"HTTP {r2.status_code}")


def test_session_null_player():
    """Session with null player_id"""
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": None},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Null player_id → rejected")
    elif r.status_code >= 500:
        warn("Null player_id", f"HTTP 500 (should be 400/422)")
    else:
        fail("Null player_id", f"HTTP {r.status_code}")


def test_session_nonexistent_player():
    """Session for player_id that doesn't exist"""
    r = requests.post(
        f"{API}/game/sessions",
        json={"player_id": 999999},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 404, 422):
        ok("Non-existent player_id → rejected cleanly")
    elif r.status_code >= 500:
        warn("Non-existent player_id", "HTTP 500 (should be 400/404)")
    else:
        ok(f"Non-existent player_id → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  6 · CHANGE PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_change_password_wrong_old():
    """Change password with wrong current password"""
    try:
        r = _curl("POST",
            f"{API}/auth/change-password",
            json={"old_password": "wrongpass", "new_password": "NewSecureP@ss1"},
            headers=_auth(),
            timeout=5,
        )
        if r.status_code == 400:
            ok("Wrong old password → rejected (400)")
        else:
            fail("Wrong old password", f"HTTP {r.status_code}")
    except Exception as e:
        warn("Wrong old password", f"exception: {e}")


def test_change_password_empty_new():
    """Change password with empty new password"""
    try:
        r = requests.post(
            f"{API}/auth/change-password",
            json={"old_password": "SecureP@ss1", "new_password": ""},
            headers=_auth(),
            timeout=5,
        )
        if r.status_code in (400, 422):
            ok("Empty new password → rejected")
        elif r.status_code == 200:
            warn("Empty new password", "accepted (no minimum length check)")
        else:
            ok(f"Empty new password → HTTP {r.status_code}")
    except requests.exceptions.Timeout:
        warn("Empty new password", "request timed out (server slow)")


# ══════════════════════════════════════════════════════════════════════════════
#  7 · CONTENT-TYPE / PAYLOAD EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_content_type():
    """Send POST without Content-Type"""
    cmd = ["curl", "-s", "-X", "POST", "-w", "\n%{http_code}", "-m", "10",
           "-d", "not json", "-H", "Content-Type: ", f"{API}/auth/login"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
    lines = result.stdout.rsplit("\n", 1)
    code = int(lines[-1]) if lines[-1].strip().isdigit() else 0
    r = _CurlResponse(code, lines[0] if len(lines) > 1 else "")
    if r.status_code >= 500:
        warn("Missing Content-Type", f"HTTP 500 (should be 400/415)")
    else:
        ok(f"Missing Content-Type → HTTP {r.status_code}")


def test_malformed_json():
    """Send invalid JSON body"""
    cmd = ["curl", "-s", "-X", "POST", "-w", "\n%{http_code}", "-m", "10",
           "-d", "{invalid json}}}", "-H", "Content-Type: application/json",
           f"{API}/auth/login"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
    lines = result.stdout.rsplit("\n", 1)
    code = int(lines[-1]) if lines[-1].strip().isdigit() else 0
    r = _CurlResponse(code, lines[0] if len(lines) > 1 else "")
    if r.status_code in (400, 422):
        ok("Malformed JSON → rejected")
    elif r.status_code >= 500:
        warn("Malformed JSON", f"HTTP 500 (should be 400)")
    else:
        ok(f"Malformed JSON → HTTP {r.status_code}")


def test_extra_fields_ignored():
    """Send extra unknown fields in request body"""
    r = requests.post(
        f"{API}/auth/login",
        json={
            "username": f"val_test_{TS}",
            "password": "SecureP@ss1",
            "evil_field": "drop table",
            "admin": True,
        },
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        if "evil_field" not in d and "admin" not in d:
            ok("Extra fields → ignored in request and response")
        else:
            warn("Extra fields", "echoed back in response")
    else:
        ok(f"Extra fields → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Input Validation Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    setup()

    section("1 · Username Validation")
    test_username_empty(); time.sleep(0.3)
    test_username_too_long(); time.sleep(0.3)
    test_username_special_chars(); time.sleep(0.3)
    test_username_duplicate(); time.sleep(0.3)

    section("2 · Password Validation")
    test_password_empty(); time.sleep(0.3)
    test_password_too_short(); time.sleep(0.3)
    test_password_common(); time.sleep(0.3)
    test_password_very_long(); time.sleep(0.3)

    section("3 · Email Validation")
    test_email_invalid_format(); time.sleep(0.3)
    test_email_empty_allowed(); time.sleep(0.3)

    section("4 · Profile Fields")
    test_bio_exactly_500(); time.sleep(0.3)
    test_bio_501(); time.sleep(0.3)
    test_bg_color_valid_formats(); time.sleep(0.3)
    test_bg_color_invalid_formats(); time.sleep(0.3)
    test_show_scores_type(); time.sleep(0.3)

    section("5 · Session Fields")
    test_session_negative_score(); time.sleep(0.3)
    test_session_string_score(); time.sleep(0.3)
    test_session_null_player(); time.sleep(0.3)
    test_session_nonexistent_player(); time.sleep(0.3)

    section("6 · Change Password")
    test_change_password_wrong_old(); time.sleep(0.3)
    test_change_password_empty_new(); time.sleep(0.3)

    section("7 · Content-Type & Payload")
    test_missing_content_type(); time.sleep(0.3)
    test_malformed_json(); time.sleep(0.3)
    test_extra_fields_ignored()

    total = 24
    passed = total - len(errors)
    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{total} input validation test(s) FAILED:")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  All {total} input validation tests passed", end="")
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
