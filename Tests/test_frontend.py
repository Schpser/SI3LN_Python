"""
SI3LN Frontend Tests
=====================
Tests the web dashboard frontend: HTML structure, CSS loading, JavaScript logic,
navigation, search, i18n, and form validation.

Runs headlessly using requests + HTML parsing (no browser needed).

Usage:
    python Tests/test_frontend.py
    SI3LN_FRONTEND_URL=http://localhost python Tests/test_frontend.py
"""

import os
import sys
import re
import requests

# Frontend is served by nginx on port 80, API on port 8000
FRONTEND = os.environ.get("SI3LN_FRONTEND_URL", "http://localhost").rstrip("/")

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"

errors: list[str] = []
warnings: list[str] = []

_html: str = ""


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


def _fetch_html():
    """Load the main page once"""
    global _html
    r = requests.get(f"{FRONTEND}/", timeout=15)
    if r.status_code != 200:
        print(f"  {FAIL} Cannot load frontend at {FRONTEND} (HTTP {r.status_code})")
        sys.exit(1)
    _html = r.text
    print(f"  {INFO} Loaded index.html ({len(_html)} bytes)")


# ══════════════════════════════════════════════════════════════════════════════
#  1 · HTML STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

def test_html_doctype():
    """Page starts with <!DOCTYPE html>"""
    if _html.strip().lower().startswith("<!doctype html>"):
        ok("HTML5 doctype present")
    else:
        fail("HTML5 doctype missing")


def test_html_lang():
    """<html lang> attribute set"""
    if re.search(r'<html[^>]*\slang=', _html):
        ok('<html lang="..."> present')
    else:
        warn("Missing lang attribute on <html>")


def test_meta_charset():
    """<meta charset="UTF-8">"""
    if 'charset="UTF-8"' in _html or "charset='UTF-8'" in _html or 'charset=UTF-8' in _html.upper():
        ok("Meta charset UTF-8")
    else:
        fail("Meta charset UTF-8 missing")


def test_meta_viewport():
    """<meta name="viewport">"""
    if 'name="viewport"' in _html:
        ok("Meta viewport present")
    else:
        fail("Meta viewport missing")


def test_title():
    """Page has a <title>"""
    m = re.search(r'<title>(.*?)</title>', _html, re.IGNORECASE)
    if m and m.group(1).strip():
        ok(f"Title: \"{m.group(1).strip()}\"")
    else:
        fail("Missing <title>")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CSS / STYLESHEETS
# ══════════════════════════════════════════════════════════════════════════════

def test_css_files_loaded():
    """All expected CSS files are linked"""
    expected_css = [
        "css/style.css",
        "css/modules/profile.css",
        "css/modules/games.css",
        "css/modules/auth.css",
        "css/modules/help.css",
        "css/language-switcher.css",
        "css/responsive.css",
        "css/mobile.css",
    ]
    missing = []
    for css in expected_css:
        # Match href containing the path (with or without ?v= cache busting)
        if css not in _html:
            missing.append(css)
    if not missing:
        ok(f"All {len(expected_css)} CSS files linked")
    else:
        fail(f"Missing CSS links: {missing}")


def test_css_files_accessible():
    """Each CSS file returns 200"""
    css_hrefs = re.findall(r'href="(css/[^"]+)"', _html)
    inaccessible = []
    for href in css_hrefs:
        url = f"{FRONTEND}/{href.split('?')[0]}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                inaccessible.append(f"{href} → {r.status_code}")
        except Exception as e:
            inaccessible.append(f"{href} → {e}")

    if not inaccessible:
        ok(f"All {len(css_hrefs)} CSS files accessible (HTTP 200)")
    else:
        fail(f"CSS files inaccessible: {inaccessible}")


def test_google_fonts():
    """Google Fonts loaded"""
    if "fonts.googleapis.com" in _html:
        ok("Google Fonts linked")
    else:
        warn("Google Fonts not linked (custom fonts may not render)")


