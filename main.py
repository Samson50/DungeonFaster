# Main.py
import pygame
import sys
# import argparse

from location.location import Location
from pygame.locals import *


# Placeholders
zoom = 1.0
x_offset = 0
y_offset = 0


def main(game_dir):
    clock = pygame.time.Clock()
    # initialize window
    width = 1000
    height = 1000
    surface = pygame.display.set_mode((width, height), RESIZABLE)
    # create surface

    # call map
    # current_map = HexMap("chult/chult.ppm", 427, 454, 77, "chult/chult.hexes")
    # current_map = GridMap("chult/camp_righteous/camp_righteous.ppm", 133, 143, 57.8, None)
    current_location = Location(game_dir)

    while True:
        try:
            surface.fill((0, 0, 0))
            # Display
            current_location.draw(surface)

            # Events
            events = pygame.event.get()

            current_location = current_location.update(events, surface)

            # Input
            for event in events:
                if event.type == KEYDOWN:
                    """
                    if event.key == K_F11:
                        flags = surface.get_flags()
                        if flags & FULLSCREEN:
                            surface = pygame.display.set_mode((width, height), RESIZABLE)
                        else:
                            surface = pygame.display.set_mode((0, 0), FULLSCREEN)
                    """
                    if event.key == K_ESCAPE:
                        current_location.save()
                        sys.exit(0)
                if event.type == QUIT:
                    current_location.save()
                    sys.exit(0)
                if event.type == pygame.VIDEORESIZE:
                    width = event.w
                    height = event.h
                    surface = pygame.display.set_mode((width, height), RESIZABLE)

            pygame.display.update()
            clock.tick(20)

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            current_location.save()
            sys.exit(0)
        except Exception as e:
            print(str(e))
            sys.exit(1)


if __name__ == "__main__":
    pygame.init()

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('game_dir', type=str, nargs=1)

    args = parser.parse_args()

    print(args.game_dir)
    """
    game_dir_arg = "example/chult"

    main(game_dir_arg)
