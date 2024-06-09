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
        self.points_of_interest: list[tuple[int, int]] = []
        self.drawn_poi: dict[tuple[int, int], Rectangle] = {}

        self.load_image(map_file)
        self.tile: Image = Image(source="resources/map/highlight_grid.png")

        # Offset of screen viewing map
        self.window.x = 0
        self.window.y = 0
        self.window.zoom = 1

        # Does this map use hidden tiles?
        self.hidden_tiles = False

        # List of references to grid tiles currently on canvas
        self.drawn_tiles: list[Rectangle] = []
        self.map_rect: Rectangle = None

    def load_image(self, map_file: str | os.PathLike):
        if map_file is None:
            return
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
        for tile in self.drawn_tiles:
            if tile in self.window.surface.canvas.children:
                self.window.surface.canvas.remove(tile)
        self.drawn_tiles = []
        self.drawn_poi = {}

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

    def drawTile(self, x: int, y: int) -> None:
        # Obscuration tile at index
        tile: Rectangle = self.grid.image_matrix[x][y]

        if self.grid.matrix[x][y] == 1:

            if tile is None:
                tile = self.grid.getRect(x, y, self.grid.hidden_image_path)
                self.grid.image_matrix[x][y] = tile

            # Tile is within display window (mostly)
            if self.window.showing(tile):
                # Has the tile been drawn already?
                if tile not in self.drawn_tiles:
                    # Add to canvas and tracking list
                    self.window.surface.canvas.add(tile)
                    self.drawn_tiles.append(tile)
        elif tile in self.drawn_tiles:
            self.window.surface.canvas.remove(tile)
            self.drawn_tiles.remove(tile)

        self.grid.updateTile(x, y)

    def drawPoI(self):
        # TODO: Seems to be an issue with PoI highlights on sub-locations
        for poi in self.points_of_interest:
            # If the PoI tile is revealed
            if self.grid.matrix[poi[0]][poi[1]] == 0:
                if poi in self.drawn_poi.keys():
                    poi_rect = self.drawn_poi[poi]
                    self.grid.updateRect(poi_rect, poi[0], poi[1])
                else:
                    poi_rect = self.grid.getRect(*poi, "resources/icons/poi.png")

                # If the PoI is within the display window
                if self.window.showing(poi_rect):
                    # If the PoI has not been drawn yet
                    if not poi in self.drawn_poi.keys():
                        # Draw the PoI
                        self.window.surface.canvas.add(poi_rect)
                        self.drawn_poi[poi] = poi_rect

                elif poi in self.drawn_poi.keys():
                    # Remove the PoI from canvas and tracking list
                    try:
                        self.window.surface.canvas.remove(self.drawn_poi[poi])
                    except:
                        pass
                    del self.drawn_poi[poi]

    def drawTiles(self):
        self.grid.scale_tiles()

        # Check if tiles need to be added/removed
        for x in range(self.grid.x):
            for y in range(self.grid.y):
                self.drawTile(x, y)

        # Draw tiles marking revealed PoIs
        self.drawPoI()

    def flip_at_coordinate(self, px: float, py: float) -> None:
        (x, y) = self.grid.pixel_to_index(px, py)
        self.flip_at_index(x, y)

    def flip_at_index(self, x: int, y: int) -> None:
        tile = self.grid.flip_tile(x, y)

        if tile in self.drawn_tiles:
            self.drawn_tiles.remove(tile)
            self.window.surface.canvas.remove(tile)
        else:
            self.drawn_tiles.append(tile)
            self.window.surface.canvas.add(tile)

    def revealed(self, x: int, y: int) -> bool:
        try:
            return self.grid.matrix[x][y] == 0
        except:
            return False

    def hidden(self, x: int, y: int) -> bool:
        try:
            return self.grid.matrix[x][y] == 1
        except:
            return False

    def reveal(self, x: int, y: int) -> None:
        if self.hidden(x, y):
            tile = self.grid.flip_tile(x, y)
            if tile in self.drawn_tiles:
                self.drawn_tiles.remove(tile)
            if tile in self.window.surface.canvas.children:
                self.window.surface.canvas.remove(tile)

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
