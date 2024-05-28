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
        # TODO: Down-sample very large high-resolution maps when screens are small and zoom is low

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

        # Does this map use hidden tiles?
        self.hidden_tiles = False

        # List of references to grid tiles currently on canvas
        self.drawn_tiles: list[Image] = []
        self.map_rect: Rectangle = None

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

    def load(self, load_json: str, surface: Widget):
        self.window.surface = surface
        self.map_file = load_json["map_file"]
        self.window.zoom = load_json["zoom"]
        self.hidden_tiles = load_json["hidden"]
        self.grid_type = load_json["grid_type"]

        # Change from default (square) to hex if necessary
        if load_json["grid_type"] == GRID_TYPE_HEX:
            self.grid = HexGrid(window=self.window)

        self.load_image(self.map_file)

        self.grid.load(load_json["grid"])

        # self.grid.scale_tiles()

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
        # self.grid.scale_tiles()

    def toHex(self):

        hexGrid = HexGrid(window=self.window)
        self.changeGrid(self.grid, hexGrid)

        self.grid_type = GRID_TYPE_HEX
        self.grid = hexGrid
        self.update()

    def toSquare(self):

        squareGrid = SquareGrid(window=self.window)
        self.changeGrid(self.grid, squareGrid)

        self.grid_type = GRID_TYPE_SQUARE
        self.grid = squareGrid
        self.update()

    def changeGrid(self, oldGrid: Grid, newGrid: Grid):
        newGrid.x = oldGrid.x
        newGrid.y = oldGrid.y
        newGrid.pixel_density = oldGrid.pixel_density
        newGrid.x_offset = oldGrid.x_offset
        newGrid.y_offset = oldGrid.y_offset

    def drawMap(self) -> None:

        texture = self.window.getSubTexture(self.image)
        pos = self.window.getRegionPos()
        size = self.window.getRegionSize()
        if self.map_rect is None:
            self.map_rect = Rectangle(texture=texture, size=size, pos=pos)
            self.window.surface.canvas.add(self.map_rect)
        else:
            self.map_rect.texture = texture
            self.map_rect.pos = pos
            self.map_rect.size = size

    def drawTiles(self):
        self.grid.scale_tiles()

        # Check if tiles need to be added/removed
        for x in range(self.grid.x):
            for y in range(self.grid.y):
                # Obscuration tile at index
                tile = self.grid.image_matrix[x][y]
                if tile is not None:
                    # Tile is within display window (mostly)
                    center = (
                        tile.pos[0] + tile.size[0] / 2,
                        tile.pos[1] + tile.size[1] / 2,
                    )
                    if self.window.surface.collide_point(*center):
                        # Has the tile been drawn already?
                        if tile not in self.drawn_tiles:
                            # Add to canvas and tracking list
                            self.window.surface.canvas.add(tile)
                            self.drawn_tiles.append(tile)
                    self.grid.updateTile(x, y)

    def flip_at_coordinate(self, px: float, py: float) -> None:
        (x, y) = self.grid.pixel_to_index(px, py)

        tile = self.grid.flip_tile(x, y)
        if tile in self.drawn_tiles:
            self.drawn_tiles.remove(tile)
            self.window.surface.canvas.remove(tile)
        else:
            self.drawn_tiles.append(tile)
            self.window.surface.canvas.add(tile)

    def draw(self):
        self.drawMap()
        self.drawTiles()
        # TODO: self.drawObjects()

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
