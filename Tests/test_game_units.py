"""
SI3LN Game Python Unit Tests
===============================
Unit tests for the Game_Python modules: auth, scores, utils, api_client.
These tests run offline — no server needed, no Pygame display needed.

Usage:
    cd Game_Python && python ../Tests/test_game_units.py
    — or —
    python Tests/test_game_units.py  (will add Game_Python to path)
"""

import os
import sys
import json
import tempfile
import shutil

# Add Game_Python to path so we can import modules directly
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)
GAME_DIR = os.path.join(PROJECT_DIR, "Game_Python")
sys.path.insert(0, GAME_DIR)

# Prevent Pygame from opening a window
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

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


# ══════════════════════════════════════════════════════════════════════════════
#  1 · utils.py TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_validate_email_valid():
    """validate_email with valid email addresses"""
    from utils import validate_email
    valid_emails = [
        "user@example.com",
        "test.user@domain.co.uk",
        "user+tag@gmail.com",
        "a@b.co",
    ]
    all_ok = True
    for email in valid_emails:
        if not validate_email(email):
            fail(f"validate_email({email})", "Should be valid")
            all_ok = False
    if all_ok:
        ok(f"validate_email accepts {len(valid_emails)} valid emails")


def test_validate_email_invalid():
    """validate_email with invalid email addresses"""
    from utils import validate_email
    invalid_emails = [
        "",
        "not-an-email",
        "@no-user.com",
        "user@",
        "user@.com",
        "user@com",
        "a b@domain.com",
    ]
    all_ok = True
    for email in invalid_emails:
        if validate_email(email):
            warn(f"validate_email({email!r})", "Should be invalid but was accepted")
            all_ok = False
    if all_ok:
        ok(f"validate_email rejects {len(invalid_emails)} invalid emails")


def test_hash_password():
    """hash_password returns consistent hashes"""
    from utils import hash_password
    h1 = hash_password("test123")
    h2 = hash_password("test123")
    h3 = hash_password("different")

    if h1 == h2 and h1 != h3:
        ok("hash_password is consistent and unique per password")
    else:
        fail("hash_password", f"h1==h2: {h1 == h2}, h1!=h3: {h1 != h3}")


def test_hash_password_not_plaintext():
    """hash_password should not return the plaintext"""
    from utils import hash_password
    password = "MySecretPass123"
    hashed = hash_password(password)
    if password not in hashed:
        ok("hash_password does not return plaintext")
    else:
        fail("hash_password returns plaintext!")


def test_clamp():
    """clamp function works correctly"""
    from utils import clamp
    tests = [
        (5, 0, 10, 5),      # Within range
        (-5, 0, 10, 0),     # Below min
        (15, 0, 10, 10),    # Above max
        (0, 0, 10, 0),      # At min
        (10, 0, 10, 10),    # At max
        (5, 5, 5, 5),       # min == max == value
    ]
    all_ok = True
    for value, min_v, max_v, expected in tests:
        result = clamp(value, min_v, max_v)
        if result != expected:
            fail(f"clamp({value}, {min_v}, {max_v})", f"Expected {expected}, got {result}")
            all_ok = False
    if all_ok:
        ok(f"clamp works correctly for {len(tests)} cases")


# ══════════════════════════════════════════════════════════════════════════════
#  2 · auth.py (AuthSystem) TESTS
# ══════════════════════════════════════════════════════════════════════════════

def _create_temp_auth():
    """Create AuthSystem with temporary data directory"""
    import constants
    import auth as _auth_mod
    tmp_dir = tempfile.mkdtemp()
    original_file = constants.USER_DATA_FILE
    new_file = os.path.join(tmp_dir, "test_users.json")
    constants.USER_DATA_FILE = new_file
    _auth_mod.USER_DATA_FILE = new_file          # patch the local binding too
    from auth import AuthSystem
    auth = AuthSystem()
    return auth, tmp_dir, original_file


