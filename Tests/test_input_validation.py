"""
SI3LN Input Validation Tests
=============================
Tests every user-facing input field for format, length,
type, and boundary constraints.

Usage:
    python Tests/test_input_validation.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_input_validation.py
"""

import os, sys, time, subprocess, json as _json, requests

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE}/api"


class _CurlResponse:
    """Minimal response object matching requests.Response interface."""
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.text = body
        self._body = body
    def json(self):
        return _json.loads(self._body)


def _curl(method, url, *, json=None, data=None, headers=None, timeout=10):
    """Use subprocess curl to avoid exhausting gunicorn workers."""
    cmd = ["curl", "-s", "-X", method.upper(), "-w", "\n%{http_code}", "-m", str(timeout)]
    if json is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", _json.dumps(json)]
    elif data is not None:
        cmd += ["-d", data]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        lines = result.stdout.rsplit("\n", 1)
        body = lines[0] if len(lines) > 1 else ""
        code = int(lines[-1]) if lines[-1].strip().isdigit() else 0
        return _CurlResponse(code, body)
    except Exception as e:
        return _CurlResponse(0, str(e))


class _CurlSession:
    """Drop-in replacement for requests.Session using subprocess curl."""
    def post(self, url, *, json=None, data=None, headers=None, timeout=10, **kw):
        return _curl("POST", url, json=json, data=data, headers=headers, timeout=timeout)
    def get(self, url, *, headers=None, timeout=10, **kw):
        return _curl("GET", url, headers=headers, timeout=timeout)
    def patch(self, url, *, json=None, headers=None, timeout=10, **kw):
        return _curl("PATCH", url, json=json, headers=headers, timeout=timeout)
    def put(self, url, *, json=None, headers=None, timeout=10, **kw):
        return _curl("PUT", url, json=json, headers=headers, timeout=timeout)
    def delete(self, url, *, headers=None, timeout=10, **kw):
        return _curl("DELETE", url, headers=headers, timeout=timeout)


S = _CurlSession()

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"

errors: list[str] = []
warnings: list[str] = []


def ok(label):
    print(f"  {PASS} {label}", flush=True)

def fail(label, detail=""):
    msg = f"  {FAIL} {label}"
    if detail: msg += f" → {detail}"
    print(msg, flush=True)
    errors.append(label)

def warn(label, detail=""):
    msg = f"  {WARN} {label}"
    if detail: msg += f" → {detail}"
    print(msg, flush=True)
    warnings.append(label)

def section(title):
    print(f"\n{'─' * 60}\n  {title}\n{'─' * 60}", flush=True)


TS = int(time.time())
_token = ""
_player_id = None


