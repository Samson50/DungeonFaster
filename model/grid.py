import math

from kivy.graphics import Rectangle
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from model.window import Window


class Grid:
    def __init__(self, window: Window = None):
        self.pixel_density: float = 60.0
        self.tile_size: tuple[float, float] = (self.pixel_density, self.pixel_density)
        self.window = window

        # How many box-width from the edges to leave without tiles
        self.x_margin = 1
        self.y_margin = 1

        # Number of pixels to offset the first grid
        self.x_offset = 0
        self.y_offset = 0

        self.matrix = None
        self.highlight_image_path = None
        self.hidden_image_path = None

        # Matrix of None or Rectangle for tiles to be drawn
        self.image_matrix: list[list[Rectangle]] = []

    def save(self) -> dict:
        save_data = {}
        save_data["width"] = self.x
        save_data["height"] = self.y
        save_data["x_offset"] = self.x_offset
        save_data["y_offset"] = self.y_offset
        save_data["x_margin"] = self.x_margin
        save_data["y_margin"] = self.y_margin
        save_data["pixel_density"] = self.pixel_density
        save_data["matrix"] = self.matrix

        return save_data

    def load(self, json_data: dict) -> None:
        self.x = json_data["width"]
        self.y = json_data["height"]
        self.x_offset = json_data["x_offset"]
        self.y_offset = json_data["y_offset"]
        self.x_margin = json_data["x_margin"]
        self.y_margin = json_data["y_margin"]
        self.pixel_density = json_data["pixel_density"]
        self.matrix = json_data["matrix"]

        self.scale_tiles()

        # Ensure valid dimensions
        if self.x != len(self.matrix) or self.y != len(self.matrix[0]):
            self.matrix = [[0 for y in range(self.y)] for x in range(self.x)]
        if self.x != len(self.image_matrix) or self.y != len(self.image_matrix[0]):
            self.image_matrix = [[None for y in range(self.y)] for x in range(self.x)]

        for x in range(self.x):
            for y in range(self.y):
                if self.matrix[x][y] == 0:
                    self.image_matrix[x][y] = None
                else:
                    self.image_matrix[x][y] = Rectangle(
                        source=self.hidden_image_path,
                        pos=self.tile_pos_from_index(x, y),
                        size=self.tile_size,
                    )

    def getRect(self, x: int, y: int, source=None) -> Rectangle:
        if source is None:
            source = self.hidden_image_path

        return Rectangle(
            source=source,
            pos=self.tile_pos_from_index(x, y),
            size=self.tile_size,
        )

    def getHighlightRect(self, x: int, y: int) -> Rectangle:
        return self.getRect(x, y, self.highlight_image_path)

    def updateRect(self, rect: Rectangle, x: int, y: int):
        rect.pos = self.tile_pos_from_index(x, y)
        rect.size = self.tile_size

    def updateTile(self, x: int, y: int):
        tile = self.image_matrix[x][y]
        if tile:
            self.updateRect(tile, x, y)

    def tileAtIndex(self, source: str, i: int, j: int):
        Image(
            source=source,
            size=self.tile_size,
            pos=self.tile_pos_from_index(i, j),
        )

    def highlightAtIndex(self, i: int, j: int):
        self.tileAtIndex(self.highlight_image_path, i, j)

    def drawHiddenTiles(self):
        for i in range(self.x):
            for j in range(self.y):
                if self.matrix[i][j] == 1:
                    self.tileAtIndex(self.hidden_image_path, i, j)

    def flip_tile(self, x: int, y: int) -> Rectangle:
        """Invert the value of the grid tile at position x, y

        Args:
            x (int): Target tile x coordinate
            y (int): Target tile y coordinate

        Returns:
            Rectangle: Flipped tile image to be added or removed from caller's tracking list
        """

        matrix_grid = self.matrix[x][y]

        tile = self.image_matrix[x][y]
        if matrix_grid == 0:
            self.matrix[x][y] = 1
            tile = Rectangle(
                source=self.hidden_image_path,
                pos=self.tile_pos_from_index(x, y),
                size=self.tile_size,
            )
            self.image_matrix[x][y] = tile
        else:
            try:
                self.window.surface.canvas.remove(tile)
            except:
                # Ignore attempts to remove tiles not currently displayed
                pass
            self.matrix[x][y] = 0
            self.image_matrix[x][y] = None

        return tile

    # ==== Override methods ==== #

    def adjacent(self, x: int, y: int) -> list[tuple[int, int]]:
        """For the given x, y index, return a list of indices that are directly adjacent to the given
        index within the matrix

        Args:
            x (int): Coordinate on the x axis
            y (int): Coordinate on the y axis

        Returns:
            list[tuple[int, int]]: List of indices within the matrix adjacent to the given
        """
        pass

    def scale_tiles(self):
        pass

    def update(self, width, height):
        """
        Calculate the number of tiles available on the x and y axis from the size of
        the background image and the current width of each tile
        """
        pass

    def tile_pos_from_index(self, i: int, j: int) -> tuple[float, float]:
        """_summary_

        Args:
            i (int): _description_
            j (int): _description_

        Returns:
            tuple[float, float]: _description_
        """
        pass

    def index_to_pixel(self, x: int, y: int) -> tuple[int, int]:
        """Get the x and y pixel offsets relative to display surface of the tile at index position (x, y)

        Args:
            x (int): x coordinate of tile
            y (int): y coordinate of tile

        Returns:
            tuple[int, int]: Position of the tile in x, y pixels relative to display surface
        """
        pass

    def pixel_to_index(self, px: float, py: float) -> tuple[int, int]:
        """Get the index of the tile which contains the pixel coordinate (px, py)

        Args:
            px (int): X axis pixel coordinate
            py (int): Y axis pixel coordinate

        Returns:
            tuple[int, int]: Integer x, y index of the containing tile in the grid map
        """
        pass


