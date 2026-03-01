"""
SI3LN Profile & Avatar Tests
==============================
Tests profile CRUD operations, avatar upload, bio, settings.

Usage:
    python Tests/test_profile.py
    SI3LN_API_URL=http://localhost:8000 python Tests/test_profile.py
"""

import os
import sys
import time
import json
import tempfile
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
    "username": f"profile_test_{TS}",
    "password": "ProfilePass123!",
    "email": f"profile_{TS}@test.com",
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
        print(f"  {INFO} Created test user: {TEST_USER['username']} (id={_player_id})")
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
            print(f"  {FAIL} Auth failed — profile tests will be limited")


# ══════════════════════════════════════════════════════════════════════════════
#  1 · PROFILE READ
# ══════════════════════════════════════════════════════════════════════════════

def test_get_profile():
    """GET /api/game/profile/me — read own profile"""
    if not _token:
        fail("GET profile", "no token")
        return
    r = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    if r.status_code == 200:
        d = r.json()
        required = [
            "id", "username", "total_score", "games_played", "highest_level",
            "bio", "bg_color", "show_scores", "achievements_count",
        ]
        missing = [k for k in required if k not in d]
        if missing:
            fail("GET profile", f"Missing fields: {missing}")
        else:
            ok("GET /game/profile/me (all fields present)")
    else:
        fail("GET profile", f"HTTP {r.status_code}")


def test_profile_defaults():
    """New profile has sensible defaults"""
    if not _token:
        fail("Profile defaults", "no token")
        return
    r = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    if r.status_code != 200:
        fail("Profile defaults", f"HTTP {r.status_code}")
        return
    d = r.json()

    checks = {
        "total_score == 0": d.get("total_score") == 0,
        "games_played == 0": d.get("games_played") == 0,
        "highest_level == 1": d.get("highest_level") == 1,
        "bio is empty": d.get("bio", "") == "",
        "bg_color default": d.get("bg_color") in ("#000000", ""),
        "show_scores default": d.get("show_scores") is True,
    }
    failures = [k for k, v in checks.items() if not v]
    if not failures:
        ok("Profile defaults are correct")
    else:
        fail(f"Profile defaults wrong: {failures}")


def test_profile_no_auth():
    """GET /game/profile/me without token"""
    r = requests.get(f"{API}/game/profile/me", timeout=10)
    if r.status_code in (401, 403):
        ok("Profile without auth → 401/403")
    else:
        fail("Profile no auth", f"Expected 401/403, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · BIO UPDATE
# ══════════════════════════════════════════════════════════════════════════════

def test_update_bio():
    """PATCH /game/profile/me — set bio"""
    if not _token:
        fail("Update bio", "no token")
        return
    bio = f"Hello from test at {TS}! This is my bio."
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": bio},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("bio") == bio:
        ok("Update bio → saved correctly")
    else:
        fail("Update bio", f"HTTP {r.status_code}")


def test_update_bio_empty():
    """PATCH /game/profile/me — clear bio"""
    if not _token:
        fail("Clear bio", "no token")
        return
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": ""},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("bio") == "":
        ok("Clear bio → saved correctly")
    else:
        fail("Clear bio", f"HTTP {r.status_code}")


def test_update_bio_long():
    """PATCH /game/profile/me — bio at max length (500 chars)"""
    if not _token:
        fail("Long bio", "no token")
        return
    long_bio = "A" * 500
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": long_bio},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        ok("Long bio (500 chars) → accepted")
    else:
        fail("Long bio", f"HTTP {r.status_code}")


def test_update_bio_too_long():
    """PATCH /game/profile/me — bio exceeding max length"""
    if not _token:
        fail("Too long bio", "no token")
        return
    too_long = "X" * 1000
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": too_long},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Bio too long → rejected by server")
    elif r.status_code == 200:
        # May be truncated or accepted
        actual_len = len(r.json().get("bio", ""))
        if actual_len <= 500:
            warn("Bio too long", f"Accepted but truncated to {actual_len} chars")
        else:
            warn("Bio too long", "Server accepted 1000 chars (no max length validation?)")
    else:
        fail("Bio too long", f"HTTP {r.status_code}")


def test_update_bio_special_chars():
    """PATCH /game/profile/me — bio with special characters / XSS attempt"""
    if not _token:
        fail("Bio special chars", "no token")
        return
    xss_bio = '<script>alert("xss")</script> &amp; "quotes" <img onerror=alert(1)>'
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bio": xss_bio},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        returned_bio = r.json().get("bio", "")
        # Check if the script tag was stored as-is (frontend should escape it on display)
        if "<script>" in returned_bio:
            warn("Bio XSS", "Script tags stored in bio (frontend must sanitize on render)")
        else:
            ok("Bio special chars → stored/sanitized")
    else:
        ok(f"Bio special chars → rejected (HTTP {r.status_code})")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · BACKGROUND COLOR