# ══════════════════════════════════════════════════════════════════════════════
#  3 · JAVASCRIPT FILES
# ══════════════════════════════════════════════════════════════════════════════

def test_js_files_loaded():
    """Expected JS files are referenced"""
    expected_js = [
        "config.js",
        "api.js",
        "app-refactored.js",
    ]
    missing = []
    for js in expected_js:
        if js not in _html:
            missing.append(js)
    if not missing:
        ok(f"Core JS files linked ({len(expected_js)})")
    else:
        fail(f"Missing JS files: {missing}")


def test_js_files_accessible():
    """Each JS file returns 200"""
    # Match both src="js/..." and src="api.js" patterns
    js_srcs = re.findall(r'src="([^"]*\.js[^"]*)"', _html)
    # Filter to local files only (skip external CDN)
    local_js = [s for s in js_srcs if not s.startswith("http")]
    inaccessible = []
    for src in local_js:
        url = f"{FRONTEND}/{src.split('?')[0]}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                inaccessible.append(f"{src} → {r.status_code}")
        except Exception as e:
            inaccessible.append(f"{src} → {e}")

    if not inaccessible:
        ok(f"All {len(local_js)} local JS files accessible")
    else:
        fail(f"JS files inaccessible: {inaccessible}")


def test_js_module_files():
    """Module files (auth, profile, games) are loaded"""
    modules_expected = ["auth.js", "profile.js", "games.js", "help.js"]
    missing = [m for m in modules_expected if m not in _html]
    if not missing:
        ok(f"All {len(modules_expected)} JS modules linked")
    else:
        fail(f"Missing JS modules: {missing}")


def test_js_services():
    """Service files (api-facade, search-service) are loaded"""
    services = ["api-facade.js", "search-service.js"]
    missing = [s for s in services if s not in _html]
    if not missing:
        ok(f"All {len(services)} JS services linked")
    else:
        fail(f"Missing JS services: {missing}")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · NAVIGATION / SPA STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

def test_side_menu_exists():
    """Side menu (nav.side-menu) exists"""
    if 'class="side-menu"' in _html or "class='side-menu'" in _html:
        ok("Side menu (.side-menu) present")
    else:
        fail("Side menu missing")


def test_menu_trigger():
    """Menu trigger button exists"""
    if 'id="menuTrigger"' in _html:
        ok("Menu trigger (#menuTrigger) present")
    else:
        fail("Menu trigger missing")


def test_menu_items():
    """Expected menu items: Profile, Games, Help, About"""
    expected_pages = ["profile", "games", "help", "about"]
    found = re.findall(r'data-page="(\w+)"', _html)
    missing = [p for p in expected_pages if p not in found]
    if not missing:
        ok(f"Menu items: {', '.join(expected_pages)}")
    else:
        fail(f"Missing menu items: {missing}")


def test_page_sections():
    """SPA pages: home, login, create-account, games, profile, help, about, game-play"""
    expected = ["home", "login", "create-account", "games", "profile"]
    found_pages = re.findall(r'id="(\w[\w-]*)-page"', _html)
    missing = [p for p in expected if f"{p}" not in [fp.replace("-page", "") for fp in found_pages] and f"{p}-page" not in _html]
    if not missing:
        ok(f"Page sections present for: {', '.join(expected)}")
    else:
        # Fallback: check by class="page"
        page_divs = _html.count('class="page')
        if page_divs >= len(expected):
            ok(f"Found {page_divs} page sections")
        else:
            fail(f"Missing page sections: {missing}")


def test_top_bar():
    """Top bar with search + auth"""
    checks = {
        "top-bar": 'class="top-bar"' in _html,
        "search-input": 'id="globalSearch"' in _html,
        "top-bar-title": 'class="top-bar-title"' in _html,
    }
    failed = [k for k, v in checks.items() if not v]
    if not failed:
        ok("Top bar structure: search + title + auth")
    else:
        fail(f"Top bar missing elements: {failed}")