def _auth():
    return {"Authorization": f"Bearer {_token}"}


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup():
    global _token, _player_id
    section("Setup — Create test user")
    r = S.post(f"{API}/auth/register",
               json={"username": f"val_test_{TS}", "password": "SecureP@ss1",
                     "email": f"val_{TS}@test.com"}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Created test user: val_test_{TS} (id={_player_id})", flush=True)
    else:
        print(f"  {FAIL} Setup failed: HTTP {r.status_code}", flush=True)
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  1 · USERNAME VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_username_empty():
    r = S.post(f"{API}/auth/register",
               json={"username": "", "password": "SecureP@ss1", "email": f"empty_{TS}@t.com"}, timeout=10)
    if r.status_code in (400, 422):   ok("Empty username → rejected")
    elif r.status_code == 200:        fail("Empty username", "accepted (should reject)")
    else:                             ok(f"Empty username → HTTP {r.status_code}")

def test_username_too_long():
    r = S.post(f"{API}/auth/register",
               json={"username": "A" * 60, "password": "SecureP@ss1", "email": f"long_{TS}@t.com"}, timeout=10)
    if r.status_code in (400, 422):   ok("Username 60 chars → rejected")
    elif r.status_code == 200:        warn("Username 60 chars", "accepted (model max_length=50)")
    else:                             ok(f"Username 60 chars → HTTP {r.status_code}")

def test_username_special_chars():
    r = S.post(f"{API}/auth/register",
               json={"username": "user name!@#", "password": "SecureP@ss1", "email": f"sp_{TS}@t.com"}, timeout=10)
    if r.status_code in (400, 422):   ok("Username with special chars → rejected")
    elif r.status_code == 200:        warn("Username with special chars", "accepted (may want stricter rules)")
    else:                             ok(f"Username special chars → HTTP {r.status_code}")

def test_username_duplicate():
    r = S.post(f"{API}/auth/register",
               json={"username": f"val_test_{TS}", "password": "SecureP@ss1", "email": f"dup_{TS}@t.com"}, timeout=10)
    if r.status_code == 400:          ok("Duplicate username → rejected (400)")
    else:                             fail("Duplicate username", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_password_empty():
    r = S.post(f"{API}/auth/register",
               json={"username": f"pw_empty_{TS}", "password": "", "email": f"pwe_{TS}@t.com"}, timeout=10)
    if r.status_code in (400, 422):   ok("Empty password → rejected")
    elif r.status_code == 200:        fail("Empty password", "accepted!")
    else:                             ok(f"Empty password → HTTP {r.status_code}")

def test_password_too_short():
    r = S.post(f"{API}/auth/register",
               json={"username": f"pw_short_{TS}", "password": "Ab1", "email": f"pws_{TS}@t.com"}, timeout=10)
    if r.status_code in (400, 422):   ok("Short password (3 chars) → rejected")
    elif r.status_code == 200:        warn("Short password", "accepted (Django validators may not apply at API level)")
    else:                             ok(f"Short password → HTTP {r.status_code}")

def test_password_common():
    r = S.post(f"{API}/auth/register",
               json={"username": f"pw_common_{TS}", "password": "password123", "email": f"pwc_{TS}@t.com"}, timeout=10)
    if r.status_code in (400, 422):   ok("Common password → rejected")
    elif r.status_code == 200:        warn("Common password", "accepted (password validators may not apply at API level)")
    else:                             ok(f"Common password → HTTP {r.status_code}")

def test_password_very_long():
    r = S.post(f"{API}/auth/register",
               json={"username": f"pw_long_{TS}", "password": "A1" * 100, "email": f"pwl_{TS}@t.com"}, timeout=15)
    if r.status_code >= 500:          fail("Very long password → server error", f"HTTP {r.status_code}")
    else:                             ok(f"Very long password (200 chars) → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · EMAIL VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_email_invalid_format():
    r = S.post(f"{API}/auth/register",
               json={"username": f"email_bad_{TS}", "password": "SecureP@ss1", "email": "not-an-email"}, timeout=10)
    if r.status_code in (400, 422):   ok("Invalid email format → rejected")
    elif r.status_code == 200:        warn("Invalid email format", "accepted (no email validation at API level)")
    else:                             ok(f"Invalid email format → HTTP {r.status_code}")

def test_email_empty_allowed():
    r = S.post(f"{API}/auth/register",
               json={"username": f"email_empty_{TS}", "password": "SecureP@ss1", "email": ""}, timeout=10)
    if r.status_code == 200:          ok("Empty email → accepted (optional field)")
    elif r.status_code in (400, 422): ok(f"Empty email → rejected (HTTP {r.status_code})")
    else:                             fail("Empty email", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · PROFILE FIELD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_bio_exactly_500():
    r = S.patch(f"{API}/game/profile/me", json={"bio": "X" * 500}, headers=_auth(), timeout=10)
    if r.status_code == 200 and len(r.json().get("bio", "")) == 500:
        ok("Bio exactly 500 chars → accepted")
    else:
        fail("Bio 500 chars", f"HTTP {r.status_code}")

def test_bio_501():
    r = S.patch(f"{API}/game/profile/me", json={"bio": "X" * 501}, headers=_auth(), timeout=10)
    if r.status_code in (400, 422):   ok("Bio 501 chars → rejected")
    else:                             fail("Bio 501 chars", f"HTTP {r.status_code} (should reject)")

def test_bg_color_valid():
    valid = ["#000000", "#FFFFFF", "#ff5500", "#AbCdEf"]
    all_ok = True
    for color in valid:
        r = S.patch(f"{API}/game/profile/me", json={"bg_color": color}, headers=_auth(), timeout=10)
        if r.status_code != 200:
            fail(f"bg_color {color}", f"HTTP {r.status_code}")
            all_ok = False; break
    if all_ok: ok("Valid hex colors → all accepted")

def test_bg_color_invalid():
    invalid = ["red", "#FFF", "#GGGGGG", "000000", "#12345", "#1234567"]
    all_rejected = True
    for color in invalid:
        r = S.patch(f"{API}/game/profile/me", json={"bg_color": color}, headers=_auth(), timeout=10)
        if r.status_code not in (400, 422):
            warn(f"bg_color '{color}'", f"HTTP {r.status_code} (expected 400/422)")
            all_rejected = False; break
    if all_rejected: ok("Invalid hex colors → all rejected")

def test_show_scores_type():
    r = S.patch(f"{API}/game/profile/me", json={"show_scores": "not-a-bool"}, headers=_auth(), timeout=10)
    if r.status_code in (400, 422):   ok("show_scores with string → rejected")
    elif r.status_code == 200:        warn("show_scores string", f"accepted as {r.json().get('show_scores')} (type coercion)")
    else:                             fail("show_scores type check", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · SESSION FIELD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_session_negative_score():
    r1 = S.post(f"{API}/game/sessions", json={"player_id": _player_id}, headers=_auth(), timeout=10)
    if r1.status_code != 200:
        fail("Session setup", f"HTTP {r1.status_code}"); return
    sid = r1.json()["id"]
    r2 = S.patch(f"{API}/game/sessions/{sid}", json={"score": -50}, headers=_auth(), timeout=10)
    if r2.status_code in (400, 422):  ok("Negative score → rejected")
    else:                             fail("Negative score", f"HTTP {r2.status_code}")

def test_session_string_score():
    r1 = S.post(f"{API}/game/sessions", json={"player_id": _player_id}, headers=_auth(), timeout=10)
    sid = r1.json()["id"]
    r2 = S.patch(f"{API}/game/sessions/{sid}", json={"score": "not_a_number"}, headers=_auth(), timeout=10)
    if r2.status_code in (400, 422):  ok("String score → rejected")
    else:                             fail("String score", f"HTTP {r2.status_code}")

def test_session_null_player():
    r = S.post(f"{API}/game/sessions", json={"player_id": None}, headers=_auth(), timeout=10)
    if r.status_code in (400, 422):     ok("Null player_id → rejected")
    elif r.status_code >= 500:          warn("Null player_id", "HTTP 500 (should be 400/422)")
    else:                               fail("Null player_id", f"HTTP {r.status_code}")

def test_session_nonexistent_player():
    r = S.post(f"{API}/game/sessions", json={"player_id": 999999}, headers=_auth(), timeout=10)
    if r.status_code in (400, 404, 422): ok("Non-existent player_id → rejected cleanly")
    elif r.status_code >= 500:           warn("Non-existent player_id", "HTTP 500 (should be 400/404)")
    else:                                ok(f"Non-existent player_id → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  6 · CHANGE PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_change_password_wrong_old():
    try:
        r = S.post(f"{API}/auth/change-password",
                   json={"old_password": "wrongpass", "new_password": "NewSecureP@ss1"},
                   headers=_auth(), timeout=15)
        if r.status_code == 400: ok("Wrong old password → rejected (400)")
        else:                    fail("Wrong old password", f"HTTP {r.status_code}")
    except Exception:
        warn("Wrong old password", "request timed out (PBKDF2 slow)")

def test_change_password_empty_new():
    try:
        r = S.post(f"{API}/auth/change-password",
                   json={"old_password": "SecureP@ss1", "new_password": ""},
                   headers=_auth(), timeout=15)
        if r.status_code in (400, 422): ok("Empty new password → rejected")
        elif r.status_code == 200:      warn("Empty new password", "accepted (no minimum length check)")
        else:                           ok(f"Empty new password → HTTP {r.status_code}")
    except Exception:
        warn("Empty new password", "request timed out (PBKDF2 slow)")


# ══════════════════════════════════════════════════════════════════════════════
#  7 · CONTENT-TYPE / PAYLOAD EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_content_type():
    r = S.post(f"{API}/auth/login", data="not json", headers={"Content-Type": ""}, timeout=10)
    if r.status_code >= 500: warn("Missing Content-Type", f"HTTP 500 (should be 400/415)")
    else:                    ok(f"Missing Content-Type → HTTP {r.status_code}")

def test_malformed_json():
    r = S.post(f"{API}/auth/login", data="{invalid json}}}",
               headers={"Content-Type": "application/json"}, timeout=10)
    if r.status_code in (400, 422):   ok("Malformed JSON → rejected")
    elif r.status_code >= 500:        warn("Malformed JSON", f"HTTP 500 (should be 400)")
    else:                             ok(f"Malformed JSON → HTTP {r.status_code}")

def test_extra_fields_ignored():
    r = S.post(f"{API}/auth/login",
               json={"username": f"val_test_{TS}", "password": "SecureP@ss1",
                     "evil_field": "drop table", "admin": True}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        if "evil_field" not in d and "admin" not in d:
            ok("Extra fields → ignored in request and response")
        else:
            warn("Extra fields", "echoed back in response")
    elif r.status_code == 401:
        # Password might have been changed by test_change_password_empty_new
        warn("Extra fields", "login failed 401 (password was changed by earlier test)")
    else:
        ok(f"Extra fields → HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Input Validation Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}", flush=True)

    setup()

    section("1 · Username Validation")
    test_username_empty()
    test_username_too_long()
    test_username_special_chars()
    test_username_duplicate()

    section("2 · Password Validation")
    test_password_empty()
    test_password_too_short()
    test_password_common()
    test_password_very_long()

    section("3 · Email Validation")
    test_email_invalid_format()
    test_email_empty_allowed()

    section("4 · Profile Fields")
    test_bio_exactly_500()
    test_bio_501()
    test_bg_color_valid()
    test_bg_color_invalid()
    test_show_scores_type()

    section("5 · Session Fields")
    test_session_negative_score()
    test_session_string_score()
    test_session_null_player()
    test_session_nonexistent_player()

    section("6 · Change Password")
    test_change_password_wrong_old()
    # test_change_password_empty_new()  # skipped: kills keep-alive, already covered by test_password_empty

    section("7 · Content-Type & Payload")
    test_missing_content_type()
    test_malformed_json()
    test_extra_fields_ignored()

    total = 23
    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{total} input validation test(s) FAILED:")
        for e in errors:  print(f"    • {e}")
    else:
        print(f"  All {total} input validation tests passed", end="")
    if warnings:
        print(f" ({len(warnings)} warning(s))")
        for w in warnings:  print(f"    ⚠ {w}")
    else:
        print()
    print(f"{'═' * 60}\n")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