# ══════════════════════════════════════════════════════════════════════════════

def test_update_bg_color():
    """PATCH /game/profile/me — set background color"""
    if not _token:
        fail("Update bg_color", "no token")
        return
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bg_color": "#ff5500"},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("bg_color") == "#ff5500":
        ok("Update bg_color → saved")
    else:
        fail("Update bg_color", f"HTTP {r.status_code}")


def test_update_bg_color_invalid():
    """PATCH /game/profile/me — invalid color format"""
    if not _token:
        fail("Invalid bg_color", "no token")
        return
    r = requests.patch(
        f"{API}/game/profile/me",
        json={"bg_color": "not-a-color"},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Invalid bg_color → rejected")
    elif r.status_code == 200:
        warn("Invalid bg_color", "Server accepted 'not-a-color' (no validation)")
    else:
        fail("Invalid bg_color", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · SHOW SCORES TOGGLE
# ══════════════════════════════════════════════════════════════════════════════

def test_toggle_show_scores():
    """Toggle show_scores on and off"""
    if not _token:
        fail("Toggle show_scores", "no token")
        return

    # Set to false
    r1 = requests.patch(
        f"{API}/game/profile/me",
        json={"show_scores": False},
        headers=_auth(),
        timeout=10,
    )
    if r1.status_code != 200:
        fail("Toggle show_scores (off)", f"HTTP {r1.status_code}")
        return

    # Verify
    r2 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    if r2.status_code == 200 and r2.json().get("show_scores") is False:
        pass  # OK so far
    else:
        fail("Toggle show_scores", "Value didn't persist")
        return

    # Set back to true
    r3 = requests.patch(
        f"{API}/game/profile/me",
        json={"show_scores": True},
        headers=_auth(),
        timeout=10,
    )
    if r3.status_code == 200 and r3.json().get("show_scores") is True:
        ok("Toggle show_scores (off → on) works")
    else:
        fail("Toggle show_scores (back on)", f"HTTP {r3.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · AVATAR UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

def _make_fake_png(size_bytes=1024):
    """Create a minimal valid PNG file in memory"""
    # Minimal 1x1 red PNG
    import struct
    import zlib
    
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xFFFFFFFF)
    
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00\xff\x00\x00')
    
    png = signature + make_chunk(b'IHDR', ihdr) + make_chunk(b'IDAT', idat) + make_chunk(b'IEND', b'')
    
    # Pad to desired size if needed
    if len(png) < size_bytes:
        # Add a text chunk with padding
        pad = b'\x00' * (size_bytes - len(png) - 12)  # 12 for chunk overhead
        png = signature + make_chunk(b'IHDR', ihdr) + make_chunk(b'tEXt', b'Comment\x00' + pad) + make_chunk(b'IDAT', idat) + make_chunk(b'IEND', b'')
    
    return png


def test_avatar_upload():
    """POST /api/game/profile/me/avatar — upload a small PNG"""
    if not _token:
        fail("Avatar upload", "no token")
        return
    
    png_data = _make_fake_png(2048)
    
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("test_avatar.png", png_data, "image/png")},
        headers=_auth(),
        timeout=15,
    )
    if r.status_code == 200:
        d = r.json()
        if "avatar_url" in d:
            ok(f"Avatar upload → success (url={d['avatar_url'][:50]}...)")
        else:
            ok("Avatar upload → accepted (no avatar_url in response)")
    else:
        fail("Avatar upload", f"HTTP {r.status_code} — {r.text[:200]}")


def test_avatar_no_file():
    """POST /api/game/profile/me/avatar — without a file"""
    if not _token:
        fail("Avatar no file", "no token")
        return
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Avatar upload no file → rejected")
    else:
        fail("Avatar no file", f"Expected 400, got {r.status_code}")


def test_avatar_wrong_type():
    """POST /api/game/profile/me/avatar — upload a .txt file"""
    if not _token:
        fail("Avatar wrong type", "no token")
        return
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("exploit.txt", b"not an image", "text/plain")},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code in (400, 422):
        ok("Avatar wrong type (txt) → rejected")
    else:
        fail("Avatar wrong type", f"Expected 400, got {r.status_code}")


