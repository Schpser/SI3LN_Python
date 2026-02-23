import pygame
import os
import sys
import asyncio

os.environ['SDL_AUDIODRIVER'] = 'dummy'

try:
    from game import Game 
except ImportError:
    print("Attention: Assurez-vous que le code de la classe Game est soit dans ce fichier, soit dans 'game.py'.")
    sys.exit(1)


async def main():
    pygame.init() 

    game = Game()
    await game.run()

if __name__ == "__main__":
    asyncio.run(main())
