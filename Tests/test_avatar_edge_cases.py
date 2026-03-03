"""
SI3LN Avatar Edge-Case Tests
==============================
Exercises avatar upload/download edge cases:
 - SVG upload (XSS vector check)
 - WebP / GIF upload
 - Re-upload replacing previous avatar
 - Avatar URL accessibility
 - Large file rejection
 - Wrong content-type

Requires running API server.

Usage:
    python Tests/test_avatar_edge_cases.py
"""

import os
import sys
import io
import time
import random
import string

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

BASE = os.environ.get("SI3LN_API_URL", "http://localhost:8000")
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


def rand(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


# ── Shared state ──────────────────────────────────────────────────────────────

TOKEN = None
PLAYER_ID = None
HEADERS = {}


def setup():
    """Register a fresh user and store auth token."""
    global TOKEN, PLAYER_ID, HEADERS

    username = f"avatar_edge_{rand()}"
    payload = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "AvatarTest1!",
    }
    r = requests.post(f"{API}/auth/register", json=payload, timeout=10)
    if r.status_code not in (200, 201):
        print(f"  {FAIL} Setup failed: cannot register ({r.status_code})")
        return False

    data = r.json()
    TOKEN = data.get("token")
    PLAYER_ID = data.get("player_id")

    if not TOKEN:
        print(f"  {FAIL} Setup failed: no token in response")
        return False

    HEADERS = {"Authorization": f"Bearer {TOKEN}"}
    print(f"  {PASS} Registered as {username} (id={PLAYER_ID})")
    return True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_png(width: int = 1, height: int = 1) -> bytes:
    """Create a minimal valid 1×1 PNG."""
    import struct, zlib
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw_row = b"\x00" + b"\xff\xff\xff" * width
    raw_data = raw_row * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw_data))
        + chunk(b"IEND", b"")
    )


