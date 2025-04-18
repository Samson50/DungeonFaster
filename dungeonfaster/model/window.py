from typing import TYPE_CHECKING

from kivy.graphics import Rectangle

# pylint: disable=no-name-in-module
from kivy.graphics.texture import Texture
from kivy.uix.image import Image

if TYPE_CHECKING:
    from kivy.uix.widget import Widget


class Window:
    def __init__(self):
        self.surface: Widget = None
        self.zoom: float = 0
        self.x: int = 0
        self.y: int = 0

        self.region_width = 0
        self.region_height = 0

    def get_sub_texture(self, image: Image) -> Texture:
        """Get a sub-texture of the given image which is zoomed, shifted, and cropped to be
        displayed within the current window.

        Args:
            image (Image): Image object for the map

        Returns:
            Texture: Scaled region of the map for drawing on self.surface's canvas
        """
        (image_width, image_height) = image.texture.size

        self.region_width = min(self.surface.width * self.zoom, image_width - self.x * self.zoom)
        if self.x < 0:
            self.region_width += self.x * self.zoom

        self.region_height = min(self.surface.height * self.zoom, image_height - self.y * self.zoom)
        if self.y < 0:
            self.region_height += self.y * self.zoom

        return image.texture.get_region(
            max(0, self.x) * self.zoom,
            max(0, self.y) * self.zoom,
            self.region_width,
            self.region_height,
        )

    def get_region_size(self) -> tuple[float, float]:
        """Get the size of the region of the map within the display window scaled to display
        within the main window.

        Returns:
            tuple[float, float]: (width, height) of the section of the map which is available to
            display within the window
        """
        width = self.surface.width

        # If there's a gap on the left side...
        if self.x < 0:
            width = width + self.x
        # If there's a gap on the right side...
        if self.region_width != self.surface.width * self.zoom:
            width = self.region_width / self.zoom

        height = self.surface.height
        # If there's a gap on the bottom...
        if self.y < 0:
            height = height + self.y
        # If there's a gap on the top...
        if self.region_height != self.surface.height * self.zoom:
            height = self.region_height / self.zoom

        return (width, height)

    def get_region_pos(self) -> tuple[int, int]:
        """Get the position of the map-region relative to the display window

        Returns:
            tuple[int, int]: x, y position within the window to display the map
        """

        x = self.surface.x
        if self.x < 0:
            x = x + abs(self.x)

        y = self.surface.y
        if self.y < 0:
            y = y + abs(self.y)

        return (x, y)

    def showing(self, tile: Rectangle) -> bool:
        """Determine if tile is within the current display window

        Args:
            tile (Rectangle): tile to check relative position of

        Returns:
            bool: Is the center of the tile within the display window?
        """
        center = (
            tile.pos[0] + tile.size[0] / 2,
            tile.pos[1] + tile.size[1] / 2,
        )
        return self.surface.collide_point(*center)