def test_avatar_too_large():
    """POST /api/game/profile/me/avatar — file > 5MB"""
    if not _token:
        fail("Avatar too large", "no token")
        return
    # 6MB of zeros
    big_data = b'\x00' * (6 * 1024 * 1024)
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("huge.png", big_data, "image/png")},
        headers=_auth(),
        timeout=30,
    )
    if r.status_code in (400, 413, 422):
        ok(f"Avatar too large (6MB) → rejected ({r.status_code})")
    else:
        fail("Avatar too large", f"Expected 400/413, got {r.status_code}")


def test_avatar_no_auth():
    """POST /api/game/profile/me/avatar — without authentication"""
    r = requests.post(
        f"{API}/game/profile/me/avatar",
        files={"avatar": ("test.png", b"fake", "image/png")},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Avatar upload no auth → 401/403")
    else:
        fail("Avatar no auth", f"Expected 401/403, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  6 · PROFILE AFTER GAME SESSION
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_stats_after_session():
    """Profile stats update after completing a game session"""
    if not (_token and _player_id):
        fail("Profile stats after session", "no auth")
        return

    # Get initial stats
    r1 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    if r1.status_code != 200:
        fail("Profile stats after session", f"Cannot read profile: HTTP {r1.status_code}")
        return
    initial = r1.json()

    # Create and complete a session
    r2 = requests.post(
        f"{API}/game/sessions",
        json={"player_id": _player_id},
        headers=_auth(),
        timeout=10,
    )
    if r2.status_code != 200:
        fail("Profile stats after session", f"Cannot create session: HTTP {r2.status_code}")
        return
    session_id = r2.json()["id"]

    r3 = requests.patch(
        f"{API}/game/sessions/{session_id}",
        json={"score": 1000, "level_reached": 3, "completed": True},
        headers=_auth(),
        timeout=10,
    )
    if r3.status_code != 200:
        fail("Profile stats after session", f"Cannot end session: HTTP {r3.status_code}")
        return

    # Check updated stats
    r4 = requests.get(f"{API}/game/profile/me", headers=_auth(), timeout=10)
    if r4.status_code != 200:
        fail("Profile stats after session", f"Cannot re-read profile: HTTP {r4.status_code}")
        return
    updated = r4.json()

    checks = {
        "total_score increased": updated.get("total_score", 0) > initial.get("total_score", 0),
        "games_played increased": updated.get("games_played", 0) > initial.get("games_played", 0),
    }
    failed = [k for k, v in checks.items() if not v]
    if not failed:
        ok(f"Profile stats updated (score: {initial.get('total_score',0)} → {updated.get('total_score',0)})")
    else:
        fail(f"Profile stats not updated: {failed}")


# ══════════════════════════════════════════════════════════════════════════════
#  7 · ACCOUNT UPDATE
# ══════════════════════════════════════════════════════════════════════════════

def test_update_account_email():
    """PATCH /api/auth/update-account — update email"""
    if not _token:
        fail("Update account email", "no token")
        return
    new_email = f"updated_{TS}@test.com"
    r = requests.patch(
        f"{API}/auth/update-account",
        json={"email": new_email},
        headers=_auth(),
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        if d.get("email") == new_email:
            ok(f"Update account email → {new_email}")
        else:
            warn("Update account email", "Email not reflected in response")
    else:
        fail("Update account email", f"HTTP {r.status_code}")


def test_update_account_no_auth():
    """PATCH /api/auth/update-account without auth"""
    r = requests.patch(
        f"{API}/auth/update-account",
        json={"email": "hacker@evil.com"},
        timeout=10,
    )
    if r.status_code in (401, 403):
        ok("Update account no auth → 401/403")
    else:
        fail("Update account no auth", f"Expected 401/403, got {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Profile & Avatar Tests")
    print(f"  Target: {BASE}")
    print(f"{'═' * 60}")

    section("Setup — Create test user")
    _setup()

    section("1 · Profile Read")
    test_get_profile()
    test_profile_defaults()
    test_profile_no_auth()

    section("2 · Bio Update")
    test_update_bio()
    test_update_bio_empty()
    test_update_bio_long()
    test_update_bio_too_long()
    test_update_bio_special_chars()

    section("3 · Background Color")
    test_update_bg_color()
    test_update_bg_color_invalid()

    section("4 · Show Scores Toggle")
    test_toggle_show_scores()

    section("5 · Avatar Upload")
    test_avatar_upload()
    test_avatar_no_file()
    test_avatar_wrong_type()
    test_avatar_too_large()
    test_avatar_no_auth()

    section("6 · Profile After Game Session")
    test_profile_stats_after_session()

    section("7 · Account Update")
    test_update_account_email()
    test_update_account_no_auth()

    # Summary
    print(f"\n{'═' * 60}")
    total = 20
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} profile tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))", end="")
        print()
    else:
        print(f"  \033[91m{failed}/{total} profile test(s) FAILED:\033[0m")
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
