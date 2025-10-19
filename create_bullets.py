#!/usr/bin/env python3
"""
Script pour créer/modifier les sprites des balles
Modifie les couleurs ci-dessous selon tes préférences !
"""
import pygame
import sys

pygame.init()

# ==========================================
# 🎨 MODIFIE LES COULEURS ICI
# ==========================================

# Couleurs pour la balle du JOUEUR
PLAYER_BULLET_COLOR_1 = (255, 100, 0)   # Orange foncé (contour)
PLAYER_BULLET_COLOR_2 = (255, 200, 0)   # Jaune/Orange clair (intérieur)

# Couleurs pour la balle des ENNEMIS  
ENEMY_BULLET_COLOR_1 = (0, 255, 100)    # Vert (contour)
ENEMY_BULLET_COLOR_2 = (0, 255, 200)    # Cyan (intérieur)

# ==========================================
# Exemples de couleurs que tu peux utiliser:
# Rouge vif:     (255, 0, 0)
# Bleu vif:      (0, 100, 255)
# Jaune:         (255, 255, 0)
# Rose:          (255, 100, 200)
# Violet:        (150, 0, 255)
# Cyan:          (0, 255, 255)
# Blanc:         (255, 255, 255)
# Orange:        (255, 150, 0)
# ==========================================

# Créer bullet joueur
bullet = pygame.Surface((8, 20), pygame.SRCALPHA)
pygame.draw.ellipse(bullet, PLAYER_BULLET_COLOR_1, (0, 0, 8, 20))
pygame.draw.ellipse(bullet, PLAYER_BULLET_COLOR_2, (1, 2, 6, 16))
pygame.image.save(bullet, 'assets/sprites/player/player_bullet.png')

# Créer bullet ennemi
enemy_bullet = pygame.Surface((8, 20), pygame.SRCALPHA)
pygame.draw.ellipse(enemy_bullet, ENEMY_BULLET_COLOR_1, (0, 0, 8, 20))
pygame.draw.ellipse(enemy_bullet, ENEMY_BULLET_COLOR_2, (1, 2, 6, 16))
pygame.image.save(enemy_bullet, 'assets/sprites/ennemy/enemy_bullet.png')

print('✓ Balles créées avec succès!')
print(f'  Balle joueur: {PLAYER_BULLET_COLOR_1} / {PLAYER_BULLET_COLOR_2}')
print(f'  Balle ennemi: {ENEMY_BULLET_COLOR_1} / {ENEMY_BULLET_COLOR_2}')
print('\nRelance le jeu pour voir les changements!')
