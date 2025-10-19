#!/usr/bin/env python3
"""
Asset verification script for SI3LN Game
Checks if all required assets are present
"""
import os
from constants import ASSETS_DIR, WORLDS

def check_file(path, required=True):
    """Check if a file exists"""
    full_path = os.path.join(ASSETS_DIR, path)
    exists = os.path.exists(full_path)
    
    status = "✓" if exists else ("✗ REQUIRED" if required else "✗ optional")
    print(f"  {status} {path}")
    
    return exists

def main():
    print("=" * 60)
    print("SI3LN Asset Verification")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Check backgrounds
    print("📸 BACKGROUNDS:")
    for world_key, world_data in WORLDS.items():
        bg_file = f"worlds/{world_data['background']}"
        if not check_file(bg_file, required=True):
            all_good = False
    
    check_file("worlds/home_page.jpg", required=True)
    print()
    
    # Check players
    print("👽 PLAYER CHARACTERS:")
    player_files = [
        "players/1000055338.png",
        "players/1000055339.png",
        "players/1000055340.png",
        "players/1000055341.png",
        "players/1000055342.png",
        "players/1000055343.png",
        "players/1000055344.png",
        "players/1000055345.png",
    ]
    
    for player_file in player_files:
        if not check_file(player_file, required=False):
            pass  # Optional
    print()
    
    # Check enemies
    print("👾 ENEMIES:")
    for world_key, world_data in WORLDS.items():
        enemies_dir = world_data['enemies_dir']
        print(f"  World: {world_data['name']}")
        for i in range(1, 6):
            enemy_file = f"enemies/{enemies_dir}/enemy_{i}.png"
            if not check_file(enemy_file, required=True):
                all_good = False
    print()
    
    # Check sprites
    print("💫 SPRITES:")
    check_file("sprites/player/player_bullet.png", required=True)
    check_file("sprites/ennemy/enemy_bullet.png", required=True)
    print()
    
    # Check directories
    print("📁 DIRECTORIES:")
    dirs = [
        "players",
        "enemies",
        "sprites",
        "sprites/player",
        "sprites/ennemy",
        "worlds",
        "fonts",
    ]
    
    for dir_name in dirs:
        full_path = os.path.join(ASSETS_DIR, dir_name)
        exists = os.path.exists(full_path) and os.path.isdir(full_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_name}/")
        if not exists and dir_name not in ["fonts"]:
            all_good = False
    print()
    
    # Summary
    print("=" * 60)
    if all_good:
        print("✅ All required assets are present!")
        print("   The game should work correctly.")
    else:
        print("⚠️  Some required assets are missing!")
        print("   The game may not work properly.")
        print()
        print("RECOMMENDATION:")
        print("  - Check the assets/ directory")
        print("  - Make sure all images are in place")
        print("  - Fallback colored rectangles will be used for missing assets")
    print("=" * 60)
    
    return all_good

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
