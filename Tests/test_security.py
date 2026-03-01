"""
SI3LN Security Tests
====================
Tests SQL injection, JWT attacks, header hardening, path traversal,
brute-force protection, XSS vectors, and response sanitisation.

Usage:
    python Tests/test_security.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_security.py
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


def _auth():
    return {"Authorization": f"Bearer {_token}"}


def setup():
    global _token, _player_id
    section("Setup — Create test user")
    r = requests.post(
        f"{API}/auth/register",
        json={
            "username": f"sec_test_{TS}",
            "password": "SecureP@ss1",
            "email": f"sec_{TS}@test.com",
        },
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        _token = d["token"]
        _player_id = d["player_id"]
        print(f"  {INFO} Created test user: sec_test_{TS} (id={_player_id})")
    else:
        print(f"  {FAIL} Setup failed: HTTP {r.status_code}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  1 · SQL INJECTION
# ══════════════════════════════════════════════════════════════════════════════

def test_sql_injection_login():
    """Try SQL injection in login username"""
    payloads = [
        "' OR '1'='1",
        "admin'--",
        "'; DROP TABLE game_player;--",
        "\" OR \"\"=\"",
        "1; SELECT * FROM auth_user--",
    ]
    all_safe = True
    for payload in payloads:
        r = requests.post(
            f"{API}/auth/login",
            json={"username": payload, "password": "anything"},
            timeout=10,
        )
        if r.status_code == 200 and r.json().get("token"):
            fail(f"SQL injection login", f"Payload succeeded: {payload[:30]}")
            all_safe = False
            break
    if all_safe:
        ok("SQL injection in login → all payloads rejected")


def test_sql_injection_register():
    """Try SQL injection in registration"""
    r = requests.post(
        f"{API}/auth/register",
        json={
            "username": "'; DROP TABLE auth_user;--",
            "password": "TestP@ss1",
            "email": "sql@test.com",
        },
        timeout=10,
    )
    if r.status_code in (200, 400, 422):
        ok("SQL injection in register → handled safely")
    elif r.status_code >= 500:
        fail("SQL injection in register", f"Server error (HTTP {r.status_code})")
    else:
        ok("SQL injection in register → handled safely")


def test_sql_injection_search_params():
    """Try SQL injection in query parameters"""
    payloads = [
        "1 OR 1=1",
        "1; DROP TABLE game_session;--",
        "1 UNION SELECT * FROM auth_user--",
    ]
    all_safe = True
    for payload in payloads:
        r = requests.get(
            f"{API}/game/leaderboard",
            params={"world_id": payload, "limit": "10"},
            timeout=10,
        )
        # Should either return valid JSON or a clean error — never 500
        if r.status_code >= 500:
            fail(f"SQL injection in query params", f"HTTP 500 with: {payload[:30]}")
            all_safe = False
            break
    if all_safe:
        ok("SQL injection in query params → all payloads safe")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · JWT ATTACKS
# ══════════════════════════════════════════════════════════════════════════════

def test_jwt_tampered_token():
    """Send a manually tampered JWT"""
    if not _token:
        fail("JWT tampered", "no token")
        return
    # Flip last char to corrupt signature
    bad = _token[:-1] + ("A" if _token[-1] != "A" else "B")
    r = requests.get(
        f"{API}/game/players",
        headers={"Authorization": f"Bearer {bad}"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Tampered JWT → rejected")
    else:
        fail("Tampered JWT", f"HTTP {r.status_code} (expected 401/403)")


def test_jwt_none_algorithm():
    """Send a JWT with 'none' algorithm (classic bypass attempt)"""
    import base64

    # Build a fake token with alg: none
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"user_id": 1, "username": "admin", "exp": int(time.time()) + 3600}).encode()
    ).rstrip(b"=").decode()
    fake_token = f"{header}.{payload}."

    r = requests.get(
        f"{API}/game/players",
        headers={"Authorization": f"Bearer {fake_token}"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("JWT alg:none → rejected")
    else:
        fail("JWT alg:none bypass", f"HTTP {r.status_code}")


def test_jwt_empty_token():
    """Send empty bearer token"""
    r = requests.get(
        f"{API}/game/players",
        headers={"Authorization": "Bearer "},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Empty bearer token → rejected")
    else:
        fail("Empty bearer token", f"HTTP {r.status_code}")


def test_jwt_bearer_without_token():
    """Send Authorization header without Bearer prefix"""
    r = requests.get(
        f"{API}/game/players",
        headers={"Authorization": "NotBearer sometoken"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Invalid auth scheme → rejected")
    else:
        fail("Invalid auth scheme", f"HTTP {r.status_code}")


def test_jwt_random_string():
    """Send a random non-JWT string"""
    r = requests.get(
        f"{API}/game/players",
        headers={"Authorization": "Bearer this-is-not-a-jwt-at-all"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Random string as JWT → rejected")
    else:
        fail("Random string JWT", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · SECURITY HEADERS
# ══════════════════════════════════════════════════════════════════════════════

def test_security_headers():
    """Check for essential security headers on API responses"""
    r = requests.get(f"{API}/game/stats", timeout=10)
    h = r.headers

    checks = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": None,  # any value is fine
        "Referrer-Policy": None,
    }
    for header, expected in checks.items():
        val = h.get(header, "")
        if not val:
            fail(f"Security header {header}", "missing")
        elif expected and val.lower() != expected.lower():
            warn(f"Security header {header}", f"expected '{expected}', got '{val}'")
        else:
            ok(f"Security header {header}: {val}")


def test_no_server_version_leak():
    """Server header should not reveal version details"""
    r = requests.get(f"{API}/game/stats", timeout=10)
    server = r.headers.get("Server", "")
    if server:
        # Warn if it's too specific (contains version numbers)
        import re
        if re.search(r'\d+\.\d+', server):
            warn("Server header leaks version", f"Server: {server}")
        else:
            ok(f"Server header present but no version: {server}")
    else:
        ok("No Server header exposed")


def test_no_sensitive_fields_in_response():
    """Verify API responses don't contain password or secret fields"""
    if not _token:
        fail("Sensitive fields check", "no token")
        return
    r = requests.get(f"{API}/auth/me", headers=_auth(), timeout=10)
    if r.status_code == 200:
        body = json.dumps(r.json()).lower()
        bad_fields = ["password", "password_hash", "secret", "private_key"]
        found = [f for f in bad_fields if f in body]
        if found:
            fail("Sensitive fields in /auth/me", f"Found: {found}")
        else:
            ok("No sensitive fields in /auth/me response")
    else:
        fail("Sensitive fields check", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · PATH TRAVERSAL
# ══════════════════════════════════════════════════════════════════════════════

def test_path_traversal_avatar():
    """Try uploading avatar with path traversal filename"""
    if not _token:
        fail("Path traversal avatar", "no token")
        return
    # Create a tiny valid PNG
    png = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
        b'\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00'
        b'\x00\x00\x00IEND\xaeB`\x82'
    )
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("../../../etc/passwd.png", png, "image/png")},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (200, 400):
        if r.status_code == 200:
            url = r.json().get("avatar_url", "")
            if "../" in url or "etc" in url:
                fail("Path traversal avatar", f"Traversal path in URL: {url}")
            else:
                ok("Path traversal avatar filename → sanitised by Django")
        else:
            ok("Path traversal avatar filename → rejected")
    else:
        fail("Path traversal avatar", f"HTTP {r.status_code}")


