import os

from kivy.core.audio import SoundLoader, Sound
from kivy.core.window import Window, WindowBase
from kivy.graphics import Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from dungeonfaster.gui.utilities import FileDialog, IconButton

from dungeonfaster.model.location import Location
from dungeonfaster.model.map import Map
from dungeonfaster.model.campaign import Campaign


DELTA_X_SHIFT = 15
DELTA_Y_SHIFT = 15

RESOURCES_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "resources")
CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")

# TODO: |
#       V
# class DMControls(BoxLayout):
#   def __init__(self, view: CampaignView)


class AudioControllerLayout(BoxLayout):
    def __init__(self, campaign_view, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.campaign_view: CampaignView = campaign_view
        self.in_combat = False

        self.skip_back_button = Button(text="<<")
        # self.skip_back_button.bind(on_release=self.play_previous)
        self.pause_button = Button(text="||")
        self.pause_button.bind(on_release=self.pause)
        self.play_button = Button(text="|>")
        self.play_button.bind(on_release=self.play)
        self.skip_forward_button = Button(text=">>")
        self.skip_forward_button.bind(on_release=self.play_next)
        self.combat_button = IconButton(
            os.path.join(RESOURCES_DIR, "icons", "swords.png")
        )
        self.combat_button.bind(on_release=self.switch_combat)
        self.volume_up_button = Button(text="+")
        self.volume_up_button.bind(on_release=self.volume_up)
        self.volume_down_button = Button(text="-")
        self.volume_down_button.bind(on_release=self.volume_down)

        self.add_widget(self.skip_back_button)
        self.add_widget(self.pause_button)
        self.add_widget(self.skip_forward_button)
        self.add_widget(self.combat_button)
        self.add_widget(self.volume_up_button)
        self.add_widget(self.volume_down_button)

    def pause(self, instance: Button) -> None:
        self.campaign_view.player.pause()
        index: int = self.children.index(instance)
        self.remove_widget(instance)
        self.add_widget(self.play_button, index)

    def play(self, instance: Button) -> None:
        self.campaign_view.player.play()
        index: int = self.children.index(instance)
        self.remove_widget(instance)
        self.add_widget(self.pause_button, index)

    def play_next(self, instance: Button) -> None:
        self.campaign_view.player.play_next()

    def switch_combat(self, instance: Button) -> None:
        if self.in_combat:
            self.campaign_view.player.change_playlist(self.campaign_view.music)
        else:
            self.campaign_view.player.change_playlist(self.campaign_view.combat_music)

        self.in_combat = not self.in_combat

    def volume_up(self, instance: Button) -> None:
        self.campaign_view.player.volume_up()

    def volume_down(self, instance: Button) -> None:
        self.campaign_view.player.volume_down()


class AudioPlayer:
    def __init__(self, playlist: list[Sound]):
        self.playlist = playlist
        self.resume_position = 0
        self.index = 0
        self.volume = 0  # 0.5
        self.started = 0

    def change_playlist(self, playlist: list[Sound]):
        self._stop(self.playlist[self.index])
        self.index = 0
        self.playlist = playlist
        self.play()

    def play(self):
        self.playlist[self.index].play()
        # TODO: Resume isn't working and I don't know why
        if self.resume_position != 0:
            self.playlist[self.index].seek(self.resume_position)
            self.resume_position = 0
        self.playlist[self.index].volume = self.volume
        self.playlist[self.index].bind(on_stop=self._play_next)

    def _play_next(self, instance: Sound):
        self._stop(instance)
        self.index = (self.index + 1) % len(self.playlist)
        self.resume_position = 0
        self.play()

    def play_next(self):
        sound: Sound = self.playlist[self.index]
        self._play_next(sound)

    def _stop(self, sound: Sound) -> None:
        sound.unbind(on_stop=self._play_next)
        sound.stop()

    def pause(self):
        self.resume_position = self.playlist[self.index].get_pos()
        self._stop(self.playlist[self.index])

    def volume_up(self):
        self.volume = self.volume + 0.05
        self.volume = min(self.volume, 1)
        self.playlist[self.index].volume = self.volume

    def volume_down(self):
        self.volume = self.volume - 0.05
        self.volume = max(self.volume, 0)
        self.playlist[self.index].volume = self.volume


# TODO: Use RelativeLayout?
class CampaignView(FloatLayout):

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.mouse_x = 0
        self.mouse_y = 0
        self.moved = False

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
        self.adjacent: list[Rectangle] = None
        self.position_stack: list[tuple[int, int]] = []
        self.map: Map = None
        self.campaign: Campaign = Campaign()

        self.map_clicked = self.interact  # : callable[[int, int], None]

        self.player: AudioPlayer = None
        self.music: list[Sound] = []
        self.combat_music: list[Sound] = []

        # Is the campaign running or being edited?
        self.running = False

        self.map_layout = FloatLayout(
            pos_hint={"x": 0.025, "y": 0.025}, size_hint=(0.95, 0.95)
        )
        self.add_widget(self.map_layout)

        # Button to leave current location - go to parent
        self.leave_button = Button(
            text="leave", pos_hint={"x": 0.05, "y": 0.90}, size_hint=(0.1, 0.05)
        )
        self.leave_button.bind(on_release=self.on_leave_cb)

        # Sliders to control map view window position
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

    def add_controls(self) -> None:
        """Add buttons for DM control:
        - Go to location
        - Change/Stop music
        - Save campaign state
        """
        self.audio_controller = AudioControllerLayout(
            self, size_hint=(0.3, 0.05), pos_hint={"x": 0.65, "y": 0.05}
        )
        self.add_widget(self.audio_controller)

        self.move_party_button = Button(
            text="Move Party",
            size_hint=(0.15, 0.05),
            pos_hint={"center_x": 0.8, "y": 0.1},
        )
        self.add_widget(self.move_party_button)
        self.move_party_button.bind(on_release=self.on_move_party_button)

        self.save_button = Button(
            text="save", size_hint=(0.1, 0.05), pos_hint={"x": 0.85, "y": 0.9}
        )
        self.add_widget(self.save_button)

    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.draw()

    def on_move_party_button(self, instance: Button) -> None:
        self.map_clicked = self.location_selected

    def location_selected(self, x: int, y: int) -> None:
        self.move_party(x, y)
        self.map_clicked = self.interact

    def save(self, file):
        # TODO: This works*, but is not intuitive behavior
        if not os.path.isabs(file):
            file = os.path.join(CAMPAIGNS_DIR, file)

        self.campaign.save(file)

    def load(self, load_path):
        self.campaign.load(load_path, self.map_layout)
        self.map = self.campaign.current_location.map
        self.set_sliders()
        self._by_scroll()

        # Get first parent with music
        tmp: Location = self.campaign.current_location
        while tmp.parent is not None and len(tmp.music) == 0:
            tmp = self.campaign.getLocation(tmp.parent)

        # Load musics as list of Sound
        if len(tmp.music) > 0:
            self.update_playlist(tmp)

        self.draw()

    def update_playlist(self, location: Location) -> None:
        for song in location.music:
            sound = SoundLoader.load(song)
            if sound:
                self.music.append(sound)
        for song in location.combat_music:
            sound = SoundLoader.load(song)
            if sound:
                self.combat_music.append(sound)

        if len(self.music) > 0:
            self.player = AudioPlayer(self.music)
            self.player.play()

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
        if not self.adjacent:
            return

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

    def changeMap(self, name: str):
        new_location: Location = self.campaign.locations[name]
        self.map = new_location.map

        self.map_layout.canvas.clear()
        self.map.drawn_tiles = []
        self.map.map_rect = None
        self.map.getZoomForSurface(self.map_layout)
        self._by_scroll()

        self.draw()

    def add_location(self, location: Location, name: str) -> None:
        # Add location to current location or campaign
        self.campaign.locations[name] = location

    def add_music(self, music_file: str) -> None:
        self.campaign.current_location.music.append(music_file)

    def add_combat_music(self, music_file: str) -> None:
        self.campaign.current_location.combat_music.append(music_file)

    def on_leave_cb(self, instance: Button) -> None:
        new_location: Location = self.leave()

        if new_location.parent is None and self.leave_button in self.children:
            self.remove_widget(self.leave_button)

    def leave(self) -> Location:
        location = self.campaign.current_location
        self.selected = None
        parent = self.campaign.getLocation(location.parent)

        # Should not get here, but just in case
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
        print(f"from_pos: {from_pos}")
        print(type(from_pos))
        print(f"entrances: {location.entrances}")
        [print(type(key)) for key in location.entrances.keys()]
        self.campaign.position = location.entrances.get(from_pos, (0,0))
        self.changeMap(location.name)

        # Update music if applicable
        if len(location.music) > 0:
            self.update_playlist(location)

        # Add button to leave location
        if self.leave_button not in self.children:
            self.add_widget(self.leave_button)

    def on_button(self, px: float, py: float) -> bool:
        children = [x for x in self.children]
        children.remove(self.map_layout)
        for child in children:
            if child.collide_point(px, py):
                return True
        return False
    
    def on_touch_move(self, event: MotionEvent):
        if event.grab_current is not self:
            return super().on_touch_move(event)
        new_x, new_y = event.pos

        if int(self.mouse_x) != int(new_x) and int(self.mouse_y) != int(new_y):
            # print(new_x, new_y, self.mouse_x, self.mouse_y)
            self.moved = True

        self.map.window.x += self.mouse_x - new_x
        self.map.window.y += self.mouse_y - new_y
        self.mouse_x, self.mouse_y = (new_x, new_y)

        # TODO: Update slider based on changed 
        width = self.map.width / self.map.window.zoom - self.map.window.surface.width
        # self.map.window.x = width * self.x_slider.value
        if 0 != width:
            self.x_slider.value = self.map.window.x / width

        height = self.map.height / self.map.window.zoom - self.map.window.surface.height
        # self.map.window.y = height * self.y_slider.value
        if 0 != height:
            self.y_slider.value = self.map.window.y / height

        self.draw()
        


    def on_click(self, layout: FloatLayout, event: MotionEvent):
        if event.is_touch:
            self.mouse_x, self.mouse_y = event.pos
            event.grab(self)
            self.moved = False

    def on_click_up(self, layout: FloatLayout, event: MotionEvent):
        if self.moved:
            return

        if event.is_mouse_scrolling:
            if event.button == "scrolldown":
                self.zoomIn()
            elif event.button == "scrollup":
                self.zoomOut()
            return

        (mouse_x, mouse_y) = event.pos
        # Ensure we're not using sliders already
        if self.x_slider.collide_point(mouse_x, mouse_y) or self.y_slider.collide_point(
            mouse_x, mouse_y
        ):
            return

        # One of the buttons is already responding to this event, ignore
        if self.on_button(mouse_x, mouse_y):
            return

        if self.map:
            (map_x, map_y) = self.map_layout.pos
            (map_width, map_height) = self.map_layout.size

            # Ensure touch is on the map, ignore otherwise
            if (
                map_x < mouse_x < map_x + map_width
                and map_y < mouse_y < map_y + map_height
            ):
                x, y = self.map.grid.pixel_to_index(
                    mouse_x - map_x, mouse_y - map_y
                )
                # print(f"{(x, y)}")
                if self.running:
                    self.map_clicked(x, y)
                else:
                    self.map.grid.flip_tile(x, y)
                self.draw()

    def interact(self, x: int, y: int) -> None:
        # TODO: Right click to re-hide tile?
        print(f"Selected: ({x}, {y})")
        if self.selected:
            if (x, y) == self.selected:
                # Attempt to go to selected location
                if (x, y) == self.campaign.position:
                    # If self.selected in transitions...
                    # print(f"({x}, {y}) in {self.campaign.current_location.transitions}")
                    if (x,y) in self.campaign.current_location.transitions:
                        self.arrive(self.campaign.locations[self.campaign.current_location.transitions[(x,y)]], (x, y))
                        self.clear_adjacent()
                self.selected = None

            # Move party to new location
            if self.selected == self.campaign.position:
                if (x, y) in self.map.grid.adjacent(*self.campaign.position):
                    self.move_party(x, y)

        elif self.map.revealed(x, y):
            self.selected = (x, y)
        elif self.map.hidden_tiles:
            self.map.flip_at_index(x, y)

    def move_party(self, x: int, y: int) -> None:
        self.campaign.position = (x, y)
        self.clear_adjacent()
        self.selected = None

        # Reveal adjacent tiles
        for adjacent in self.map.grid.adjacent(x, y):
            self.map.reveal(*adjacent)

    def zoomIn(self):
        if self.map is None:
            return
        self.map.window.zoom /= 1.5
        self._by_scroll()

    def zoomOut(self):
        if self.map is None:
            return
        self.map.window.zoom *= 1.5
        self._by_scroll()
