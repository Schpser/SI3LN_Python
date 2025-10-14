import pygame
import os
import sys

os.environ['SDL_AUDIODRIVER'] = 'dummy'

try:
    from game import Game 
except ImportError:
    print("Attention: Assurez-vous que le code de la classe Game est soit dans ce fichier, soit dans 'game.py'.")
    sys.exit(1)


def main():
    pygame.init() 

    game = Game()
    game.run()

if __name__ == "__main__":
    main()
