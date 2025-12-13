"""
Collision Manager for SI3LN Game
Handles all collision detection and resolution
"""
import pygame
import random
from constants import (
    ENEMY_PLAYER_COLLISION_DISTANCE,
    ENEMY_SPAWN_MIN_Y_THRESHOLD,
    BONUS_DROP_CHANCE,
    RED,
    STATE_GAME_OVER
)
# Explosion creation is handled by EntityManager


class CollisionManager:
    """Manages all collision detection and resolution"""
    
    def __init__(self, game):
        """
        Initialize collision manager
        
        Args:
            game: Reference to the Game instance for callbacks
        """
        self.game = game
    
    def check_all_collisions(self):
        """Check all types of collisions in the game"""
        self._check_bullet_enemy_collisions()
        self._check_bullet_player_collisions()
        self._check_enemy_player_collisions()
        self._check_bonus_player_collisions()
        self._check_special_attack_player_collisions()
    
    def _check_bullet_enemy_collisions(self):
        """Check collisions between player bullets and enemies"""
        for bullet in self.game.player_bullets:
            hits = pygame.sprite.spritecollide(bullet, self.game.enemies, True)
            if hits:
                bullet.kill()
                self.game.current_score += 10 * self.game.current_level
                
                for enemy in hits:
                    # Create explosion using entity manager
                    self.game.entity_manager.create_explosion(
                        enemy.rect.centerx,
                        enemy.rect.centery,
                        explosion_img=self.game.enemy_explosion_img
                    )
                    
                    # Chance to drop bonus
                    if random.random() < BONUS_DROP_CHANCE:
                        self.game.entity_manager.spawn_bonus(enemy.rect.centerx, enemy.rect.centery)
    
    def _check_bullet_player_collisions(self):
        """Check collisions between enemy bullets and player"""
        if not self.game.player:
            return
        
        hits = pygame.sprite.spritecollide(self.game.player, self.game.enemy_bullets, True)
        if hits:
            self.game.lives -= len(hits)
            
            if self.game.lives <= 0:
                # Player death - create explosion using entity manager
                self.game.entity_manager.create_explosion(
                    self.game.player.rect.centerx,
                    self.game.player.rect.centery,
                    RED,
                    explosion_img=self.game.player_explosion_img
                )
                self.game.player = None
                
                # Save score
                username = self.game.auth.current_user or "Guest"
                if username != "Guest":
                    self.game.score_manager.add_score(
                        username,
                        self.game.current_score,
                        self.game.current_level
                    )
                
                self.game.state = STATE_GAME_OVER
    
    def _check_enemy_player_collisions(self):
        """Check collisions between enemies and player"""
        if not self.game.player:
            return
        
        hits = pygame.sprite.spritecollide(self.game.player, self.game.enemies, False)
        for enemy in hits:
            # Calculate distance to prevent initial spawn collisions
            dx = self.game.player.rect.centerx - enemy.rect.centerx
            dy = self.game.player.rect.centery - enemy.rect.centery
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Only register collision if:
            # 1. Enemy is close enough
            # 2. Enemy is below middle screen (has dropped from spawn)
            min_spawn_y = self.game.screen_height // ENEMY_SPAWN_MIN_Y_THRESHOLD
            
            if distance < ENEMY_PLAYER_COLLISION_DISTANCE and enemy.rect.y > min_spawn_y:
                enemy.kill()
                self.game.lives -= 2
                
                if self.game.lives <= 0:
                    self.game.player = None
                    self.game.state = STATE_GAME_OVER
    
    def _check_bonus_player_collisions(self):
        """Check collisions between bonuses and player"""
        if not self.game.player:
            return
        
        collected_bonuses = pygame.sprite.spritecollide(
            self.game.player,
            self.game.bonuses,
            True
        )
        
        for bonus in collected_bonuses:
            self.game.activate_bonus(bonus.bonus_type)
    
    def _check_special_attack_player_collisions(self):
        """Check collisions between special attacks and player"""
        if not self.game.player:
            return
        
        for attack in self.game.special_attacks:
            if pygame.sprite.collide_rect(self.game.player, attack):
                if attack.world == "Space":
                    self.game.lives -= attack.damage
                    attack.kill()
                    
                    if self.game.lives <= 0:
                        self.game.player = None
                        self.game.state = STATE_GAME_OVER

