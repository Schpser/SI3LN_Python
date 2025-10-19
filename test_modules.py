"""
Quick test script to verify all modules load correctly
"""
import os
import sys

os.environ['SDL_AUDIODRIVER'] = 'dummy'

print("Testing SI3LN Game modules...")
print("-" * 50)

# Test imports
try:
    print("✓ Testing constants.py...", end=" ")
    import constants
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing utils.py...", end=" ")
    import utils
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing auth.py...", end=" ")
    from auth import AuthSystem
    auth = AuthSystem()
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing scores.py...", end=" ")
    from scores import ScoreManager
    scores = ScoreManager()
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing entities.py...", end=" ")
    from entities import Player, Enemy, Bullet, Explosion
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing ui_components.py...", end=" ")
    from ui_components import Button, InputField, ProfileIcon, Panel
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing pygame...", end=" ")
    import pygame
    pygame.init()
    print(f"OK (version {pygame.version.ver})")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

try:
    print("✓ Testing game.py...", end=" ")
    from game import Game
    print("OK")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

print("-" * 50)
print("✅ All modules loaded successfully!")
print()

# Test auth system
print("Testing AuthSystem...")
auth = AuthSystem()

# Test registration
success, msg = auth.register("test_user", "test123", "test@example.com")
print(f"  Registration: {msg}")

# Test login
success, msg = auth.login("test_user", "test123")
print(f"  Login: {msg}")

# Test guest mode
success, msg = auth.login_as_guest(0)
print(f"  Guest mode: {msg}")

print()

# Test score system
print("Testing ScoreManager...")
score_mgr = ScoreManager()

# Add some test scores
pos, is_top = score_mgr.add_score("player1", 1000, 5)
print(f"  Added score: position={pos}, is_top_20={is_top}")

pos, is_top = score_mgr.add_score("player2", 1500, 7)
print(f"  Added score: position={pos}, is_top_20={is_top}")

print()

# Check file structure
print("Checking file structure...")
required_dirs = ["assets", "assets/players", "assets/enemies", "assets/sprites", "assets/worlds", "data"]
for dir_path in required_dirs:
    full_path = os.path.join(constants.BASE_DIR, dir_path)
    if os.path.exists(full_path):
        print(f"  ✓ {dir_path}")
    else:
        print(f"  ✗ {dir_path} (missing)")

print()
print("=" * 50)
print("🎮 Game is ready to launch!")
print("   Run: python3 main.py")
print("=" * 50)
