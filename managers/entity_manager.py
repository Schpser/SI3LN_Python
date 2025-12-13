"""
Entity Manager for SI3LN Game
Handles spawning, updating, and cleanup of game entities
"""
import pygame
import random
from constants import (
    MAX_PLAYER_BULLETS,
    ENEMY_SPAWN_BASE_ROWS,
    ENEMY_SPAWN_BASE_COLS,
    ENEMY_SPAWN_MAX_ROWS,
    ENEMY_SPAWN_MAX_COLS,
    ENEMY_SPACING_X,
    ENEMY_SPACING_Y,
    ENEMY_WIDTH,
    ENEMY_HEIGHT,
    ENEMY_SPAWN_START_Y
)
from entities import Enemy, Bullet, Bonus


class EntityManager:
    """Manages all game entities (spawning, updating, cleanup)"""
    
    def __init__(self, game):
        """
        Initialize entity manager
        
        Args:
            game: Reference to the Game instance
        """
        self.game = game
    
    def spawn_enemies(self):
        """Spawn enemies for the current level"""
        # Calculate grid size based on level
        rows = min(ENEMY_SPAWN_BASE_ROWS + self.game.current_level // 2, ENEMY_SPAWN_MAX_ROWS)
        cols = min(ENEMY_SPAWN_BASE_COLS + self.game.current_level // 2, ENEMY_SPAWN_MAX_COLS)
        
        # Calculate spacing
        total_width = cols * (ENEMY_WIDTH + ENEMY_SPACING_X)
        start_x = (self.game.screen_width - total_width) // 2
        start_y = ENEMY_SPAWN_START_Y
        
        # Spawn enemies in grid
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (ENEMY_WIDTH + ENEMY_SPACING_X) + ENEMY_WIDTH // 2
                y = start_y + row * (ENEMY_HEIGHT + ENEMY_SPACING_Y) + ENEMY_HEIGHT // 2
                
                # Select random enemy image for current world
                enemy_img = random.choice(self.game.enemy_images[self.game.current_world])
                enemy = Enemy(x, y, enemy_img, self.game.screen_width, self.game.current_level)
                self.game.enemies.add(enemy)
    
    def shoot_player_bullet(self):
        """Create a player bullet if conditions are met"""
        if self.game.player and len(self.game.player_bullets) < MAX_PLAYER_BULLETS:
            bullet = Bullet(
                self.game.player.rect.centerx,
                self.game.player.rect.top,
                self.game.player_bullet_img,
                True,
                self.game.screen_height
            )
            self.game.player_bullets.add(bullet)
    
    def shoot_mega_shot(self):
        """Create triple shot for mega shot bonus"""
        if not self.game.player:
            return
        
        # Triple shot with offset
        for i in range(-1, 2):
            bullet = Bullet(
                self.game.player.rect.centerx + i * 20,
                self.game.player.rect.top,
                self.game.player_bullet_img,
                True,
                self.game.screen_height
            )
            self.game.player_bullets.add(bullet)
    
    def spawn_bonus(self, x, y):
        """Spawn a random bonus at the specified position"""
        bonus_type = random.choice(["life", "shield", "mega_shot"])
        bonus = Bonus(x, y, bonus_type)
        self.game.bonuses.add(bonus)
    
    def create_explosion(self, x, y, color=None, explosion_img=None):
        """
        Create an explosion at the specified position
        
        Args:
            x: X coordinate
            y: Y coordinate
            color: Optional color for explosion
            explosion_img: Optional explosion image
            
        Returns:
            The created Explosion sprite
        """
        from entities import Explosion
        from constants import RED
        
        explosion = Explosion(
            x,
            y,
            color or RED,
            explosion_img=explosion_img
        )
        self.game.explosions.add(explosion)
        return explosion
    
    def cleanup_sprites(self):
        """Clean up and remove all dead sprites from all groups"""
        # Remove dead sprites from all groups
        sprite_groups = [
            self.game.enemies,
            self.game.player_bullets,
            self.game.enemy_bullets,
            self.game.explosions,
            self.game.bonuses,
            self.game.special_attacks
        ]
        
        for group in sprite_groups:
            for sprite in group:
                if not sprite.alive():
                    sprite.kill()

