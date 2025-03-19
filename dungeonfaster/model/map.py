import os

from kivy.graphics import Rectangle
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from dungeonfaster.model.grid import Grid, HexGrid, SquareGrid
from dungeonfaster.model.window import Window

RESOURCES_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "resources")
CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")
CAMP_FILE_DIR = os.path.join(CAMPAIGNS_DIR, "files")

GRID_TYPE_SQUARE = "square"
GRID_TYPE_HEX = "hex"


class Map:
    image: Image

    def __init__(self, map_file: os.PathLike):
        # TODO: Down-sample very large high-resolution maps when screens are small and zoom is low

        self.map_file = os.path.join(CAMP_FILE_DIR, map_file)
        self.width = 0
        self.height = 0

        self.window = Window()
        self.grid: Grid = SquareGrid(window=self.window)
        self.grid_type: str = GRID_TYPE_SQUARE
        self.points_of_interest: list[tuple[int, int]] = []
        self.drawn_poi: dict[tuple[int, int], Rectangle] = {}

        self.load_image()
        # self.tile: Image = Image(source="resources/map/highlight_grid.png")

        # Offset of screen viewing map
        self.window.x = 0
        self.window.y = 0
        self.window.zoom = 1

        # Does this map use hidden tiles?
        self.hidden_tiles = False

        # List of references to grid tiles currently on canvas
        self.drawn_tiles: list[Rectangle] = []
        self.map_rect: Rectangle = None

    def load_image(self):
        self.image = Image(source=self.map_file)
        (self.width, self.height) = self.image.texture.size
        if self.grid.matrix is None:
            self.grid.update(self.width, self.height)

    def get_zoom_for_surface(self, surface: Widget):
        self.window.surface = surface
        if self.height / surface.height > self.width / surface.width:
            self.window.zoom = self.width / surface.width
        else:
            self.window.zoom = self.height / surface.height

    def load(self, load_json: dict, surface: Widget):
        self.window.surface = surface
        self.map_file = load_json["map_file"]
        self.window.zoom = load_json["zoom"]
        self.hidden_tiles = load_json["hidden"]
        self.grid_type = load_json["grid_type"]

        # Change from default (square) to hex if necessary
        if load_json["grid_type"] == GRID_TYPE_HEX:
            self.grid = HexGrid(window=self.window)

        # Image files must be under campaigns/files/
        # self.load_image()

        self.grid.load(load_json["grid"])

        self.window.x = load_json.get("window_x", 0)
        self.window.y = load_json.get("window_y", 0)

        # self.grid.scale_tiles()

    def save(self):
        save_data = {}
        save_data["map_file"] = self.map_file
        save_data["zoom"] = self.window.zoom
        save_data["hidden"] = self.hidden_tiles
        save_data["grid_type"] = self.grid_type
        save_data["grid"] = self.grid.save()

        save_data["window_x"] = self.window.x
        save_data["window_y"] = self.window.y

        return save_data

    def update(self):
        self.grid.update(self.width, self.height)
        for tile in self.drawn_tiles:
            if tile in self.window.surface.canvas.children:
                self.window.surface.canvas.remove(tile)
        self.drawn_tiles = []
        self.drawn_poi = {}

    def to_hex(self):
        hex_grid = HexGrid(window=self.window)
        self.change_grid(self.grid, hex_grid)

        self.grid_type = GRID_TYPE_HEX
        self.grid = hex_grid
        self.update()

    def to_square(self):
        square_grid = SquareGrid(window=self.window)
        self.change_grid(self.grid, square_grid)

        self.grid_type = GRID_TYPE_SQUARE
        self.grid = square_grid
        self.update()

    def change_grid(self, old_grid: Grid, new_grid: Grid):
        new_grid.x = old_grid.x
        new_grid.y = old_grid.y
        new_grid.pixel_density = old_grid.pixel_density
        new_grid.x_offset = old_grid.x_offset
        new_grid.y_offset = old_grid.y_offset

    def draw_map(self) -> None:
        texture = self.window.get_sub_texture(self.image)
        pos = self.window.get_region_pos()
        size = self.window.get_region_size()
        if self.map_rect is None:
            self.map_rect = Rectangle(texture=texture, size=size, pos=pos)
            self.window.surface.canvas.add(self.map_rect)
        else:
            self.map_rect.texture = texture
            self.map_rect.pos = pos
            self.map_rect.size = size

    def draw_tile(self, x: int, y: int) -> None:
        # Obscuration tile at index
        tile: Rectangle = self.grid.image_matrix.get((x, y), None)

        if (x, y) in self.grid.matrix:
            if tile is None:
                tile = self.grid.get_rect(x, y, self.grid.hidden_image_path)
                self.grid.image_matrix[(x, y)] = tile

            # Tile is within display window (mostly) and has the tile been drawn already?
            if self.window.showing(tile) and tile not in self.drawn_tiles:
                # Add to canvas and tracking list
                self.window.surface.canvas.add(tile)
                self.drawn_tiles.append(tile)
        elif tile in self.drawn_tiles:
            self.window.surface.canvas.remove(tile)
            self.drawn_tiles.remove(tile)

        self.grid.update_tile(x, y)

    def draw_poi(self):
        # TODO: Seems to be an issue with PoI highlights on sub-locations
        for poi in self.points_of_interest:
            # If the PoI tile is revealed
            if poi not in self.grid.matrix:
                if poi in self.drawn_poi:
                    poi_rect = self.drawn_poi[poi]
                    self.grid.update_rect(poi_rect, poi[0], poi[1])
                else:
                    poi_rect = self.grid.get_rect(*poi, os.path.join(RESOURCES_DIR, "icons", "poi.png"))

                # If the PoI is within the display window
                if self.window.showing(poi_rect):
                    # If the PoI has not been drawn yet
                    if poi not in self.drawn_poi:
                        # Draw the PoI
                        self.window.surface.canvas.add(poi_rect)
                        self.drawn_poi[poi] = poi_rect

                elif poi in self.drawn_poi:
                    # Remove the PoI from canvas and tracking list
                    try:
                        self.window.surface.canvas.remove(self.drawn_poi[poi])
                    except:
                        pass
                    del self.drawn_poi[poi]

    def draw_tiles(self):
        self.grid.scale_tiles()

        # Check if tiles need to be added/removed
        for x in range(self.grid.x):
            for y in range(self.grid.y):
                self.draw_tile(x, y)

        # Draw tiles marking revealed PoIs
        self.draw_poi()

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
        return (x, y) not in self.grid.matrix

    def hidden(self, x: int, y: int) -> bool:
        return (x, y) in self.grid.matrix

    def reveal(self, x: int, y: int) -> None:
        if self.hidden(x, y):
            tile = self.grid.flip_tile(x, y)
            if tile in self.drawn_tiles:
                self.drawn_tiles.remove(tile)
            if tile in self.window.surface.canvas.children:
                self.window.surface.canvas.remove(tile)

    def draw(self):
        self.draw_map()
        self.draw_tiles()
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
