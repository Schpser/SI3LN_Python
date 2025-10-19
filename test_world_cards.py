"""Test script for world card display"""
import pygame
from constants import *
from level_selector import LevelSelector

pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Test World Cards")

selector = LevelSelector(screen, WORLDS)
selector.open()

print("World backgrounds loaded:")
for world, bg in selector.world_backgrounds.items():
    print(f"  {world}: {bg}")

print("\nWorld cards created:")
for i, card in enumerate(selector.world_cards):
    print(f"  Card {i}: {card.world_name}, bg_image={card.bg_image is not None}")

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        
        result = selector.handle_event(event)
        if result:
            print(f"Result: {result}")
    
    selector.update()
    
    screen.fill((20, 20, 40))
    selector.draw()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