def _cleanup_temp_auth(tmp_dir, original_file):
    import constants
    import auth as _auth_mod
    constants.USER_DATA_FILE = original_file
    _auth_mod.USER_DATA_FILE = original_file     # restore the local binding
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_auth_register_success():
    """Register a new user successfully"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        success, msg = auth.register("testuser", "password123", "test@test.com")
        if success:
            ok("AuthSystem.register → success")
        else:
            fail("AuthSystem.register", msg)
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_register_duplicate():
    """Register with duplicate username"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "pass1234", "a@b.com")
        success, msg = auth.register("testuser", "pass5678", "c@d.com")
        if not success:
            ok("AuthSystem.register duplicate → rejected")
        else:
            fail("AuthSystem.register duplicate", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_register_short_username():
    """Register with username shorter than 3 chars"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        success, msg = auth.register("ab", "password123")
        if not success:
            ok("AuthSystem.register short username → rejected")
        else:
            fail("AuthSystem.register short username", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_register_short_password():
    """Register with password shorter than 4 chars"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        success, msg = auth.register("testuser", "abc")
        if not success:
            ok("AuthSystem.register short password → rejected")
        else:
            fail("AuthSystem.register short password", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_register_invalid_email():
    """Register with invalid email format"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        success, msg = auth.register("testuser", "password123", "not-an-email")
        if not success:
            ok("AuthSystem.register invalid email → rejected")
        else:
            fail("AuthSystem.register invalid email", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_login_success():
    """Login with correct credentials"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "mypass123", "test@test.com")
        success, msg = auth.login("testuser", "mypass123")
        if success and auth.current_user == "testuser":
            ok("AuthSystem.login → success")
        else:
            fail("AuthSystem.login", msg)
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_login_wrong_password():
    """Login with wrong password"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "correctpass", "test@test.com")
        success, msg = auth.login("testuser", "wrongpass")
        if not success:
            ok("AuthSystem.login wrong password → rejected")
        else:
            fail("AuthSystem.login wrong password", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_login_nonexistent_user():
    """Login with username that doesn't exist"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        success, msg = auth.login("ghost_user", "password123")
        if not success:
            ok("AuthSystem.login nonexistent user → rejected")
        else:
            fail("AuthSystem.login nonexistent", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_guest_mode():
    """Login as guest"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        success, msg = auth.login_as_guest(2)
        if success and auth.guest_mode and auth.current_user is None:
            ok("AuthSystem.login_as_guest → success (guest_mode=True)")
        else:
            fail("AuthSystem.login_as_guest", msg)
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_logout():
    """Logout clears current user"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "pass1234")
        auth.login("testuser", "pass1234")
        auth.logout()
        if auth.current_user is None and not auth.guest_mode:
            ok("AuthSystem.logout → cleared")
        else:
            fail("AuthSystem.logout", f"current_user={auth.current_user}, guest={auth.guest_mode}")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_change_password_success():
    """Change password with correct old password"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "oldpass123")
        auth.login("testuser", "oldpass123")
        success, msg = auth.change_password("oldpass123", "newpass456")
        if success:
            # Verify new password works
            auth.logout()
            ok2, _ = auth.login("testuser", "newpass456")
            if ok2:
                ok("AuthSystem.change_password → success + login with new pass")
            else:
                fail("AuthSystem.change_password", "New password doesn't work after change")
        else:
            fail("AuthSystem.change_password", msg)
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_change_password_wrong_old():
    """Change password with wrong old password"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "correctold")
        auth.login("testuser", "correctold")
        success, msg = auth.change_password("wrongold", "newpass456")
        if not success:
            ok("AuthSystem.change_password wrong old → rejected")
        else:
            fail("AuthSystem.change_password wrong old", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_change_password_too_short():
    """Change password to something too short"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "oldpass123")
        auth.login("testuser", "oldpass123")
        success, msg = auth.change_password("oldpass123", "ab")
        if not success:
            ok("AuthSystem.change_password too short → rejected")
        else:
            fail("AuthSystem.change_password too short", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_change_username():
    """Change username"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("oldname", "pass1234")
        auth.login("oldname", "pass1234")
        success, msg = auth.change_username("newname")
        if success and auth.current_user == "newname":
            ok("AuthSystem.change_username → success")
        else:
            fail("AuthSystem.change_username", msg)
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_change_username_duplicate():
    """Change username to an already-taken name"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("user_a", "pass1234")
        auth.register("user_b", "pass1234")
        auth.login("user_a", "pass1234")
        success, msg = auth.change_username("user_b")
        if not success:
            ok("AuthSystem.change_username duplicate → rejected")
        else:
            fail("AuthSystem.change_username duplicate", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_change_username_too_short():
    """Change username to something shorter than 3 chars"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "pass1234")
        auth.login("testuser", "pass1234")
        success, msg = auth.change_username("ab")
        if not success:
            ok("AuthSystem.change_username too short → rejected")
        else:
            fail("AuthSystem.change_username too short", "Should have been rejected")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_is_username_available():
    """Check username availability"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("taken_name", "pass1234")
        if not auth.is_username_available("taken_name"):
            if auth.is_username_available("free_name"):
                ok("AuthSystem.is_username_available works correctly")
            else:
                fail("is_username_available", "Free name reported as taken")
        else:
            fail("is_username_available", "Taken name reported as available")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_get_user_data():
    """Get user data after login"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "pass1234", "test@test.com")
        auth.login("testuser", "pass1234")
        data = auth.get_user_data()
        if data and "email" in data and "high_score" in data:
            ok("AuthSystem.get_user_data → returns user data dict")
        else:
            fail("AuthSystem.get_user_data", f"Unexpected: {data}")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_get_user_data_guest():
    """Get user data in guest mode"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.login_as_guest(1)
        data = auth.get_user_data()
        if data and data.get("high_score") == 0:
            ok("AuthSystem.get_user_data (guest) → returns default data")
        else:
            fail("AuthSystem.get_user_data guest", f"Unexpected: {data}")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_update_user_data():
    """Update current user data"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.register("testuser", "pass1234")
        auth.login("testuser", "pass1234")
        result = auth.update_user_data(high_score=5000)
        if result:
            data = auth.get_user_data("high_score")
            if data == 5000:
                ok("AuthSystem.update_user_data → high_score updated")
            else:
                fail("AuthSystem.update_user_data", f"high_score={data}")
        else:
            fail("AuthSystem.update_user_data", "Returned False")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_update_user_data_guest():
    """Update user data in guest mode should fail"""
    auth, tmp_dir, orig = _create_temp_auth()
    try:
        auth.login_as_guest()
        result = auth.update_user_data(high_score=9999)
        if not result:
            ok("AuthSystem.update_user_data (guest) → rejected")
        else:
            fail("AuthSystem.update_user_data guest", "Should have returned False")
    finally:
        _cleanup_temp_auth(tmp_dir, orig)


def test_auth_persistence():
    """User data persists after reload"""
    import constants
    import auth as _auth_mod
    tmp_dir = tempfile.mkdtemp()
    user_file = os.path.join(tmp_dir, "test_users.json")
    original_file = constants.USER_DATA_FILE
    constants.USER_DATA_FILE = user_file
    _auth_mod.USER_DATA_FILE = user_file          # patch local binding
    try:
        from auth import AuthSystem
        auth1 = AuthSystem()
        auth1.register("persist_user", "pass1234", "p@test.com")

        # Create a new AuthSystem instance (simulates restart)
        auth2 = AuthSystem()
        if "persist_user" in auth2.users:
            ok("AuthSystem data persists across instances")
        else:
            fail("AuthSystem persistence", "User not found after reload")
    finally:
        constants.USER_DATA_FILE = original_file
        _auth_mod.USER_DATA_FILE = original_file  # restore
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
#  3 · scores.py (ScoreManager) TESTS
# ══════════════════════════════════════════════════════════════════════════════

def _create_temp_scores():
    """Create ScoreManager with temporary data directory"""
    import constants
    import scores as _scores_mod
    tmp_dir = tempfile.mkdtemp()
    original_file = constants.SCORES_FILE
    new_file = os.path.join(tmp_dir, "test_scores.json")
    constants.SCORES_FILE = new_file
    _scores_mod.SCORES_FILE = new_file            # patch local binding
    from scores import ScoreManager
    mgr = ScoreManager()
    return mgr, tmp_dir, original_file


def _cleanup_temp_scores(tmp_dir, original_file):
    import constants
    import scores as _scores_mod
    constants.SCORES_FILE = original_file
    _scores_mod.SCORES_FILE = original_file       # restore local binding
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_scores_add_and_rank():
    """Add scores and verify ranking"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        pos1, is_top1 = mgr.add_score("player1", 1000, 5)
        pos2, is_top2 = mgr.add_score("player2", 2000, 7)
        pos3, is_top3 = mgr.add_score("player3", 500, 3)

        if pos2 == 1 and is_top2:
            ok("Highest score gets rank 1")
        else:
            fail("Score ranking", f"player2 (2000) got position={pos2}")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_guest_rejected():
    """Guest scores should not be saved"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        pos, is_top = mgr.add_score("Guest", 5000, 10)
        if pos is None and not is_top:
            ok("Guest score rejected (not saved)")
        else:
            fail("Guest score", f"pos={pos}, is_top={is_top}")

        pos2, is_top2 = mgr.add_score("", 5000, 10)
        if pos2 is None and not is_top2:
            ok("Empty username score rejected")
        else:
            fail("Empty username score", f"pos={pos2}, is_top={is_top2}")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_top_20_limit():
    """Leaderboard should only keep top 20 scores"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        # Add 25 scores
        for i in range(25):
            mgr.add_score(f"player_{i}", (i + 1) * 100, i + 1)

        top = mgr.get_top_scores()
        if len(top) == 20:
            ok("Top 20 limit enforced correctly")
        else:
            fail("Top 20 limit", f"Got {len(top)} scores instead of 20")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_get_top_with_limit():
    """get_top_scores with custom limit"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        for i in range(10):
            mgr.add_score(f"player_{i}", (i + 1) * 100, 1)

        top5 = mgr.get_top_scores(5)
        if len(top5) == 5:
            ok("get_top_scores(5) returns 5 entries")
        else:
            fail("get_top_scores limit", f"Got {len(top5)} entries")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_sorted_descending():
    """Scores should be sorted descending"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        mgr.add_score("low", 100, 1)
        mgr.add_score("high", 5000, 10)
        mgr.add_score("mid", 2500, 5)

        top = mgr.get_top_scores()
        scores = [s["score"] for s in top]
        if scores == sorted(scores, reverse=True):
            ok("Scores sorted descending")
        else:
            fail("Score sorting", f"Order: {scores}")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_get_user_best():
    """Get user's best score"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        mgr.add_score("player1", 100, 1)
        mgr.add_score("player1", 500, 5)
        mgr.add_score("player1", 300, 3)

        best = mgr.get_user_best_score("player1")
        if best and best["score"] == 500:
            ok("get_user_best_score → 500 (correct)")
        else:
            fail("get_user_best_score", f"Got {best}")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_get_user_best_nonexistent():
    """Get best score for user with no scores"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        result = mgr.get_user_best_score("ghost")
        if result is None:
            ok("get_user_best_score (nonexistent) → None")
        else:
            fail("get_user_best_score nonexistent", f"Expected None, got {result}")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_is_high_score():
    """is_high_score check"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        # Add less than 20 scores → any score is a high score
        mgr.add_score("player", 100, 1)
        if mgr.is_high_score(50):
            ok("is_high_score when < 20 entries → True")
        else:
            fail("is_high_score", "Should be True when under 20 entries")

        # Fill up to 20
        for i in range(19):
            mgr.add_score(f"p{i}", 1000 + i * 100, 1)

        # Now check a score below the lowest
        lowest = mgr.scores[-1]["score"]
        if not mgr.is_high_score(lowest - 1):
            ok(f"is_high_score below lowest ({lowest}) → False")
        else:
            fail("is_high_score below lowest", "Should be False")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_get_rank():
    """get_rank returns the correct position"""
    mgr, tmp, orig = _create_temp_scores()
    try:
        mgr.add_score("low", 100, 1)
        mgr.add_score("mid", 500, 3)
        mgr.add_score("high", 1000, 5)

        rank = mgr.get_rank(1500)
        if rank == 1:
            ok("get_rank(1500) → rank 1 (above all)")
        else:
            fail("get_rank(1500)", f"Expected 1, got {rank}")

        rank2 = mgr.get_rank(300)
        if rank2 == 3:
            ok("get_rank(300) → rank 3 (between low and mid)")
        else:
            warn("get_rank(300)", f"Expected 3, got {rank2}")
    finally:
        _cleanup_temp_scores(tmp, orig)


def test_scores_persistence():
    """Scores persist after reload"""
    import constants
    import scores as _scores_mod
    tmp_dir = tempfile.mkdtemp()
    scores_file = os.path.join(tmp_dir, "test_scores.json")
    original_file = constants.SCORES_FILE
    constants.SCORES_FILE = scores_file
    _scores_mod.SCORES_FILE = scores_file             # patch local binding
    try:
        from scores import ScoreManager
        mgr1 = ScoreManager()
        mgr1.add_score("persist_player", 9999, 10)

        mgr2 = ScoreManager()
        top = mgr2.get_top_scores()
        found = any(s["username"] == "persist_player" for s in top)
        if found:
            ok("ScoreManager data persists across instances")
        else:
            fail("ScoreManager persistence", "Score not found after reload")
    finally:
        constants.SCORES_FILE = original_file
        _scores_mod.SCORES_FILE = original_file       # restore
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
#  4 · api_client.py TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_jwt_field_decode():
    """_jwt_field decodes a JWT payload field"""
    from api_client import _jwt_field
    import base64, json as _json

    # Build a fake JWT
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    payload_data = {"user_id": 42, "player_id": 7, "username": "testplayer"}
    payload = base64.urlsafe_b64encode(
        _json.dumps(payload_data).encode()
    ).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    token = f"{header}.{payload}.{sig}"

    if _jwt_field(token, "player_id") == 7:
        ok("_jwt_field decodes player_id correctly")
    else:
        fail("_jwt_field", f"Got {_jwt_field(token, 'player_id')}")

    if _jwt_field(token, "username") == "testplayer":
        ok("_jwt_field decodes username correctly")
    else:
        fail("_jwt_field username", f"Got {_jwt_field(token, 'username')}")


def test_jwt_field_malformed():
    """_jwt_field with malformed tokens returns None"""
    from api_client import _jwt_field

    bad_tokens = [
        "",
        "not.a.jwt.with.four.parts",
        "only_one_part",
        "two.parts",
        "valid.!!!invalid_base64!!!.sig",
    ]
    all_ok = True
    for tok in bad_tokens:
        result = _jwt_field(tok, "player_id")
        if result is not None:
            fail(f"_jwt_field({tok!r})", f"Expected None, got {result}")
            all_ok = False
    if all_ok:
        ok(f"_jwt_field returns None for {len(bad_tokens)} malformed tokens")


def test_api_client_set_token():
    """APIClient.set_token extracts player_id and username"""
    from api_client import APIClient
    import base64, json as _json

    client = APIClient()

    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        _json.dumps({"player_id": 42, "username": "hero"}).encode()
    ).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"sig").rstrip(b"=").decode()
    token = f"{header}.{payload}.{sig}"

    client.set_token(token)

    if client.is_authenticated() and client.get_player_id() == 42 and client.get_username() == "hero":
        ok("APIClient.set_token → authenticated, player_id=42, username=hero")
    else:
        fail("APIClient.set_token", f"auth={client.is_authenticated()}, pid={client.get_player_id()}")


def test_api_client_not_authenticated():
    """APIClient without token is not authenticated"""
    from api_client import APIClient
    client = APIClient()
    client._token = ""
    client._player_id = None

    if not client.is_authenticated():
        ok("APIClient without token → not authenticated")
    else:
        fail("APIClient not authenticated", "Should not be authenticated without token")


def test_api_client_headers():
    """APIClient._headers includes auth when token is set"""
    from api_client import APIClient
    client = APIClient()
    client._token = "test_jwt_token"

    headers = client._headers()
    if headers.get("Authorization") == "Bearer test_jwt_token":
        ok("APIClient._headers includes Bearer token")
    else:
        fail("APIClient._headers", f"Got: {headers}")

    client._token = ""
    headers2 = client._headers()
    if "Authorization" not in headers2:
        ok("APIClient._headers excludes auth when no token")
    else:
        warn("APIClient._headers", "Auth header present without token")


def test_api_client_start_session_no_auth():
    """start_session without auth returns None"""
    from api_client import APIClient
    client = APIClient()
    client._token = ""
    client._player_id = None

    result = client.start_session()
    if result is None:
        ok("APIClient.start_session (no auth) → None")
    else:
        fail("APIClient.start_session no auth", f"Expected None, got {result}")


def test_api_client_end_session_no_auth():
    """end_session without auth returns None"""
    from api_client import APIClient
    client = APIClient()
    client._token = ""
    client._player_id = None
    client._session_id = None

    result = client.end_session(score=100)
    if result is None:
        ok("APIClient.end_session (no auth/session) → None")
    else:
        fail("APIClient.end_session no auth", f"Expected None, got {result}")


def test_api_client_get_leaderboard_fallback():
    """get_leaderboard returns empty list on failure"""
    from api_client import APIClient
    client = APIClient()
    # Without a working server, should return empty list
    import api_client as ac
    old_has = ac._HAS_REQUESTS
    ac._HAS_REQUESTS = False
    try:
        result = client.get_leaderboard()
        if isinstance(result, list) and len(result) == 0:
            ok("APIClient.get_leaderboard fallback → empty list")
        else:
            fail("APIClient.get_leaderboard fallback", f"Expected [], got {result}")
    finally:
        ac._HAS_REQUESTS = old_has


# ══════════════════════════════════════════════════════════════════════════════
#  5 · constants.py TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_constants_worlds_config():
    """Verify WORLDS configuration is complete"""
    from constants import WORLDS, WORLD_IDS
    expected_worlds = ["Space", "Desert", "Forest", "Marine", "Apocalyptic"]

    missing = [w for w in expected_worlds if w not in WORLDS]
    if not missing:
        ok(f"All {len(expected_worlds)} worlds configured in WORLDS")
    else:
        fail("WORLDS config", f"Missing: {missing}")

    missing_ids = [w for w in expected_worlds if w not in WORLD_IDS]
    if not missing_ids:
        ok(f"All {len(expected_worlds)} worlds have IDs in WORLD_IDS")
    else:
        fail("WORLD_IDS config", f"Missing: {missing_ids}")


def test_constants_world_fields():
    """Each world has required fields"""
    from constants import WORLDS
    required = ["name", "background", "levels", "enemies_dir", "enemy_count", "bullet_colors"]

    all_ok = True
    for world_name, world_cfg in WORLDS.items():
        missing = [f for f in required if f not in world_cfg]
        if missing:
            fail(f"World {world_name}", f"Missing fields: {missing}")
            all_ok = False
    if all_ok:
        ok(f"All worlds have required fields ({', '.join(required[:3])}...)")


def test_constants_colors():
    """Verify key color constants exist and are RGB tuples"""
    from constants import WHITE, BLACK, RED, GREEN, BLUE, YELLOW

    colors = {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "BLUE": BLUE, "YELLOW": YELLOW}
    all_ok = True
    for name, color in colors.items():
        if not isinstance(color, tuple) or len(color) != 3:
            fail(f"Color {name}", f"Expected 3-tuple, got {color}")
            all_ok = False
        elif not all(0 <= c <= 255 for c in color):
            fail(f"Color {name}", f"Values out of range: {color}")
            all_ok = False
    if all_ok:
        ok(f"All {len(colors)} color constants are valid RGB tuples")


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    print(f"\n{'═' * 60}")
    print(f"  SI3LN Game Python Unit Tests")
    print(f"  (Offline — no server needed)")
    print(f"{'═' * 60}")

    section("1 · utils.py")
    test_validate_email_valid()
    test_validate_email_invalid()
    test_hash_password()
    test_hash_password_not_plaintext()
    test_clamp()

    section("2 · auth.py (AuthSystem)")
    test_auth_register_success()
    test_auth_register_duplicate()
    test_auth_register_short_username()
    test_auth_register_short_password()
    test_auth_register_invalid_email()
    test_auth_login_success()
    test_auth_login_wrong_password()
    test_auth_login_nonexistent_user()
    test_auth_guest_mode()
    test_auth_logout()
    test_auth_change_password_success()
    test_auth_change_password_wrong_old()
    test_auth_change_password_too_short()
    test_auth_change_username()
    test_auth_change_username_duplicate()
    test_auth_change_username_too_short()
    test_auth_is_username_available()
    test_auth_get_user_data()
    test_auth_get_user_data_guest()
    test_auth_update_user_data()
    test_auth_update_user_data_guest()
    test_auth_persistence()

    section("3 · scores.py (ScoreManager)")
    test_scores_add_and_rank()
    test_scores_guest_rejected()
    test_scores_top_20_limit()
    test_scores_get_top_with_limit()
    test_scores_sorted_descending()
    test_scores_get_user_best()
    test_scores_get_user_best_nonexistent()
    test_scores_is_high_score()
    test_scores_get_rank()
    test_scores_persistence()

    section("4 · api_client.py (APIClient)")
    test_jwt_field_decode()
    test_jwt_field_malformed()
    test_api_client_set_token()
    test_api_client_not_authenticated()
    test_api_client_headers()
    test_api_client_start_session_no_auth()
    test_api_client_end_session_no_auth()
    test_api_client_get_leaderboard_fallback()

    section("5 · constants.py")
    test_constants_worlds_config()
    test_constants_world_fields()
    test_constants_colors()

    # Summary
    print(f"\n{'═' * 60}")
    total = 43
    failed = len(errors)
    warned = len(warnings)
    passed = total - failed
    if failed == 0:
        print(f"  \033[92mAll {passed} game unit tests passed\033[0m", end="")
        if warned:
            print(f" ({warned} warning(s))")
        else:
            print()
    else:
        print(f"  \033[91m{failed}/{total} game unit test(s) FAILED:\033[0m")
        for e in errors:
            print(f"    • {e}")
        if warned:
            print(f"  \033[93m{warned} warning(s)\033[0m")
    print(f"{'═' * 60}\n")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
