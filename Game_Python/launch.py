#!/usr/bin/env python3
"""
Quick launch script for SI3LN Game
Performs pre-flight checks before launching
"""
import os
import sys

def main():
    print("=" * 60)
    print("🚀 SI3LN - Space Invaders III Last Night")
    print("=" * 60)
    print()
    
    # Check Python version
    print("Checking Python version...", end=" ")
    if sys.version_info < (3, 7):
        print("❌")
        print("ERROR: Python 3.7+ required")
        print(f"Current: Python {sys.version}")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check pygame
    print("Checking Pygame...", end=" ")
    try:
        import pygame
        print(f"✓ Pygame {pygame.version.ver}")
    except ImportError:
        print("❌")
        print("ERROR: Pygame not installed")
        print("Install with: pip install pygame")
        return False
    
    # Check modules
    print("Checking game modules...", end=" ")
    required_modules = [
        "constants", "utils", "auth", "scores", 
        "entities", "ui_components", "profile", 
        "level_selector", "game"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            print("❌")
            print(f"ERROR: Failed to import {module}")
            print(f"Details: {e}")
            return False
    print("✓ All modules OK")
    
    # Check assets
    print("Checking assets...", end=" ")
    from constants import ASSETS_DIR
    if not os.path.exists(ASSETS_DIR):
        print("⚠️  Assets directory missing")
    else:
        print("✓ Assets found")
    
    # Check data directory
    print("Checking data directory...", end=" ")
    from constants import DATA_DIR
    if not os.path.exists(DATA_DIR):
        print("⚠️  Creating data directory...")
        os.makedirs(DATA_DIR, exist_ok=True)
    print("✓ Data directory ready")
    
    print()
    print("=" * 60)
    print("✅ All checks passed! Launching game...")
    print("=" * 60)
    print()
    print("Controls:")
    print("  - Movement: Arrow keys or WASD")
    print("  - Shoot: SPACE")
    print("  - Fullscreen: F11")
    print("  - Quit/Pause: ESC")
    print()
    print("Have fun! 🎮")
    print()
    
    # Launch game
    try:
        from game import Game
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for playing!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
