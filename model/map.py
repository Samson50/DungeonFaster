import os
import numpy

from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle


class Map:
    def __init__(self, map_file: str = None):

        self.map_file = map_file
        self.image = None
        self.width = 0
        self.height = 0

        self.load_image(map_file)
        self.tile: Image = Image(source="resources/map/highlight_grid.png")

        # Offset of screen viewing map
        self.map_x_offset = 0
        self.map_y_offset = 0

        # How many box-width from the edges to leave without tiles
        self.x_margin = 1
        self.y_margin = 1

        # Number of pixels to offset the first grid
        self.grid_x_offset = 0
        self.grid_y_offset = 0
        self.zoom = 1

        self.pixel_density = 60

        # Number of grids on each axis we may need to display
        self.grid_x = None
        self.grid_y = None

        self.grid_file = None

        # Matrix of integers representing revealed/hidden grid tiles
        self.hidden_tiles = False
        self.grid_matrix = None
        self.update_grid()

        self.grid_image = None
        self.highlight_image = None
        self.scale_tiles()

    def load_image(self, map_file: str | os.PathLike):
        self.image = Image(source=map_file)
        (self.width, self.height) = self.image.texture.size

    def getZoomForSurface(self, surface: Widget):
        if self.height / surface.height > self.width / surface.width:
            self.zoom = self.width / surface.width
        else:
            self.zoom = self.height / surface.height

    def getSubTexture(self, surface: Widget):
        return self.image.texture.get_region(
            self.map_x_offset * self.zoom,
            self.map_y_offset * self.zoom,
            surface.width * self.zoom,
            surface.height * self.zoom,
        )

    def load(self, load_json):
        self.map_file = load_json["map_file"]
        self.grid_x_offset = load_json["grid_x_offset"]
        self.grid_y_offset = load_json["grid_y_offset"]
        self.x_margin = load_json["x_margin"]
        self.y_margin = load_json["y_margin"]
        self.pixel_density = load_json["pixel_density"]
        self.zoom = load_json["zoom"]
        self.grid_matrix = load_json["grid_matrix"]
        if len(self.grid_matrix) > 0:
            self.grid_x = len(self.grid_matrix)
            self.grid_y = len(self.grid_matrix[0])
        else:
            self.update_grid()
        self.hidden_tiles = load_json["hidden"]

        self.load_image(self.map_file)

    def save(self):
        save_data = {}
        save_data["map_file"] = self.map_file
        save_data["grid_x_offset"] = self.grid_x_offset
        save_data["grid_y_offset"] = self.grid_y_offset
        save_data["x_margin"] = self.x_margin
        save_data["y_margin"] = self.y_margin
        save_data["pixel_density"] = self.pixel_density
        save_data["zoom"] = self.zoom
        save_data["grid_matrix"] = self.grid_matrix
        save_data["hidden"] = self.hidden_tiles

        return save_data

    def update_grid(self):
        """
        Calculate the number of tiles available on the x and y axis from the size of
        the background image and the current width of each tile
        """

        self.grid_x = int(self.width / self.pixel_density - 2 * self.x_margin)
        self.grid_y = int(self.height / self.pixel_density - 2 * self.y_margin)
        self.grid_matrix = [[0 for y in range(self.grid_y)] for x in range(self.grid_x)]

    def scale_tiles(self):
        self.tile.size = (
            self.pixel_density / self.zoom,
            self.pixel_density / self.zoom,
        )

    def draw_grid(self, widget: Widget, x, y):
        grid_x, grid_y = self.index_to_pixel(x, y)
        with widget.canvas:
            Image(source="resources/map/highlight_grid.png", pos=(grid_x, grid_y))

    def draw_grids(self, surface):
        for x in range(self.grid_x):
            for y in range(self.grid_y):
                # if self.grid_matrix[y][x] == 1:
                self.draw_grid(surface, x, y)

    def highlightAtIndex(self, surface: Widget, i: int, j: int):
        self.tileAtIndex(surface, "resources/map/highlight_grid.png", i, j)

    def tileAtIndex(self, surface: Widget, source: str, i: int, j: int):
        Image(
            source=source,
            size=(
                self.pixel_density / self.zoom,
                self.pixel_density / self.zoom,
            ),
            pos=(
                surface.pos[0]
                + (self.grid_x_offset + (self.x_margin + i) * self.pixel_density)
                / self.zoom,
                surface.pos[1]
                + (self.grid_y_offset + (self.y_margin + j) * self.pixel_density)
                / self.zoom,
            ),
        )

    def sparseTiles(self, surface: Widget, interval: int):
        for i in range(self.grid_x):
            if i % interval == 0 or i == self.grid_x - 1:
                for j in range(self.grid_y):
                    if j % interval == 0 or j == self.grid_y - 1:
                        self.highlightAtIndex(surface, i, j)

    def drawHiddenTiles(self, surface: Widget):
        for i in range(self.grid_x):
            for j in range(self.grid_y):
                if self.grid_matrix[i][j] == 1:
                    self.tileAtIndex(surface, "resources/map/grid.png", i, j)

    def drawSparse(self, surface: Widget) -> None:
        sub_texture = self.getSubTexture(surface)

        i = 0
        for row in self.grid_matrix[::-1]:
            print(f"{i}: {row}")
            i += 1

        surface.canvas.clear()
        with surface.canvas:

            Rectangle(
                texture=sub_texture,
                size=(surface.width, surface.height),
                pos=surface.pos,
            )
            self.sparseTiles(surface, 5)

            if self.hidden_tiles:
                self.drawHiddenTiles(surface)

    def draw(self, surface: Widget):
        pass

    def flip_tile(self, x: int, y: int) -> None:
        """Invert the value of the grid tile at position x, y

        Args:
            x (int): Target tile x coordinate
            y (int): Target tile y coordinate
        """
        print(f"Flipping tile {x}, {y}")

        matrix_grid = self.grid_matrix[x][y]

        if matrix_grid == 0:
            self.grid_matrix[x][y] = 1
        else:
            self.grid_matrix[x][y] = 0

    def index_to_pixel(self, x: int, y: int) -> tuple[int, int]:
        """Get the x and y pixel offsets relative to display surface of the tile at index position (x, y)

        Args:
            x (int): x coordinate of tile
            y (int): y coordinate of tile

        Returns:
            tuple[int, int]: Position of the tile in x, y pixels relative to display surface
        """
        px = (self.grid_x_offset + (self.x_margin + x) * self.pixel_density) / self.zoom
        py = (self.grid_y_offset + (self.y_margin + y) * self.pixel_density) / self.zoom

        return px, py

    def pixel_to_index(self, px: int, py: int) -> tuple[int, int]:
        """Get the index of the tile which contains the pixel coordinate (px, py)

        Args:
            px (int): X axis pixel coordinate
            py (int): Y axis pixel coordinate

        Returns:
            tuple[int, int]: Integer x, y index of the containing tile in the grid map
        """

        x = (px * self.zoom - self.grid_x_offset) / self.pixel_density - self.x_margin
        y = (py * self.zoom - self.grid_y_offset) / self.pixel_density - self.y_margin

        return (int(x), int(y))

    def flip_at_coordinate(self, px: int, py: int):
        (x, y) = self.pixel_to_index(px, py)

        self.flip_tile(x, y)

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
