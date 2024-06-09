from kivy.core.audio import SoundLoader, Sound
from kivy.graphics import Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from gui.utilities import FileDialog

from model.location import Location
from model.map import Map
from model.campaign import Campaign


DELTA_X_SHIFT = 15
DELTA_Y_SHIFT = 15


class CampaignView(FloatLayout):

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(**kwargs)

        self.screen = screen
        self.party_icon = Rectangle(
            source="resources/icons/party.png",
        )
        self.party_bg = None
        self.selected: tuple[int, int] = None
        self.select_rect: Rectangle = Rectangle(source="resources/icons/selected.png")
        self.adjacent: list[Rectangle] = None
        self.position_stack: list[tuple[int, int]] = []
        self.map: Map = None
        self.campaign: Campaign = Campaign()
        self.music: list[Sound] = []
        self.combat_music: list[Sound] = []

        # Is the campaign running or being edited?
        self.running = False

        self.map_layout = FloatLayout(
            pos_hint={"x": 0.025, "y": 0.025}, size_hint=(0.95, 0.95)
        )
        self.add_widget(self.map_layout)

        self.getMapButton = Button(text="Select Overworld Map")
        self.getMapButton.bind(on_release=self.selectOverworldMapDialog)
        self.add_widget(self.getMapButton)

        self.x_slider: Slider = Slider(
            min=0,
            max=1,
            value=0.0,
            orientation="horizontal",
            step=0.01,
            size_hint=(0.9, 0.05),
            pos_hint={"x": 0.05, "y": 0.0},
        )

        self.y_slider: Slider = Slider(
            min=0,
            max=1,
            value=0.0,
            orientation="vertical",
            step=0.01,
            size_hint=(0.05, 0.9),
            pos_hint={"x": 0.0, "y": 0.05},
        )

    def add_controls(self) -> None:
        """TODO: add buttons for DM control:
        - Go to location
        - Change/Stop music
        """
        pass

    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.draw()

    def save(self, file):
        self.campaign.save(file)

    def load(self, load_path):
        self.remove_widget(self.getMapButton)
        self.campaign.load(load_path, self.map_layout)
        self.map = self.campaign.current_location.map
        self.set_sliders()

        # Load musics as list of Sound
        for song in self.campaign.current_location.music:
            self.music.append(SoundLoader.load(song))
        for song in self.campaign.current_location.combat_music:
            self.combat_music.append(SoundLoader.load(song))

    # TODO: move back to newCampaignScreen
    def selectOverworldMapDialog(self, instance):
        self.overworldMapDialog = FileDialog(
            popup_title="Select Overworld Map",
            on_select=self.saveOverworldMap,
        )

        self.overworldMapDialog.openDialog(None)

    def draw(self) -> None:
        self.map.draw()
        self.draw_party()
        self.draw_selected()

    def draw_party(self) -> None:
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

    def clear_adjacent(self) -> None:
        for tile in self.adjacent:
            if tile in self.map_layout.canvas.children:
                self.map_layout.canvas.remove(tile)
        self.adjacent = None

    def draw_selected(self) -> None:
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

                for tile in self.adjacent:
                    # tile.pos = self.map.grid.pixel_to_index
                    if tile not in self.map_layout.canvas.children:
                        self.map_layout.canvas.add(tile)
        else:
            if self.select_rect in self.map_layout.canvas.children:
                self.map_layout.canvas.remove(self.select_rect)

            if self.adjacent:
                self.clear_adjacent()

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
        self.draw()

        self.set_sliders()

    def set_sliders(self):
        self.add_widget(self.x_slider)
        self.add_widget(self.y_slider)
        self.x_slider.bind(value=self.x_scroll)
        self.y_slider.bind(value=self.y_scroll)

    def x_scroll(self, instance: Slider, value):
        width = self.map.width / self.map.window.zoom - self.map.window.surface.width
        self.map.window.x = width * value
        self.draw()

    def y_scroll(self, instance: Slider, value: float) -> None:
        height = self.map.height / self.map.window.zoom - self.map.window.surface.height
        self.map.window.y = height * value
        self.draw()

    def _by_scroll(self):
        width = self.map.width / self.map.window.zoom - self.map.window.surface.width
        self.map.window.x = width * self.x_slider.value

        height = self.map.height / self.map.window.zoom - self.map.window.surface.height
        self.map.window.y = height * self.y_slider.value

        self.draw()

    def changeMap(self, map: Map):
        self.map = map

        self.map_layout.canvas.clear()
        self.drawn_tiles = []
        self.map.map_rect = None
        self.map.getZoomForSurface(self.map_layout)
        self.draw()

    def add_location(self, location: Location, x: int, y: int) -> None:
        # Add location to current location or campaign
        if self.campaign.current_location is None:
            self.campaign.locations[(x, y)] = location
            self.campaign.current_location = location
        else:
            self.campaign.current_location.locations[(x, y)] = location
            self.map.points_of_interest.append((x, y))

    def add_music(self, music_file: str) -> None:
        self.campaign.current_location.music.append(music_file)

    def add_combat_music(self, music_file: str) -> None:
        self.campaign.current_location.combat_music.append(music_file)

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
        try:
            self.campaign.position = self.position_stack.pop()
        except:
            self.campaign.position = location.parent.start_position

        return location.parent

    def arrive(self, location: Location) -> None:
        self.campaign.current_location = location
        self.position_stack.append(self.campaign.position)
        self.campaign.position = location.start_position
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

        if self.map:
            (map_x, map_y) = self.map_layout.pos
            (map_width, map_height) = self.map_layout.size

            # Ensure touch is on the map, ignore otherwise
            if (
                map_x < mouse_x < map_x + map_width
                and map_y < mouse_y < map_y + map_height
            ):
                try:
                    x, y = self.map.grid.pixel_to_index(
                        mouse_x - map_x, mouse_y - map_y
                    )
                    print(f"{(x, y)}")
                    if self.running:
                        self.interact(x, y)
                    else:
                        self.map.grid.flip_tile(x, y)
                    self.draw()
                # TODO: Deliberate error message and catching index error
                except Exception as e:
                    print(f"Error in interaction: {e}")

    def interact(self, x: int, y: int) -> None:
        # TODO: Right click to re-hide tile?
        if self.selected:
            if (x, y) == self.selected:
                # Attempt to go to selected location
                if (x, y) == self.campaign.position:
                    # TODO: if self.selected in locations...
                    if (x, y) in self.campaign.current_location.locations.keys():
                        self.arrive(self.campaign.current_location.locations[(x, y)])
                        self.clear_adjacent()
                self.selected = None

            # Move party to new location
            if self.selected == self.campaign.position:
                if (x, y) in self.map.grid.adjacent(*self.campaign.position):
                    self.campaign.position = (x, y)
                    self.clear_adjacent()
                    self.selected = None

                    # Reveal adjacent tiles
                    for adjacent in self.map.grid.adjacent(x, y):
                        self.map.reveal(*adjacent)

        elif self.map.revealed(x, y):
            self.selected = (x, y)
        elif self.map.hidden_tiles:
            self.map.flip_at_index(x, y)

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