def test_path_traversal_api_routes():
    """Try accessing parent directories via API path"""
    traversal_paths = [
        f"{BASE}/../../../etc/passwd",
        f"{API}/../../admin/",
        f"{API}/game/players/../../auth/me",
    ]
    for path in traversal_paths:
        try:
            r = requests.get(path, timeout=10, allow_redirects=False)
            if r.status_code == 200 and "root:" in r.text:
                fail("Path traversal in URL", f"File leak at {path}")
                return
        except requests.exceptions.RequestException:
            pass
    ok("Path traversal in URL routes → no file leaks")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · XSS VECTORS
# ══════════════════════════════════════════════════════════════════════════════

def test_xss_in_username():
    """Try XSS payload in username during registration"""
    xss = '<script>alert("xss")</script>'
    r = requests.post(
        f"{API}/auth/register",
        json={"username": xss, "password": "SecureP@ss1", "email": f"xss_{TS}@test.com"},
        timeout=10,
    )
    if r.status_code == 200:
        returned = r.json().get("username", "")
        if "<script>" in returned:
            warn("XSS in username", "Script tags stored in username")
        else:
            ok("XSS in username → sanitised/escaped")
    elif r.status_code in (400, 422):
        ok("XSS in username → rejected by server")
    else:
        ok(f"XSS in username → HTTP {r.status_code}")


def test_xss_in_profile_fields():
    """Try XSS in profile bio (should be sanitised now)"""
    if not _token:
        fail("XSS in profile", "no token")
        return
    xss_payloads = [
        '<img src=x onerror=alert(1)>',
        '<svg/onload=alert(1)>',
        'javascript:alert(1)',
        '<iframe src="evil.com"></iframe>',
    ]
    all_clean = True
    for xss in xss_payloads:
        r = requests.patch(
            f"{API}/game/profile/me",
            json={"bio": xss},
            headers=_auth(),
            timeout=10,
        )
        if r.status_code == 200:
            bio = r.json().get("bio", "")
            if "<" in bio and ">" in bio:
                fail("XSS in bio", f"HTML tags stored: {bio[:50]}")
                all_clean = False
                break
    if all_clean:
        ok("XSS payloads in bio → all sanitised")


# ══════════════════════════════════════════════════════════════════════════════
#  6 · BRUTE FORCE PROTECTION
# ══════════════════════════════════════════════════════════════════════════════