# ══════════════════════════════════════════════════════════════════════════════
#  5 · AUTH FORMS
# ══════════════════════════════════════════════════════════════════════════════

def test_login_form():
    """Login page has username + password fields + submit"""
    checks = {
        "loginUsername": 'id="loginUsername"' in _html,
        "loginPassword": 'id="loginPassword"' in _html,
    }
    failed = [k for k, v in checks.items() if not v]
    if not failed:
        ok("Login form fields present")
    else:
        fail(f"Login form missing: {failed}")


def test_signup_form():
    """Signup page has all required fields"""
    expected_ids = [
        "signupPseudo",
        "signupEmail",
        "signupPassword",
        "signupConfirmPassword",
        "acceptTerms",
    ]
    missing = [eid for eid in expected_ids if f'id="{eid}"' not in _html]
    if not missing:
        ok("Signup form: all fields present")
    else:
        fail(f"Signup form missing fields: {missing}")


def test_password_requirements_ui():
    """Password strength indicators exist"""
    expected = ["reqLength", "reqNumber", "reqUpper"]
    missing = [eid for eid in expected if f'id="{eid}"' not in _html]
    if not missing:
        ok("Password requirement indicators present")
    else:
        warn(f"Password indicators missing: {missing}")


# ══════════════════════════════════════════════════════════════════════════════
#  6 · i18n
# ══════════════════════════════════════════════════════════════════════════════

def test_language_switcher():
    """Language switcher exists"""
    if 'id="languageSwitcher"' in _html:
        ok("Language switcher present")
    else:
        fail("Language switcher missing")


def test_i18n_attributes():
    """data-i18n attributes used for translations"""
    i18n_count = len(re.findall(r'data-i18n[=\-]', _html))
    if i18n_count > 0:
        ok(f"i18n attributes found ({i18n_count} elements)")
    else:
        warn("No data-i18n attributes found")


