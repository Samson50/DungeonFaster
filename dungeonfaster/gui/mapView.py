import os

from kivy.core.audio import Sound
from kivy.core.window import Window, WindowBase
from kivy.graphics import Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from dungeonfaster.model.location import Location
from dungeonfaster.model.map import Map
from dungeonfaster.model.campaign import Campaign
from dungeonfaster.gui.audio import AudioPlayer

RESOURCES_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "resources")
CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")

class MapView(FloatLayout):
    campaign: Campaign

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.mouse_x = 0
        self.mouse_y = 0
        self.moved = False
        self.last_zoom = (0, 0)

        self.screen = screen
        self.party_icon = Rectangle(
            source=os.path.join(RESOURCES_DIR, "icons", "party.png")
        )
        self.party_bg = None
        self.highlight_rect: Rectangle = None
        self.selected: tuple[int, int] = None
        self.select_rect: Rectangle = Rectangle(
            source=os.path.join(RESOURCES_DIR, "icons", "selected.png")
        )
        self.map: Map = None

        self.map_layout = FloatLayout(
            pos_hint={"x": 0.025, "y": 0.025}, size_hint=(0.95, 0.95)
        )
        self.add_widget(self.map_layout)


    def on_mouse_pos(self, window: WindowBase, pos: tuple[float, float]) -> None:
        if not self.map:
            return

        (map_x, map_y) = self.map_layout.pos
        (mouse_x, mouse_y) = pos
        if self.map_layout.collide_point(*pos):
            x, y = self.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)
            if not self.highlight_rect:
                self.highlight_rect = self.map.grid.getHighlightRect(x, y)
            if self.highlight_rect not in self.map_layout.children:
                self.map_layout.canvas.add(self.highlight_rect)
            self.map.grid.updateRect(self.highlight_rect, x, y)

        elif self.highlight_rect in self.map_layout.canvas.children:
            self.map_layout.canvas.remove(self.highlight_rect)


    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.draw()

    def draw(self) -> None:
        self.map.draw()
        self.draw_party()
        self.draw_selected()

    def draw_party(self, ) -> None:
        if not self.party_bg:
            self.party_bg = self.map.grid.getRect(
                *self.campaign.position, self.map.grid.hidden_image_path
            )
        self.party_icon.pos = self.map.grid.tile_pos_from_index(*self.campaign.position)
        self.party_icon.size = self.map.grid.tile_size
        self.party_bg.pos = self.party_icon.pos
        self.party_bg.size = self.party_icon.size

        if self.party_bg not in self.map_layout.canvas.children:
            self.map_layout.canvas.add(self.party_bg)
        if self.party_icon not in self.map_layout.canvas.children:
            self.map_layout.canvas.add(self.party_icon)

    def draw_selected(self, ) -> None:
        if self.selected:
            self.select_rect.pos = self.map.grid.tile_pos_from_index(*self.selected)
            self.select_rect.size = self.map.grid.tile_size
            if self.select_rect not in self.map_layout.canvas.children:
                self.map_layout.canvas.add(self.select_rect)

            if self.selected == self.campaign.position:
                # Draw adjacent tiles
                if not self.adjacent:
                    self.adjacent = [
                        self.map.grid.getHighlightRect(*pos)
                        for pos in self.map.grid.adjacent(*self.selected)
                    ]
        else:
            if self.select_rect in self.map_layout.canvas.children:
                self.map_layout.canvas.remove(self.select_rect)


    def changeMap(self, name: str):
        new_location: Location = self.campaign.locations[name]
        self.map = new_location.map

        self.map_layout.canvas.clear()
        self.map.drawn_tiles = []
        self.map.map_rect = None
        self.map.getZoomForSurface(self.map_layout)
        # self._by_scroll()

        self.draw()

    def leave(self, ) -> Location:
        location = self.campaign.current_location
        self.selected = None
        parent = self.campaign.getLocation(location.parent)

        # TODO: Leave campaign?
        if parent is None:
            # Back to overworld
            return None
        else:
            self.changeMap(location.parent)

        # Update music if applicable
        if len(parent.music) > 0:
            self.update_playlist(parent)

        self.campaign.current_location = parent
        try:
            self.campaign.position = self.position_stack.pop()
        except:
            self.campaign.position = parent.position

        return parent

    def arrive(self, location: Location, from_pos: tuple[int, int]) -> None:
        self.selected = None
        self.campaign.current_location = location
        self.position_stack.append(self.campaign.position)
        self.campaign.position = location.entrances.get(from_pos, (0,0))
        self.changeMap(location.name)

    def on_button(self, px: float, py: float) -> bool:
        children = self.children[:]
        children.remove(self.map_layout)
        for child in children:
            if child.collide_point(px, py):
                return True
        return False
    
    def on_touch_move(self, event: MotionEvent):
        (mouse_x, mouse_y) = event.pos
        if self.on_button(mouse_x, mouse_y):
            return
        
        if event.grab_current is not self:
            return super().on_touch_move(event)
        new_x, new_y = event.pos

        if int(self.mouse_x) != int(new_x) and int(self.mouse_y) != int(new_y):
            self.moved = True

        self.map.window.x += self.mouse_x - new_x
        self.map.window.y += self.mouse_y - new_y
        self.mouse_x, self.mouse_y = (new_x, new_y)

        self.draw()
        


    def on_click(self, layout: FloatLayout, event: MotionEvent):
        if event.is_touch:
            self.mouse_x, self.mouse_y = event.pos
            event.grab(self)
            self.moved = False

    def on_click_up(self, layout: FloatLayout, event: MotionEvent):
        if self.moved:
            return
        
        (mouse_x, mouse_y) = event.pos

        # One of the buttons is already responding to this event, ignore
        if self.on_button(mouse_x, mouse_y):
            return

        if event.is_mouse_scrolling and self.last_zoom != event.pos:
            self.last_zoom = event.pos
            if event.button == "scrolldown":
                self.zoomIn(event)
            elif event.button == "scrollup":
                self.zoomOut(event)
            return


    def interact(self, x: int, y: int) -> None:
        # TODO: Right click to re-hide tile?
        pass

    def _byZoom(self, old_zoom: float, event: MotionEvent):
        mouse_x, mouse_y = event.pos

        zoom_factor = old_zoom / self.map.window.zoom
        self.map.window.x = (self.map.window.x + mouse_x) * zoom_factor - mouse_x 
        self.map.window.y = (self.map.window.y + mouse_y) * zoom_factor - mouse_y 
        self.draw()

    def zoomIn(self, event: MotionEvent):
        if self.map is None:
            return
        old_zoom = self.map.window.zoom
        self.map.window.zoom /= 1.5

        self._byZoom(old_zoom, event)

    def zoomOut(self, event: MotionEvent):
        if self.map is None:
            return
        old_zoom = self.map.window.zoom
        self.map.window.zoom *= 1.5

        self._byZoom(old_zoom, event)

