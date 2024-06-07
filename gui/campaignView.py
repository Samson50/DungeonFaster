from kivy.input.motionevent import MotionEvent
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.slider import Slider

from gui.utilities import FileDialog

from model.location import Location
from model.map import Map
from model.campaign import Campaign
from functools import partial


DELTA_X_SHIFT = 15
DELTA_Y_SHIFT = 15


class CampaignView(FloatLayout):

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(**kwargs)

        self.map: Map = None
        self.campaign: Campaign = Campaign()
        self.screen = screen
        self.map_layout = FloatLayout(
            pos_hint={"x": 0.025, "y": 0.025}, size_hint=(0.95, 0.95)
        )
        self.add_widget(self.map_layout)

        self.getMapButton = Button(text="Select Overworld Map")
        self.getMapButton.bind(on_release=self.selectOverworldMapDialog)
        self.add_widget(self.getMapButton)

        self.x_slider = Slider(
            min=0,
            max=1,
            value=0.0,
            orientation="horizontal",
            step=0.01,
            size_hint=(0.9, 0.05),
            pos_hint={"x": 0.05, "y": 0.0},
        )

        self.y_slider = Slider(
            min=0,
            max=1,
            value=0.0,
            orientation="vertical",
            step=0.01,
            size_hint=(0.05, 0.9),
            pos_hint={"x": 0.0, "y": 0.05},
        )

    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.map.draw()

    def save(self, file):
        self.campaign.save(file)

    def load(self, load_path):
        self.remove_widget(self.getMapButton)
        self.campaign.load(load_path, self.map_layout)
        self.map = self.campaign.current_location.map
        self.set_sliders()

    # TODO: move back to newCampaignScreen
    def selectOverworldMapDialog(self, instance):
        self.overworldMapDialog = FileDialog(
            popup_title="Select Overworld Map",
            on_select=self.saveOverworldMap,
        )

        self.overworldMapDialog.openDialog(None)

    def saveOverworldMap(self, instance):
        # Set overworld map file
        overworldMapFile = self.overworldMapDialog.textInput.text
        self.remove_widget(self.getMapButton)
        self.overworldMapDialog.closeDialog(None)

        base_location = Location("overworld", 0, 0)
        base_location.set_map(overworldMapFile)
        self.map = base_location.map

        self.add_location(base_location, 0, 0)

        self.map.getZoomForSurface(self.map_layout)
        self.map.draw()

        self.set_sliders()

    def set_sliders(self):
        self.add_widget(self.x_slider)
        self.add_widget(self.y_slider)
        self.x_slider.bind(value=self.x_scroll)
        self.y_slider.bind(value=self.y_scroll)

    def x_scroll(self, instance: Slider, value):
        width = self.map.width / self.map.window.zoom - self.map.window.surface.width
        self.map.window.x = width * value
        self.map.draw()

    def y_scroll(self, instance: Slider, value: float) -> None:
        height = self.map.height / self.map.window.zoom - self.map.window.surface.height
        self.map.window.y = height * value
        self.map.draw()

    def _by_scroll(self):
        width = self.map.width / self.map.window.zoom - self.map.window.surface.width
        self.map.window.x = width * self.x_slider.value

        height = self.map.height / self.map.window.zoom - self.map.window.surface.height
        self.map.window.y = height * self.y_slider.value

        self.map.draw()

    def changeMap(self, map: Map):
        self.map = map

        self.map_layout.canvas.clear()
        self.map.drawn_tiles = []
        self.map.map_rect = None
        self.map.getZoomForSurface(self.map_layout)
        self.map.draw()

    def add_location(self, location: Location, x: int, y: int) -> None:
        # Add location to current location or campaign
        if self.campaign.current_location is None:
            self.campaign.locations[(x, y)] = location
            self.campaign.current_location = location
        else:
            self.campaign.current_location.locations[(x, y)] = location
            self.map.points_of_interest.append((x, y))

    def leave(self) -> Location:
        location = self.campaign.current_location

        # Should not get here, but just in case
        # TODO: Leave campaign?
        if location.parent is None:
            # Back to overworld
            return None
        else:
            self.changeMap(location.parent.map)

        self.campaign.current_location = location.parent

        return location.parent

    def arrive(self, location: Location) -> None:
        self.campaign.current_location = location
        self.changeMap(location.map)

    def on_click(self, layout: FloatLayout, event: MotionEvent):
        if event.is_mouse_scrolling:
            if event.button == "scrolldown":
                self.zoomIn(0.0)
            elif event.button == "scrollup":
                self.zoomOut(0.0)
            return

        (mouse_x, mouse_y) = event.pos
        # Ensure we're not using sliders already
        if self.x_slider.collide_point(mouse_x, mouse_y) or self.y_slider.collide_point(
            mouse_x, mouse_y
        ):
            return

        if self.map and self.map.hidden_tiles:
            (map_x, map_y) = self.map_layout.pos
            (map_width, map_height) = self.map_layout.size

            # Ensure touch is on the map, ignore otherwise
            if (
                map_x < mouse_x < map_x + map_width
                and map_y < mouse_y < map_y + map_height
            ):
                try:
                    self.map.flip_at_coordinate(mouse_x - map_x, mouse_y - map_y)
                    self.map.draw()
                # TODO: Deliberate error message and catching index error
                except Exception as e:
                    print(e)

    def zoomIn(self, value: float):
        if self.map is None:
            return
        self.map.window.zoom -= 1
        self._by_scroll()

    def zoomOut(self, value: float):
        if self.map is None:
            return
        self.map.window.zoom += 1
        self._by_scroll()
