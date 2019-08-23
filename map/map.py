import pygame
import json


class Map:
    def __init__(self, image_file, x_margin, y_margin, pixel_density, grid_file=None, path=""):  # margin  asdf
        self.path = path
        self.image = pygame.image.load(path + image_file)
        self.original = pygame.image.load(path + image_file)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        self.x_margin = x_margin
        self.y_margin = y_margin

        self.x_offset = 0
        self.y_offset = 0
        self.zoom = 1

        self.pixel_density = pixel_density

        self.grid_x = None
        self.grid_y = None
        self.grid_file = None
        self.grid_matrix = None
        self.initialize_grid(grid_file)

        self.grid_image = None
        self.highlight_image = None
        self.scale_tiles()

    def load(self, load_json):
        self.x_offset = load_json["x_offset"]
        self.y_offset = load_json["y_offset"]
        self.zoom = load_json["zoom"]
        self.grid_matrix = load_json["grid_matrix"]

        self.update_zoom()

    def save(self, save_file):
        save_data = {
            "x_offset": self.x_offset,
            "y_offset": self.y_offset,
            "zoom": self.zoom,
            "grid_matrix": self.grid_matrix
        }

        save_file.write(json.dumps(save_data))

    def initialize_grid(self, grid_file):
        pass

    def scale_tiles(self):
        pass

    def read_grid_file(self):
        with open(self.grid_file, 'r') as grid_file:
            grid_data = grid_file.read()
            grid_data = [[int(y) for y in x.split(',')] for x in grid_data.split('\n')]
            return grid_data

    def write_grid_file(self):
        grid_data = '\n'.join([','.join([str(y) for y in x]) for x in self.grid_matrix])
        with open(self.grid_file, 'w+') as grid_file:
            grid_file.write(grid_data)

    def draw_grid(self, surface, x, y):
        grid_x, grid_y = self.index_to_pixel(x, y)

        surface.blit(
            self.grid_image, (
                grid_x,
                grid_y
            )
        )

    def highlight_grid(self, surface, x, y):
        grid_x, grid_y = self.index_to_pixel(x, y)

        surface.blit(
            self.highlight_image, (
                grid_x,
                grid_y
            )
        )

    def draw_grids(self, surface):
        for x in range(self.grid_x):
            for y in range(self.grid_y):
                if self.grid_matrix[y][x] == 1:
                    self.draw_grid(surface, x, y)

    def draw(self, surface):
        surface.blit(self.image, (-int(self.x_offset * self.zoom), -int(self.y_offset * self.zoom)))
        self.draw_grids(surface)

    def flip_grid(self, x, y):
        selected_grid = self.get_grid(x, y)

        if not selected_grid:
            return

        matrix_grid = self.grid_matrix[selected_grid[1]][selected_grid[0]]

        if matrix_grid == 0:
            self.grid_matrix[selected_grid[1]][selected_grid[0]] = 1
        else:
            self.grid_matrix[selected_grid[1]][selected_grid[0]] = 0

    def index_to_pixel(self, x, y):
        return None, None

    def get_grid(self, x, y):
        pass

    def update_zoom(self):
        pass

    def shift_right(self):
        pass

    def shift_left(self):
        pass

    def shift_up(self):
        pass

    def shift_down(self):
        pass

    def zoom_in(self):
        pass

    def zoom_out(self):
        pass

