import pygame
import math

from map.map import Map

# 560, 485
HEX = pygame.image.load("resources/maps/hexes.png")

HIGHLIGHT = pygame.image.load("resources/maps/highlight.png")


class HexMap(Map):
    def __init__(self, image_file, x_margin, y_margin, pixel_density, hex_file=None, path=""):
        super().__init__(image_file, x_margin, y_margin, pixel_density, hex_file, path)

    def initialize_grid(self, hex_file):
        self.grid_x = int((self.width - 2 * self.x_margin) / (2 * self.pixel_density))
        self.grid_y = int((self.height - 2 * self.y_margin) / (math.sqrt(3) * self.pixel_density / 2))

        if not hex_file:
            self.grid_file = "test.txt"
            self.grid_matrix = [[0 for i in range(self.grid_x)] for j in range(self.grid_y)]
        else:
            self.grid_file = self.path + hex_file
            self.grid_matrix = self.read_grid_file()

    def scale_tiles(self):
        scale = (2.0 * self.pixel_density) / HEX.get_width()
        self.grid_image = pygame.transform.scale(
            HEX,
            (int(HEX.get_width() * scale), int(HEX.get_height() * scale))
        )
        self.highlight_image = pygame.transform.scale(
            HIGHLIGHT,
            (int(HEX.get_width() * scale), int(HEX.get_height() * scale))
        )

    def index_to_pixel(self, x, y):
        if y % 2 == 0:
            grid_x = x * 3 * self.pixel_density
            grid_y = y * math.sqrt(3) * self.pixel_density / 2
        else:
            grid_x = x * 3 * self.pixel_density + 3 * self.pixel_density / 2
            grid_y = y * math.sqrt(3) * self.pixel_density / 2

        grid_x = int((grid_x + self.x_margin - self.x_offset) * self.zoom)
        grid_y = int((grid_y + self.y_margin - self.y_offset) * self.zoom)

        return grid_x, grid_y

    def get_grid(self, x, y):
        x = int(x / self.zoom) + self.x_offset
        y = int(y / self.zoom) + self.y_offset

        if x < self.x_margin or y < self.y_margin:
            return None
        if ((x - self.x_margin) % (self.pixel_density * 3 / 2)) <= self.pixel_density / 2:
            return None

        x -= self.x_margin
        y -= self.y_margin

        x_mod = int(x / (self.pixel_density * 3 / 2))
        if x_mod % 2 == 0:
            return [int(x_mod / 2), int(y / (math.sqrt(3) * self.pixel_density))*2]
        else:
            return [int((x_mod - 1) / 2), int((y / (math.sqrt(3)*self.pixel_density) - 0.5))*2+1]

    def update_zoom(self):
        scale = (2.0 * self.pixel_density) / HEX.get_width() * self.zoom

        self.grid_image = pygame.transform.scale(
            HEX,
            (int(HEX.get_width() * scale), int(HEX.get_height() * scale))
        )
        self.highlight_image = pygame.transform.scale(
            HIGHLIGHT,
            (int(HEX.get_width() * scale), int(HEX.get_height() * scale))
        )

        self.image = pygame.transform.scale(
            self.original,
            (int(self.width * self.zoom), int(self.height * self.zoom))
        )

    def shift_right(self):
        self.x_offset += self.pixel_density * 2
        if self.x_offset < 0:
            self.x_offset = 0

    def shift_left(self):
        self.x_offset -= self.pixel_density * 2
        if self.x_offset < 0:
            self.x_offset = 0

    def shift_up(self):
        self.y_offset -= math.sqrt(3) * self.pixel_density
        if self.y_offset < 0:
            self.y_offset = 0

    def shift_down(self):
        self.y_offset += math.sqrt(3) * self.pixel_density

    def zoom_in(self):
        self.zoom += 0.1
        self.update_zoom()

    def zoom_out(self):
        self.zoom -= 0.1
        if self.zoom <= 0:
            self.zoom = 0.1
        self.update_zoom()


if __name__ == "__main__":
    print("Working")
