import os

from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle

from model.grid import Grid, SquareGrid, HexGrid
from model.window import Window

GRID_TYPE_SQUARE = "square"
GRID_TYPE_HEX = "hex"


class Map:
    def __init__(self, map_file: str = None):

        self.map_file = map_file
        self.image = None
        self.width = 0
        self.height = 0

        self.window = Window()
        self.grid: Grid = SquareGrid(window=self.window)
        self.grid_type: str = GRID_TYPE_SQUARE

        self.load_image(map_file)
        self.tile: Image = Image(source="resources/map/highlight_grid.png")

        # Offset of screen viewing map
        self.window.x = 0
        self.window.y = 0
        self.window.zoom = 1

        # Matrix of integers representing revealed/hidden grid tiles
        self.hidden_tiles = False

    def load_image(self, map_file: str | os.PathLike):
        self.image = Image(source=map_file)
        (self.width, self.height) = self.image.texture.size
        if self.grid.matrix is None:
            self.grid.update(self.width, self.height)

    def getZoomForSurface(self, surface: Widget):
        self.window.surface = surface
        if self.height / surface.height > self.width / surface.width:
            self.window.zoom = self.width / surface.width
        else:
            self.window.zoom = self.height / surface.height

    def getSubTexture(self):
        return self.image.texture.get_region(
            self.window.x * self.window.zoom,
            self.window.y * self.window.zoom,
            self.window.surface.width * self.window.zoom,
            self.window.surface.height * self.window.zoom,
        )

    def load(self, load_json):
        self.map_file = load_json["map_file"]
        self.window.zoom = load_json["zoom"]
        self.hidden_tiles = load_json["hidden"]
        self.grid_type = load_json["grid_type"]

        # Change from default (square) to hex if necessary
        if load_json["grid_type"] is GRID_TYPE_HEX:
            self.grid = HexGrid(window=self.window)

        self.grid.load(load_json["grid"])

        self.load_image(self.map_file)

        self.grid.scale_tiles()

    def save(self):
        save_data = {}
        save_data["map_file"] = self.map_file
        save_data["zoom"] = self.window.zoom
        save_data["hidden"] = self.hidden_tiles
        save_data["grid_type"] = self.grid_type
        save_data["grid"] = self.grid.save()

        return save_data

    def update(self):
        self.grid.update(self.width, self.height)

    def toHex(self):

        hexGrid = HexGrid(window=self.window)
        self.changeGrid(self.grid, hexGrid)

        self.grid_type = GRID_TYPE_HEX
        self.grid = hexGrid
        self.update()

        self.grid.scale_tiles()

    def toSquare(self):

        squareGrid = SquareGrid(window=self.window)
        self.changeGrid(self.grid, squareGrid)

        self.grid_type = GRID_TYPE_SQUARE
        self.grid = squareGrid
        self.update()

        self.grid.scale_tiles()

    def changeGrid(self, oldGrid: Grid, newGrid: Grid):
        newGrid.x = oldGrid.x
        newGrid.y = oldGrid.y
        newGrid.pixel_density = oldGrid.pixel_density
        newGrid.x_offset = oldGrid.x_offset
        newGrid.y_offset = oldGrid.y_offset

    def sparseTiles(self, interval: int):
        for i in range(self.grid.x):
            if i % interval == 0 or i == self.grid.x - 1:
                for j in range(self.grid.y):
                    if j % interval == 0 or j == self.grid.y - 1:
                        self.grid.highlightAtIndex(i, j)

    def drawSparse(self) -> None:
        sub_texture = self.window.getSubTexture(self.image)

        self.window.surface.canvas.clear()
        with self.window.surface.canvas:
            Rectangle(
                texture=sub_texture,
                size=(self.window.surface.width, self.window.surface.height),
                pos=self.window.surface.pos,
            )
            self.sparseTiles(3)

            if self.hidden_tiles:
                self.grid.drawHiddenTiles()

    def flip_at_coordinate(self, px: float, py: float):
        (x, y) = self.grid.pixel_to_index(px, py)

        self.grid.flip_tile(x, y)

    def draw(self, surface: Widget):
        pass

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