class SquareGrid(Grid):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.highlight_image_path = "resources/map/highlight_grid.png"
        self.hidden_image_path = "resources/map/grid.png"

    def adjacent(self, x: int, y: int) -> list[tuple[int, int]]:
        tiles = [
            (x, y - 1),
            (x, y + 1),
            (x - 1, y - 1),
            (x - 1, y + 1),
            (x - 1, y),
            (x + 1, y - 1),
            (x + 1, y + 1),
            (x + 1, y),
        ]

        # TODO: Filter out of range

        return tiles

    def update(self, width, height):
        self.x = int(width / self.pixel_density - 2 * self.x_margin)
        self.y = int(height / self.pixel_density - 2 * self.y_margin)
        self.matrix = [[0 for y in range(self.y)] for x in range(self.x)]
        # if len(self.image_matrix) == 0:
        self.image_matrix = [[None for y in range(self.y)] for x in range(self.x)]

    def scale_tiles(self):
        self.tile_size = (
            self.pixel_density / self.window.zoom,
            self.pixel_density / self.window.zoom,
        )

    def tile_pos_from_index(self, i: int, j: int) -> tuple[float, float]:
        (sx, sy) = self.window.surface.pos
        return (
            sx
            - self.window.x
            + (self.x_offset + (self.x_margin + i) * self.pixel_density)
            / self.window.zoom,
            sy
            - self.window.y
            + (self.y_offset + (self.y_margin + j) * self.pixel_density)
            / self.window.zoom,
        )

    def index_to_pixel(self, x: int, y: int) -> tuple[int, int]:
        px = (
            self.x_offset + (self.x_margin + x) * self.pixel_density
        ) / self.window.zoom - self.window.x
        py = (
            self.y_offset + (self.y_margin + y) * self.pixel_density
        ) / self.window.zoom - self.window.y

        return px, py

    def pixel_to_index(self, px: float, py: float) -> tuple[int, int]:
        x = (
            (px + self.window.x) * self.window.zoom - self.x_offset
        ) / self.pixel_density - self.x_margin
        y = (
            (py + self.window.y) * self.window.zoom - self.y_offset
        ) / self.pixel_density - self.y_margin

        return (int(x), int(y))


class HexGrid(Grid):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.highlight_image_path = "resources/icons/highlight.png"
        self.hidden_image_path = "resources/map/hexes.png"

    def adjacent(self, x: int, y: int) -> list[tuple[int, int]]:
        tiles = [(x, y + 2), (x, y - 2)]
        if x % 2 == 0:
            tiles.append((x, y + 1))
            tiles.append((x, y - 1))
        else:
            tiles.append((x, y + 1))
            tiles.append((x, y - 1))

        if y % 2 == 0:
            tiles.append((x - 1, y + 1))
            tiles.append((x - 1, y - 1))
        else:
            tiles.append((x + 1, y - 1))
            tiles.append((x + 1, y + 1))

        return tiles

    def scale_tiles(self):
        self.tile_size = (
            self.pixel_density * 2 / self.window.zoom,
            self.pixel_density * 2 / self.window.zoom,
        )

    def update(self, width, height):
        self.x = int((width / (2 * self.pixel_density) - 2 * self.x_margin))
        self.y = int(
            (height / (math.sqrt(3) * self.pixel_density / 2)) - 2 * self.y_margin
        )
        self.matrix = [[0 for y in range(self.y)] for x in range(self.x)]
        # if len(self.image_matrix) == 0:
        self.image_matrix = [[None for y in range(self.y)] for x in range(self.x)]

    def tile_pos_from_index(self, i: int, j: int) -> tuple[float, float]:
        (sx, sy) = self.window.surface.pos
        (px, py) = self.index_to_pixel(i, j)
        return (sx + px, sy + py)

    # TODO: Fix this. I hate this, but it works and I'm tired
    def index_to_pixel(self, x: int, y: int) -> tuple[float, float]:

        if y % 2 == 0:
            grid_x = (x + self.x_margin) * 3 * self.pixel_density
        else:
            grid_x = ((x + self.x_margin) + 1 / 2) * 3 * self.pixel_density

        px = (grid_x + self.x_offset) / self.window.zoom - self.window.x
        py = (
            (y + self.y_margin) * (math.sqrt(3) / 2) * self.pixel_density
            + self.y_offset
        ) / self.window.zoom - self.window.y

        return px, py

    # TODO: Fix this. I hate this, but it works and I'm tired
    def pixel_to_index(self, px: float, py: float) -> tuple[int, int]:
        y = ((py + self.window.y) * self.window.zoom - self.y_offset) / (
            (math.sqrt(3) / 2) * self.pixel_density
        ) - self.y_margin

        x = ((px + self.window.x) * self.window.zoom - self.x_offset) / (
            3 * self.pixel_density
        ) - self.x_margin

        if x % 1 < 1 / 2:
            y = y - (int(y) % 2)
        else:
            y = y - (1 - (int(y) % 2))

        return int(x), int(y)