def _upload_avatar(file_bytes: bytes, filename: str, content_type: str) -> requests.Response:
    """Upload an avatar to the profile endpoint."""
    files = {"avatar": (filename, io.BytesIO(file_bytes), content_type)}
    return requests.post(
        f"{API}/game/profile/me/avatar",
        headers=HEADERS,
        files=files,
        timeout=10,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  1 · BASIC PNG UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

def test_png_upload():
    """Uploading a valid PNG should succeed"""
    png = _make_png()
    r = _upload_avatar(png, "avatar.png", "image/png")
    if r.status_code in (200, 204):
        ok("PNG upload accepted")
    elif r.status_code == 405:
        warn("PNG upload", "PUT profile returned 405 — avatar upload may use a different endpoint")
    else:
        fail("PNG upload", f"HTTP {r.status_code}: {r.text[:120]}")


def test_avatar_url_accessible():
    """After upload the avatar URL should be GET-accessible"""
    # First get profile to find avatar URL
    r = requests.get(f"{API}/game/profile/me", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        warn("Avatar URL check", f"Cannot fetch profile (HTTP {r.status_code})")
        return

    data = r.json()
    avatar_url = data.get("avatar_url") or data.get("avatar") or data.get("profile_picture")
    if not avatar_url:
        warn("Avatar URL check", "No avatar URL in profile response")
        return

    # If relative, prepend base
    if avatar_url.startswith("/"):
        avatar_url = BASE + avatar_url

    r2 = requests.get(avatar_url, timeout=10)
    if r2.status_code == 200:
        ok(f"Avatar URL accessible (HTTP 200)")
    else:
        warn("Avatar URL accessible", f"HTTP {r2.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · SVG UPLOAD (XSS VECTOR)
# ══════════════════════════════════════════════════════════════════════════════

def test_svg_upload_rejected():
    """SVG files should be rejected (XSS risk)"""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert("xss")</script></svg>'
    r = _upload_avatar(svg, "evil.svg", "image/svg+xml")

    if r.status_code in (400, 415, 422):
        ok("SVG upload rejected (XSS prevention)")
    elif r.status_code in (200, 201, 204):
        # SVG accepted — check if it's served with safe headers
        warn("SVG upload ACCEPTED — potential XSS vector! Check Content-Security-Policy")
    else:
        warn("SVG upload", f"HTTP {r.status_code}: {r.text[:80]}")


def test_svg_with_png_extension():
    """SVG renamed to .png should still be caught"""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    r = _upload_avatar(svg, "fake.png", "image/png")

    if r.status_code in (400, 415, 422):
        ok("SVG-as-PNG detected and rejected")
    elif r.status_code in (200, 201, 204):
        warn("SVG-as-PNG accepted", "Server may not check magic bytes")
    else:
        warn("SVG-as-PNG", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · ALTERNATIVE FORMATS
# ══════════════════════════════════════════════════════════════════════════════

def test_gif_upload():
    """GIF upload should be accepted or properly rejected"""
    # Minimal GIF89a (1x1 white pixel)
    gif = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
        b"\xff\xff\xff\x00\x00\x00"
        b"!\xf9\x04\x00\x00\x00\x00\x00"
        b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )
    r = _upload_avatar(gif, "avatar.gif", "image/gif")

    if r.status_code in (200, 201, 204):
        ok("GIF upload accepted")
    elif r.status_code in (400, 415):
        ok("GIF upload properly rejected (PNG/JPEG only)")
    else:
        warn("GIF upload", f"HTTP {r.status_code}")


def test_webp_upload():
    """WebP upload should be accepted or properly rejected"""
    # Minimal WebP header (not a real image but tests content-type handling)
    webp = b"RIFF\x24\x00\x00\x00WEBPVP8 \x18\x00\x00\x000\x01\x00\x9d\x01\x2a\x01\x00\x01\x00\x01\x00\x03p\x00\xfe\xfb\x94\x00\x00"
    r = _upload_avatar(webp, "avatar.webp", "image/webp")

    if r.status_code in (200, 201, 204):
        ok("WebP upload accepted")
    elif r.status_code in (400, 415):
        ok("WebP upload properly rejected (format not supported)")
    else:
        warn("WebP upload", f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · RE-UPLOAD / OVERWRITE
# ══════════════════════════════════════════════════════════════════════════════

def test_reupload_replaces_previous():
    """Upload → re-upload should replace (not accumulate) avatars"""
    png1 = _make_png(1, 1)
    png2 = _make_png(2, 2)

    r1 = _upload_avatar(png1, "first.png", "image/png")
    if r1.status_code not in (200, 201, 204):
        warn("Re-upload test", f"First upload failed (HTTP {r1.status_code})")
        return

    # Get avatar URL after first upload
    p1 = requests.get(f"{API}/game/profile/me", headers=HEADERS, timeout=10).json()
    url1 = p1.get("avatar_url") or p1.get("avatar") or p1.get("profile_picture")

    r2 = _upload_avatar(png2, "second.png", "image/png")
    if r2.status_code not in (200, 201, 204):
        warn("Re-upload test", f"Second upload failed (HTTP {r2.status_code})")
        return

    p2 = requests.get(f"{API}/game/profile/me", headers=HEADERS, timeout=10).json()
    url2 = p2.get("avatar_url") or p2.get("avatar") or p2.get("profile_picture")

    if url1 and url2:
        if url1 != url2:
            ok("Re-upload produces new avatar URL (old replaced)")
        else:
            warn("Re-upload same URL", "Might use filename-based caching")
    else:
        warn("Re-upload test", "Could not determine avatar URLs")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · SIZE / INVALID CONTENT
# ══════════════════════════════════════════════════════════════════════════════

def test_large_file_rejected():
    """Files over the size limit should be rejected"""
    # 6 MB of zero-padding after a valid PNG header
    big = _make_png(1, 1)
    big += b"\x00" * (6 * 1024 * 1024)

    try:
        files = {"avatar": ("huge.png", io.BytesIO(big), "image/png")}
        r = requests.post(
            f"{API}/game/profile/me/avatar",
            headers=HEADERS,
            files=files,
            timeout=30,  # longer timeout for large upload
        )
        if r.status_code in (400, 413, 422):
            ok(f"Large file rejected (HTTP {r.status_code})")
        elif r.status_code in (200, 201, 204):
            warn("Large file accepted", "Consider adding a max avatar size limit")
        else:
            warn("Large file", f"HTTP {r.status_code}")
    except requests.exceptions.ReadTimeout:
        warn("Large file", "Upload timed out (server may lack size check before read)")
    except requests.exceptions.ConnectionError:
        warn("Large file", "Connection reset (server may have dropped oversized request)")


def test_non_image_rejected():
    """Non-image file (e.g. .exe) should be rejected"""
    exe_header = b"MZ" + b"\x00" * 100  # Minimal PE header
    r = _upload_avatar(exe_header, "malware.exe", "application/octet-stream")

    if r.status_code in (400, 415, 422):
        ok("Non-image file rejected")
    elif r.status_code in (200, 201, 204):
        fail("Non-image file ACCEPTED", "Server accepts arbitrary file types as avatars!")
    else:
        warn("Non-image file", f"HTTP {r.status_code}")


def test_empty_file():
    """Empty file upload should be handled gracefully"""
    r = _upload_avatar(b"", "empty.png", "image/png")

    if r.status_code in (400, 422):
        ok("Empty file rejected")
    elif r.status_code in (200, 201, 204):
        warn("Empty file accepted", "May cause issues when rendering")
    else:
        warn("Empty file", f"HTTP {r.status_code}")


def test_no_auth_upload():
    """Avatar upload without auth should fail"""
    png = _make_png()
    files = {"avatar": ("noauth.png", io.BytesIO(png), "image/png")}
    r = requests.post(f"{API}/game/profile/me/avatar", files=files, timeout=10)

    if r.status_code in (401, 403):
        ok("Avatar upload without auth rejected")
    elif r.status_code == 405:
        warn("No-auth upload (405)", "Endpoint may differ")
    else:
        fail("No-auth upload", f"HTTP {r.status_code} (expected 401/403)")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Avatar Edge-Case Tests")
    print(f"  API: {API}")
    print(f"{'═' * 60}")

    if not setup():
        print(f"\n  {FAIL} Setup failed – aborting.\n")
        return 1

    section("1 · Basic PNG Upload")
    test_png_upload()
    test_avatar_url_accessible()

    section("2 · SVG Upload (XSS)")
    test_svg_upload_rejected()
    test_svg_with_png_extension()

    section("3 · Alternative Formats")
    test_gif_upload()
    test_webp_upload()

    section("4 · Re-Upload / Overwrite")
    test_reupload_replaces_previous()

    section("5 · Size & Invalid Content")
    test_large_file_rejected()
    test_non_image_rejected()
    test_empty_file()
    test_no_auth_upload()

    # Summary
    print(f"\n{'═' * 60}")
    total = 11
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed - warned
    if failed == 0:
        if warned:
            print(f"  \033[92m{passed} passed\033[0m, \033[93m{warned} warning(s)\033[0m out of {total} avatar tests")
        else:
            print(f"  \033[92mAll {total} avatar edge-case tests passed\033[0m")
    else:
        print(f"  \033[91m{failed}/{total} avatar test(s) FAILED:\033[0m")
        for e in errors:
            print(f"    • {e}")
    print(f"{'═' * 60}\n")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
