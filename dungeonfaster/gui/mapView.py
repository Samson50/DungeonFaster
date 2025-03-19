import os
from typing import TYPE_CHECKING

from kivy.core.window import Window, WindowBase
from kivy.graphics import Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from dungeonfaster.model.campaign import Campaign
from dungeonfaster.model.location import Location

if TYPE_CHECKING:
    from dungeonfaster.model.map import Map

ZOOM_FACTOR = 1.25

RESOURCES_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "resources")
CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")


class PlayerRect(Rectangle):
    def __init__(self, name: str, index: tuple[int, int], **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.index = index


class MapView(FloatLayout):
    campaign: Campaign

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.mouse_x = 0
        self.mouse_y = 0
        self.moved = False
        self.moving_token = False
        self.last_zoom = (0, 0)

        self.screen = screen
        self.party_icon = Rectangle(source=os.path.join(RESOURCES_DIR, "icons", "party.png"))
        self.party_bg = None
        self.highlight_rect: Rectangle = None
        self.selected: tuple[int, int] = None
        self.select_rect: Rectangle = Rectangle(source=os.path.join(RESOURCES_DIR, "icons", "selected.png"))
        self.map: Map = None

        self.party_tiles: list[PlayerRect] = []
        self.active_tile: PlayerRect | None = None

        self.map_layout = FloatLayout(pos_hint={"x": 0.025, "y": 0.025}, size_hint=(0.95, 0.95))
        self.add_widget(self.map_layout)

    def on_mouse_pos(self, window: WindowBase, pos: tuple[float, float]) -> None:
        if not self.map:
            return

        (map_x, map_y) = self.map_layout.pos
        (mouse_x, mouse_y) = pos
        if self.map_layout.collide_point(*pos):
            x, y = self.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)
            if not self.highlight_rect:
                self.highlight_rect = self.map.grid.get_highlight_rect(x, y)
            if self.highlight_rect not in self.map_layout.children:
                self.map_layout.canvas.add(self.highlight_rect)
            self.map.grid.update_rect(self.highlight_rect, x, y)

        elif self.highlight_rect in self.map_layout.canvas.children:
            self.map_layout.canvas.remove(self.highlight_rect)

    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.draw()

    def draw(self) -> None:
        self.map.draw()
        if not self.moving_token:
            self.draw_party()
        self.draw_selected()

    def _draw_active_tile(self, pos: tuple[float, float]):
        if not self.active_tile:
            return

        if self.active_tile not in self.map_layout.canvas.children:
            self.map_layout.canvas.add(self.active_tile)

        self.active_tile.pos = pos
        self.active_tile.size = self.map.grid.tile_size

    def _draw_party_icons(self, pos: tuple[float, float]):
        if not self.party_bg:
            self.party_bg = self.map.grid.get_rect(*self.campaign.position, self.map.grid.hidden_image_path)

        if self.party_bg not in self.map_layout.canvas.children:
            self.map_layout.canvas.add(self.party_bg)
        if self.party_icon not in self.map_layout.canvas.children:
            self.map_layout.canvas.add(self.party_icon)

        self.party_icon.pos = pos
        self.party_icon.size = self.map.grid.tile_size
        self.party_bg.pos = self.party_icon.pos
        self.party_bg.size = self.party_icon.size

    def draw_party(self) -> None:
        if self.campaign.current_location.type == "group":
            self._draw_party_icons(self.map.grid.tile_pos_from_index(*self.campaign.position))

        elif self.campaign.current_location.type == "individual":
            for tile in self.party_tiles:
                if tile == self.active_tile:
                    continue
                self.map_layout.canvas.add(tile)
                tile.pos = self.map.grid.tile_pos_from_index(*tile.index)
                tile.size = self.map.grid.tile_size

    def draw_selected(self) -> None:
        if self.selected:
            self.select_rect.pos = self.map.grid.tile_pos_from_index(*self.selected)
            self.select_rect.size = self.map.grid.tile_size
            if self.select_rect not in self.map_layout.canvas.children:
                self.map_layout.canvas.add(self.select_rect)

        else:
            if self.select_rect in self.map_layout.canvas.children:
                self.map_layout.canvas.remove(self.select_rect)

    def change_map(self, name: str):
        new_location: Location = self.campaign.locations[name]
        self.map = new_location.map

        self.map_layout.canvas.clear()
        self.map.drawn_tiles = []
        self.map.map_rect = None
        self.map.get_zoom_for_surface(self.map_layout)
        # self._by_scroll()

        self.draw()

    def leave(self) -> Location:
        location = self.campaign.current_location
        self.selected = None
        parent = self.campaign.get_location(location.parent)

        self.change_map(location.parent)

        # Update music if applicable
        if len(parent.music) > 0:
            self.update_playlist(parent)

        self.campaign.current_location = parent
        self.campaign.position = parent.position

        return parent

    def arrive(self, location: Location, from_pos: tuple[int, int]) -> None:
        self.selected = None

        if self.campaign.current_location.type != location.type:
            if location.type == "group":
                for tile in self.party_tiles:
                    self.map_layout.canvas.remove(tile)

            elif location.type == "individual":
                for player in self.campaign.party:
                    player_rect = PlayerRect(
                        player.name, player.position, source=os.path.join(CAMPAIGNS_DIR, "files", player.image)
                    )
                    self.map_layout.canvas.add(player_rect)

                    # pylint: disable=attribute-defined-outside-init
                    player_rect.pos = self.map.grid.tile_pos_from_index(*player.position)
                    # pylint: disable=attribute-defined-outside-init
                    player_rect.size = self.map.grid.tile_size

                    self.party_tiles.append(player_rect)

        self.campaign.current_location = location
        self.campaign.position = location.entrances.get(from_pos, (0, 0))

        self.change_map(location.name)

    def on_button(self, px: float, py: float) -> bool:
        children = self.children[:]
        children.remove(self.map_layout)
        return any(child.collide_point(px, py) for child in children)

    def grabbing_token(self, event: MotionEvent):
        mouse_x, mouse_y = event.pos
        (map_x, map_y) = self.map_layout.pos
        cursor_inedx = self.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)

        if cursor_inedx == self.campaign.position:
            return True

        for token in self.party_tiles:
            if cursor_inedx == token.index:
                print("TRUE!")
                self.active_tile = token
                return True

        return False

    def move_token(self, event: MotionEvent):
        mouse_x, mouse_y = event.pos

        icon_width, icon_height = self.map.grid.tile_size
        if self.campaign.current_location.type == "group":
            self._draw_party_icons((mouse_x - icon_width / 2, mouse_y - icon_height / 2))

        elif self.campaign.current_location.type == "individual":
            self._draw_active_tile((mouse_x - icon_width / 2, mouse_y - icon_height / 2))

    def set_token_position(self, event: MotionEvent):
        mouse_x, mouse_y = event.pos
        (map_x, map_y) = self.map_layout.pos
        cursor_inedx = self.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)

        if self.campaign.current_location.type == "group":
            self.campaign.position = cursor_inedx

        elif self.campaign.current_location.type == "individual":
            self.active_tile.index = cursor_inedx
            self.active_tile = None

        self.draw_party()

    def on_click(self, layout: FloatLayout, event: MotionEvent):
        if event.is_touch:
            self.mouse_x, self.mouse_y = event.pos
            event.grab(self)
            self.moved = False
            if self.grabbing_token(event):
                self.moving_token = True

    def on_click_up(self, layout: FloatLayout, event: MotionEvent):
        if self.moving_token:
            self.set_token_position(event)
            self.moving_token = False

        if self.moved:
            return

        (mouse_x, mouse_y) = event.pos

        # One of the buttons is already responding to this event, ignore
        if self.on_button(mouse_x, mouse_y):
            return

        if event.is_mouse_scrolling:  # and self.last_zoom != event.pos:
            self.last_zoom = event.pos
            if event.button == "scrolldown":
                self.zoom_in(event)
            elif event.button == "scrollup":
                self.zoom_out(event)
            return

    def on_touch_move(self, touch: MotionEvent):
        (mouse_x, mouse_y) = touch.pos
        if self.on_button(mouse_x, mouse_y):
            return

        if touch.grab_current is not self:
            return
        super().on_touch_move(touch)
        new_x, new_y = touch.pos

        if self.moving_token:
            self.move_token(touch)
            self.moved = True

        else:
            if int(self.mouse_x) != int(new_x) and int(self.mouse_y) != int(new_y):
                self.moved = True

            self.map.window.x += self.mouse_x - new_x
            self.map.window.y += self.mouse_y - new_y
            self.mouse_x, self.mouse_y = (new_x, new_y)

        self.draw()

    def interact(self, x: int, y: int) -> None:
        # TODO: Right click to re-hide tile?
        pass

    def _by_zoom(self, old_zoom: float, event: MotionEvent):
        mouse_x, mouse_y = event.pos

        zoom_factor = old_zoom / self.map.window.zoom
        self.map.window.x = (self.map.window.x + mouse_x) * zoom_factor - mouse_x
        self.map.window.y = (self.map.window.y + mouse_y) * zoom_factor - mouse_y
        self.draw()

    def zoom_in(self, event: MotionEvent):
        if self.map is None:
            return
        old_zoom = self.map.window.zoom
        self.map.window.zoom /= ZOOM_FACTOR

        self._by_zoom(old_zoom, event)

    def zoom_out(self, event: MotionEvent):
        if self.map is None:
            return
        old_zoom = self.map.window.zoom
        self.map.window.zoom *= ZOOM_FACTOR

        self._by_zoom(old_zoom, event)