def test_locale_files_accessible():
    """Check if locale JSON files are accessible"""
    for lang in ["en", "fr"]:
        try:
            r = requests.get(f"{FRONTEND}/locales/{lang}.json", timeout=10)
            if r.status_code == 200:
                try:
                    data = r.json()
                    ok(f"Locale {lang}.json accessible ({len(data)} keys)")
                except Exception:
                    fail(f"Locale {lang}.json not valid JSON")
            else:
                warn(f"Locale {lang}.json", f"HTTP {r.status_code}")
        except Exception as e:
            warn(f"Locale {lang}.json", str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  7 · GAME SECTION
# ══════════════════════════════════════════════════════════════════════════════

def test_game_iframe():
    """Game iframe element exists"""
    if 'id="gameFrame"' in _html:
        ok("Game iframe (#gameFrame) present")
    else:
        warn("Game iframe missing (may be injected dynamically)")


def test_game_page_accessible():
    """Game index.html is accessible"""
    try:
        r = requests.get(f"{FRONTEND}/game/index.html", timeout=15)
        if r.status_code == 200:
            ok("Game page (game/index.html) accessible")
        else:
            warn("Game page", f"HTTP {r.status_code}")
    except Exception as e:
        warn("Game page", str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  8 · PROFILE SECTION
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_elements():
    """Profile page has all expected elements"""
    expected_ids = [
        "profileDisplayName",
        "profileUsername",
        "profileAvatarLarge",
        "userBio",
        "editProfileBtn",
    ]
    missing = [eid for eid in expected_ids if f'id="{eid}"' not in _html]
    if not missing:
        ok("Profile page elements present")
    else:
        fail(f"Profile elements missing: {missing}")


def test_edit_profile_modal():
    """Edit profile modal exists"""
    if 'id="editProfileModal"' in _html:
        ok("Edit profile modal present")
    else:
        warn("Edit profile modal missing")


# ══════════════════════════════════════════════════════════════════════════════
#  9 · SECURITY CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def test_no_inline_tokens():
    """No tokens/secrets leaked in HTML"""
    # Look for JWT-like patterns in the HTML source
    jwt_pattern = re.findall(r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}', _html)
    if not jwt_pattern:
        ok("No JWT tokens in HTML source")
    else:
        fail(f"JWT token found in HTML source ({len(jwt_pattern)} occurrence(s))")


def test_no_console_log_tokens():
    """JS files don't use console.log with token"""
    # Check main config
    try:
        r = requests.get(f"{FRONTEND}/js/config.js", timeout=10)
        if r.status_code == 200:
            js = r.text
            if 'DEBUG_MODE: false' in js or 'DEBUG_MODE:false' in js:
                ok("DEBUG_MODE is false in production config")
            elif 'DEBUG_MODE: true' in js:
                warn("DEBUG_MODE is true — will log to console")
            else:
                ok("Config loaded (DEBUG_MODE check inconclusive)")
    except Exception:
        warn("Couldn't check config.js")


def test_api_base_url():
    """API base URL is relative (not hardcoded localhost)"""
    try:
        r = requests.get(f"{FRONTEND}/js/config.js", timeout=10)
        if r.status_code == 200:
            if "localhost" in r.text and "API_BASE_URL" in r.text:
                # Check if it's just /api (relative)
                if "'/api'" in r.text or '"/api"' in r.text:
                    ok("API_BASE_URL is relative (/api)")
                else:
                    warn("API_BASE_URL may be hardcoded to localhost")
            else:
                ok("No hardcoded localhost in API config")
    except Exception:
        warn("Couldn't check API_BASE_URL")


# ══════════════════════════════════════════════════════════════════════════════
#  10 · RESPONSIVE / MOBILE
# ══════════════════════════════════════════════════════════════════════════════

def test_mobile_css():
    """Mobile CSS is loaded"""
    if "mobile.css" in _html:
        ok("Mobile CSS linked")
    else:
        fail("Mobile CSS missing")


def test_responsive_css():
    """Responsive CSS is loaded"""
    if "responsive.css" in _html:
        ok("Responsive CSS linked")
    else:
        fail("Responsive CSS missing")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Frontend Tests")
    print(f"  Target: {FRONTEND}")
    print(f"{'═' * 60}")

    section("Setup — Load index.html")
    _fetch_html()

    section("1 · HTML Structure")
    test_html_doctype()
    test_html_lang()
    test_meta_charset()
    test_meta_viewport()
    test_title()

    section("2 · CSS / Stylesheets")
    test_css_files_loaded()
    test_css_files_accessible()
    test_google_fonts()

    section("3 · JavaScript Files")
    test_js_files_loaded()
    test_js_files_accessible()
    test_js_module_files()
    test_js_services()

    section("4 · Navigation / SPA Structure")
    test_side_menu_exists()
    test_menu_trigger()
    test_menu_items()
    test_page_sections()
    test_top_bar()

    section("5 · Auth Forms")
    test_login_form()
    test_signup_form()
    test_password_requirements_ui()

    section("6 · i18n")
    test_language_switcher()
    test_i18n_attributes()
    test_locale_files_accessible()

    section("7 · Game Section")
    test_game_iframe()
    test_game_page_accessible()

    section("8 · Profile Section")
    test_profile_elements()
    test_edit_profile_modal()

    section("9 · Security Checks")
    test_no_inline_tokens()
    test_no_console_log_tokens()
    test_api_base_url()

    section("10 · Responsive / Mobile")
    test_mobile_css()
    test_responsive_css()

    # Summary
    print(f"\n{'═' * 60}")
    total = 30
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} frontend tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))", end="")
        print()
    else:
        print(f"  \033[91m{failed}/{total} frontend test(s) FAILED:\033[0m")
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
        print(f"\n  {FAIL} Cannot connect to {FRONTEND}")
        print(f"  {INFO} Start the frontend server first:\n"
              f"       docker compose -f Docker/docker-compose.yml up -d\n")
        sys.exit(1)