def test_brute_force_login():
    """Rapidly send many wrong login attempts"""
    start = time.time()
    blocked = False
    for i in range(20):
        r = requests.post(
            f"{API}/auth/login",
            json={"username": f"sec_test_{TS}", "password": f"wrong_{i}"},
            timeout=5,
        )
        if r.status_code == 429:
            blocked = True
            break
    elapsed = time.time() - start

    if blocked:
        ok(f"Brute force login → rate-limited after {i + 1} attempts ({elapsed:.1f}s)")
    else:
        warn("Brute force login", f"20 rapid attempts accepted ({elapsed:.1f}s) — no rate limiting on auth endpoint")


def test_brute_force_register():
    """Rapidly send many registration attempts"""
    blocked = False
    for i in range(20):
        r = requests.post(
            f"{API}/auth/register",
            json={
                "username": f"bf_test_{TS}_{i}",
                "password": "SecureP@ss1",
                "email": f"bf_{TS}_{i}@test.com",
            },
            timeout=5,
        )
        if r.status_code == 429:
            blocked = True
            break

    if blocked:
        ok(f"Brute force register → rate-limited after {i + 1} attempts")
    else:
        warn("Brute force register", "20 rapid registrations accepted — no rate limiting")


# ══════════════════════════════════════════════════════════════════════════════
#  7 · RESPONSE CONTENT SECURITY
# ══════════════════════════════════════════════════════════════════════════════

def test_error_responses_no_stack_trace():
    """Ensure error responses don't leak stack traces"""
    r = requests.get(f"{API}/game/players/not_a_number", timeout=10)
    body = r.text.lower()
    leaky = ["traceback", "file \"", "line ", "exception", "django."]
    found = [w for w in leaky if w in body]
    if found:
        fail("Stack trace in error", f"Found: {found}")
    else:
        ok("Error response hides stack trace")


def test_404_doesnt_enumerate():
    """Ensure 404 doesn't reveal internal details"""
    r = requests.get(f"{API}/game/secret-admin-panel", timeout=10)
    body = r.text.lower()
    if "traceback" in body or "django" in body:
        fail("404 leaks internal info", r.text[:100])
    else:
        ok("404 response is clean (no internal details)")


def test_json_content_type():
    """API must always return application/json"""
    endpoints = [
        f"{API}/game/stats",
        f"{API}/game/leaderboard",
    ]
    all_json = True
    for url in endpoints:
        r = requests.get(url, timeout=10)
        ct = r.headers.get("Content-Type", "")
        if "application/json" not in ct:
            fail("Content-Type", f"{url} returned {ct}")
            all_json = False
    if all_json:
        ok("All public endpoints return application/json")


# ══════════════════════════════════════════════════════════════════════════════
#  8 · MISC SECURITY CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def test_cors_preflight():
    """Proper CORS preflight response"""
    r = requests.options(
        f"{API}/game/stats",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
        timeout=10,
    )
    allow_origin = r.headers.get("Access-Control-Allow-Origin", "")
    if allow_origin == "*":
        warn("CORS allows all origins", "Access-Control-Allow-Origin: * in production is risky")
    elif "evil.example.com" in allow_origin:
        fail("CORS allows evil origin", allow_origin)
    else:
        ok(f"CORS preflight → origin not reflected for evil domain")


def test_http_methods():
    """Ensure unexpected HTTP methods are rejected"""
    safe = True
    for method in ["TRACE", "CONNECT"]:
        try:
            r = requests.request(method, f"{API}/game/stats", timeout=10)
            if r.status_code == 200:
                fail(f"HTTP {method} allowed", "should be rejected")
                safe = False
        except requests.exceptions.RequestException:
            pass  # connection error is fine — method blocked
    if safe:
        ok("TRACE/CONNECT methods → rejected")


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Security Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    setup()

    section("1 · SQL Injection")
    test_sql_injection_login()
    test_sql_injection_register()
    test_sql_injection_search_params()

    section("2 · JWT Attacks")
    test_jwt_tampered_token()
    test_jwt_none_algorithm()
    test_jwt_empty_token()
    test_jwt_bearer_without_token()
    test_jwt_random_string()

    section("3 · Security Headers")
    test_security_headers()
    test_no_server_version_leak()
    test_no_sensitive_fields_in_response()

    section("4 · Path Traversal")
    test_path_traversal_avatar()
    test_path_traversal_api_routes()

    section("5 · XSS Vectors")
    test_xss_in_username()
    test_xss_in_profile_fields()

    section("6 · Brute Force Protection")
    test_brute_force_login()
    test_brute_force_register()

    section("7 · Response Content Security")
    test_error_responses_no_stack_trace()
    test_404_doesnt_enumerate()
    test_json_content_type()

    section("8 · Misc Security")
    test_cors_preflight()
    test_http_methods()

    total = 22
    passed = total - len(errors)
    print(f"\n{'═' * 60}")
    if errors:
        print(f"  {len(errors)}/{total} security test(s) FAILED:")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"  All {total} security tests passed", end="")
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
