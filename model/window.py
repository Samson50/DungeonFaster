from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics.texture import Texture


class Window:
    def __init__(self):
        self.surface: Widget = None
        self.zoom: float = 0
        self.x: int = 0
        self.y: int = 0

    def getSubTexture(self, image: Image) -> Texture:
        return image.texture.get_region(
            self.x * self.zoom,
            self.y * self.zoom,
            self.surface.width * self.zoom,
            self.surface.height * self.zoom,
        )
