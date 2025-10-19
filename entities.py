"""
Game entities: Player, Enemy, Bullet
"""
import pygame
import random
from constants import *


class Player(pygame.sprite.Sprite):
    """Player entity"""
    def __init__(self, x, y, image, screen_width, screen_height):
        super().__init__()
        self.image = image
        self.original_image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.speed = PLAYER_SPEED
        
        # Play area boundaries (keep player in visible area)
        self.min_x = 0
        self.max_x = screen_width
        self.min_y = screen_height // 2  # Can't go above middle
        self.max_y = screen_height - 20
    
    def move(self, dx, dy):
        """Move player with boundary checking"""
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        
        # Keep within boundaries
        self.rect.x = max(self.min_x, min(self.rect.x, self.max_x - self.rect.width))
        self.rect.y = max(self.min_y, min(self.rect.y, self.max_y - self.rect.height))
    
    def update(self, keys):
        """Update player based on key presses"""
        dx = 0
        dy = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        
        if dx != 0 or dy != 0:
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            self.move(dx, dy)


class Enemy(pygame.sprite.Sprite):
    """Enemy entity"""
    def __init__(self, x, y, image, screen_width, level=1):
        super().__init__()
        self.image = image
        self.original_image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.screen_width = screen_width
        
        # Movement
        self.speed = ENEMY_SPEED + (level * 0.2)
        self.direction = 1
        self.drop_distance = 20
        
        # Shooting
        self.last_shot = pygame.time.get_ticks()
        self.shoot_cooldown = max(1000, 2500 - level * 150)  # Faster shooting at higher levels
        self.shoot_chance = min(0.03 * level, 0.15)  # Max 15% chance per frame
        
        # Boundaries (enemy play area)
        self.min_x = 20
        self.max_x = screen_width - 20
        self.max_y = screen_width // 2  # Don't go too low
    
    def update(self):
        """Update enemy position"""
        # Horizontal movement
        self.rect.x += self.speed * self.direction
        
        # Boundary checking and direction change
        if self.rect.right >= self.max_x and self.direction > 0:
            self.direction = -1
            self.rect.y += self.drop_distance
        elif self.rect.left <= self.min_x and self.direction < 0:
            self.direction = 1
            self.rect.y += self.drop_distance
        
        # Keep within vertical bounds
        if self.rect.bottom > self.max_y:
            self.rect.bottom = self.max_y
    
    def can_shoot(self):
        """Check if enemy can shoot"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_cooldown:
            if random.random() < self.shoot_chance:
                self.last_shot = current_time
                return True
        return False


class Bullet(pygame.sprite.Sprite):
    """Bullet entity"""
    def __init__(self, x, y, image, is_player_bullet, screen_height):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.is_player_bullet = is_player_bullet
        self.screen_height = screen_height
        
        if is_player_bullet:
            self.speed = -PLAYER_BULLET_SPEED  # Negative = upward
        else:
            self.speed = ENEMY_BULLET_SPEED  # Positive = downward
    
    def update(self):
        """Update bullet position"""
        self.rect.y += self.speed
        
        # Remove if off screen
        if self.rect.bottom < 0 or self.rect.top > self.screen_height:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """Simple explosion effect"""
    def __init__(self, x, y, color=ORANGE, explosion_img=None):
        super().__init__()
        self.frames = []
        
        if explosion_img:
            # Use provided explosion image with scaling animation
            for scale in [0.3, 0.6, 1.0, 0.8, 0.5, 0.2]:
                w, h = explosion_img.get_size()
                new_w = int(w * scale)
                new_h = int(h * scale)
                if new_w > 0 and new_h > 0:
                    surf = pygame.transform.scale(explosion_img, (new_w, new_h))
                    self.frames.append(surf)
        else:
            # Create explosion animation frames with circles (fallback)
            for size in [10, 20, 30, 25, 15, 5]:
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (size, size), size)
                self.frames.append(surf)
        
        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.animation_speed = 3
        self.counter = 0
    
    def update(self):
        """Update explosion animation"""
        self.counter += 1
        if self.counter >= self.animation_speed:
            self.counter = 0
            self.current_frame += 1
            
            if self.current_frame >= len(self.frames):
                self.kill()
            else:
                old_center = self.rect.center
                self.image = self.frames[self.current_frame]
                self.rect = self.image.get_rect(center=old_center)


class PowerUp(pygame.sprite.Sprite):
    """Power-up collectible (future feature)"""
    def __init__(self, x, y, power_type="health"):
        super().__init__()
        self.power_type = power_type
        
        # Create visual
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        color = GREEN if power_type == "health" else CYAN
        pygame.draw.circle(self.image, color, (15, 15), 15)
        pygame.draw.circle(self.image, WHITE, (15, 15), 15, 2)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2
    
    def update(self):
        """Move power-up down"""
        self.rect.y += self.speed
        if self.rect.top > 800:  # Off screen
            self.kill()
