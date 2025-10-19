"""
Development Guide for SI3LN Game
Tips and patterns for extending the game
"""

# ============================================
# ADDING A NEW WORLD
# ============================================

"""
1. Add world assets:
   - Create folder: assets/enemies/YourWorld_world/
   - Add enemy images: enemy_1.png, enemy_2.png, etc.
   - Add background: assets/worlds/background_yourworld.jpg

2. Update constants.py:

WORLDS = {
    "Space": {...},
    "YourWorld": {
        "name": "Your World Name",
        "background": "background_yourworld.jpg",
        "levels": 10,  # Number of levels
        "enemies_dir": "YourWorld_world"
    }
}

3. (Optional) Add world-specific logic in game.py spawn_enemies()
"""

# ============================================
# ADDING A NEW ENEMY TYPE
# ============================================

"""
Create a new enemy class in entities.py:

class BossEnemy(Enemy):
    def __init__(self, x, y, image, screen_width, level=1):
        super().__init__(x, y, image, screen_width, level)
        self.health = 100  # Boss has health
        self.speed = 0.5   # Slower
        self.shoot_cooldown = 500  # Faster shooting
    
    def take_damage(self, damage=10):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True  # Boss defeated
        return False

Then use it in game.py:
    if self.current_level % 5 == 0:  # Boss every 5 levels
        boss = BossEnemy(x, y, boss_image, self.screen_width, self.current_level)
        self.enemies.add(boss)
"""

# ============================================
# ADDING POWER-UPS
# ============================================

"""
1. PowerUp class already exists in entities.py
2. Spawn power-ups when enemies are destroyed:

In game.py check_collisions():
    for enemy in hits:
        # Random chance to drop power-up
        if random.random() < 0.1:  # 10% chance
            power_type = random.choice(["health", "speed", "multishot"])
            powerup = PowerUp(enemy.rect.centerx, enemy.rect.centery, power_type)
            self.powerups.add(powerup)

3. Collect power-ups:
    # In update_gameplay()
    powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
    for powerup in powerup_hits:
        if powerup.power_type == "health":
            self.lives += 1
        elif powerup.power_type == "speed":
            self.player.speed *= 1.5
        elif powerup.power_type == "multishot":
            self.multishot_timer = 300  # 5 seconds at 60 FPS
"""

# ============================================
# ADDING SOUND EFFECTS
# ============================================

"""
1. Remove SDL_AUDIODRIVER=dummy from main.py

2. Load sounds in game.py load_assets():
    self.shoot_sound = pygame.mixer.Sound("assets/sounds/shoot.wav")
    self.explosion_sound = pygame.mixer.Sound("assets/sounds/explosion.wav")
    self.music = pygame.mixer.music.load("assets/sounds/music.mp3")
    pygame.mixer.music.play(-1)  # Loop forever

3. Play sounds:
    self.shoot_sound.play()
    self.explosion_sound.play()
"""

# ============================================
# ADDING ACHIEVEMENTS
# ============================================

"""
1. Create achievements.py:

class AchievementSystem:
    def __init__(self):
        self.achievements = {
            "first_kill": {"name": "First Blood", "unlocked": False},
            "level_5": {"name": "Survivor", "unlocked": False},
            "perfect": {"name": "Perfect", "unlocked": False}
        }
    
    def check_achievement(self, key, condition):
        if key in self.achievements and not self.achievements[key]["unlocked"]:
            if condition:
                self.achievements[key]["unlocked"] = True
                return self.achievements[key]["name"]
        return None

2. Use in game.py:
    # After killing first enemy
    ach = self.achievements.check_achievement("first_kill", True)
    if ach:
        self.show_message(f"Achievement: {ach}!", YELLOW, 300)
"""

# ============================================
# SAVING GAME PROGRESS
# ============================================

"""
In auth.py, add to user data:

def save_progress(self, world, level):
    if not self.current_user or self.guest_mode:
        return
    
    if "progress" not in self.users[self.current_user]:
        self.users[self.current_user]["progress"] = {}
    
    if world not in self.users[self.current_user]["progress"]:
        self.users[self.current_user]["progress"][world] = 0
    
    self.users[self.current_user]["progress"][world] = max(
        self.users[self.current_user]["progress"][world], level
    )
    
    self.save_users()

def get_max_level_unlocked(self, world):
    if self.guest_mode or not self.current_user:
        return 1
    return self.users[self.current_user].get("progress", {}).get(world, 1)
"""

# ============================================
# DEBUGGING TIPS
# ============================================

"""
1. Enable debug mode:
   In constants.py:
   DEBUG = True

2. Show collision boxes:
   In game.py draw_gameplay():
   if DEBUG:
       for enemy in self.enemies:
           pygame.draw.rect(self.screen, RED, enemy.rect, 1)
       if self.player:
           pygame.draw.rect(self.screen, GREEN, self.player.rect, 1)

3. Show FPS:
   fps = int(self.clock.get_fps())
   fps_text = self.font_tiny.render(f"FPS: {fps}", True, WHITE)
   self.screen.blit(fps_text, (10, 10))

4. Print game state:
   Press 'D' to print debug info:
   if event.key == pygame.K_d:
       print(f"State: {self.state}")
       print(f"Score: {self.current_score}")
       print(f"Enemies: {len(self.enemies)}")
       print(f"Lives: {self.lives}")
"""

# ============================================
# OPTIMIZING PERFORMANCE
# ============================================

"""
1. Use sprite groups efficiently:
   - Don't iterate over all sprites every frame
   - Use sprite.update() for group updates

2. Limit bullet count:
   Already implemented with MAX_PLAYER_BULLETS

3. Remove off-screen entities:
   Already implemented in Bullet.update()

4. Use dirty sprite rendering:
   pygame.sprite.RenderUpdates() instead of Group()

5. Optimize collision detection:
   Use spatial partitioning for many entities:
   
   def get_nearby_enemies(self, player_rect, radius=200):
       nearby = []
       for enemy in self.enemies:
           if player_rect.collidepoint(enemy.rect.center):
               nearby.append(enemy)
       return nearby
"""

# ============================================
# TESTING CHECKLIST
# ============================================

"""
Before release, test:

□ All menu navigation paths
□ Account creation with various inputs
□ Login with correct/incorrect credentials
□ Guest mode functionality
□ Profile modification (character, username, password)
□ All level transitions
□ Game over handling
□ Score saving and leaderboard
□ Window resize and fullscreen
□ All keyboard controls
□ All button clicks
□ Collision detection
□ Enemy spawning and behavior
□ Bullet limits and cooldowns
□ Lives system
□ Score calculation
"""

print("See source code for development patterns and examples!")
