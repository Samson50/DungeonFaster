# Main.py
import pygame
import sys

from location import Location
from pygame.locals import *


# Placeholders
zoom = 1.0
x_offset = 0
y_offset = 0


def main():
    clock = pygame.time.Clock()
    # initialize window
    surface = pygame.display.set_mode((1000, 1000))
    # create surface

    # call map
    # current_map = HexMap("chult/chult.ppm", 427, 454, 77, "chult/chult.hexes")
    # current_map = GridMap("chult/camp_righteous/camp_righteous.ppm", 133, 143, 57.8, None)
    location = Location("resources/locations/chult")

    while True:
        try:
            surface.fill((0, 0, 0))
            # Display
            location.draw(surface)

            # Events
            events = pygame.event.get()

            location.update(events, surface)

            # Input
            for event in events:
                if event.type == QUIT:
                    location.save()
                    sys.exit(0)

            pygame.display.update()
            clock.tick(20)

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            location.save()
            sys.exit(0)
        except Exception as e:
            print(str(e))
            sys.exit(1)


if __name__ == "__main__":
    pygame.init()
    main()
