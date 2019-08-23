import pygame

from map.map import Map

# 730, 730
GRID = pygame.image.load("resources/maps/grid.png")

HIGHLIGHT = pygame.image.load("resources/maps/highlight_grid.png")


class GridMap(Map):
    def __init__(self, image_file, x_margin, y_margin, pixel_density, hex_file=None, path=""):
        super().__init__(image_file, x_margin, y_margin, pixel_density, hex_file, path)

    def initialize_grid(self, hex_file):
        self.grid_x = int((self.width - 2 * self.x_margin) / self.pixel_density)
        self.grid_y = int((self.height - 2 * self.y_margin) / self.pixel_density)

        if not hex_file:
            self.grid_file = "test.txt"
            self.grid_matrix = [[0 for i in range(self.grid_x)] for j in range(self.grid_y)]
        else:
            self.grid_file = self.path + hex_file
            self.grid_matrix = self.read_grid_file()

    def scale_tiles(self):
        scale = self.pixel_density / GRID.get_width()
        self.grid_image = pygame.transform.scale(
            GRID,
            (int(GRID.get_width() * scale), int(GRID.get_height() * scale))
        )
        self.highlight_image = pygame.transform.scale(
            HIGHLIGHT,
            (int(GRID.get_width() * scale), int(GRID.get_height() * scale))
        )

    def index_to_pixel(self, x, y):
        grid_x = x * self.pixel_density
        grid_y = y * self.pixel_density

        grid_x = int((grid_x + self.x_margin - self.x_offset) * self.zoom)
        grid_y = int((grid_y + self.y_margin - self.y_offset) * self.zoom)

        return grid_x, grid_y

    def get_grid(self, x, y):
        x = int(x / self.zoom) + self.x_offset
        y = int(y / self.zoom) + self.y_offset

        if x < self.x_margin or y < self.y_margin:
            return None

        x -= self.x_margin
        y -= self.y_margin

        grid_x = x / self.pixel_density
        grid_y = y / self.pixel_density

        return [int(grid_x), int(grid_y)]

    def update_zoom(self):
        scale = self.pixel_density / GRID.get_width() * self.zoom

        self.grid_image = pygame.transform.scale(
            GRID,
            (int(GRID.get_width() * scale), int(GRID.get_height() * scale))
        )
        self.highlight_image = pygame.transform.scale(
            HIGHLIGHT,
            (int(GRID.get_width() * scale), int(GRID.get_height() * scale))
        )

        self.image = pygame.transform.scale(
            self.original,
            (int(self.width * self.zoom), int(self.height * self.zoom))
        )

    def shift_right(self):
        self.x_offset += self.pixel_density
        if self.x_offset < 0:
            self.x_offset = 0

    def shift_left(self):
        self.x_offset -= self.pixel_density
        if self.x_offset < 0:
            self.x_offset = 0

    def shift_up(self):
        self.y_offset -= self.pixel_density
        if self.y_offset < 0:
            self.y_offset = 0

    def shift_down(self):
        self.y_offset += self.pixel_density

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
