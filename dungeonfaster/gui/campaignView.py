import os
from datetime import datetime
from typing import TYPE_CHECKING

from kivy.core.audio import Sound, SoundLoader
from kivy.input.motionevent import MotionEvent
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from dungeonfaster.gui.audio import AudioPlayer
from dungeonfaster.gui.DMTools import DMTools
from dungeonfaster.gui.mapView import MapView
from dungeonfaster.gui.utilities import IconButton
from dungeonfaster.model.campaign import Campaign
from dungeonfaster.model.location import Location
from dungeonfaster.networking.server import CampaignServer

if TYPE_CHECKING:
    from kivy.graphics import Rectangle

DELTA_X_SHIFT = 15
DELTA_Y_SHIFT = 15

RESOURCES_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "resources")
CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")


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
        self.combat_button = IconButton(os.path.join(RESOURCES_DIR, "icons", "swords.png"))
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
        # self.campaign_view.player.volume_up()
        pass

    def volume_down(self, instance: Button) -> None:
        # self.campaign_view.player.volume_down()
        pass


class CampaignView(MapView):
    player: AudioPlayer

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(screen, **kwargs)

        self.dm_controls = DMTools(self, size_hint=(0.3, 0.05), pos_hint={"x": 0.65, "top": 0.9})
        self.audio_controller = AudioControllerLayout(self, size_hint=(0.3, 0.05), pos_hint={"x": 0.65, "y": 0.05})
        self.move_party_button = Button(
            text="Move Party",
            size_hint=(0.15, 0.05),
            pos_hint={"center_x": 0.8, "y": 0.1},
        )
        self.save_button = Button(text="save", size_hint=(0.1, 0.05), pos_hint={"x": 0.85, "y": 0.9})
        self.save_button.bind(on_press=self.on_click_save)

        self.adjacent: list[Rectangle] | None = None
        self.campaign: Campaign = Campaign()

        self.map_clicked = self.interact  # : callable[[int, int], None]

        self.music: list[Sound] = []
        self.combat_music: list[Sound] = []

        # Is the campaign running or being edited?
        self.running = False

        # self.map_layout.pos_hint = {"x": 0.025, "y": 0.025}
        # self.map_layout.size_hint=(0.95, 0.95)

        # Button to leave current location - go to parent
        self.leave_button = Button(text="leave", pos_hint={"x": 0.05, "y": 0.90}, size_hint=(0.1, 0.05))
        self.leave_button.bind(on_release=self.on_leave_cb)

        self.comms = CampaignServer()

    def start_server(self):
        self.comms.start_server(self)

    def add_controls(self) -> None:
        """Add buttons for DM control:
        - Go to location
        - Change/Stop music
        - Save campaign state
        """
        self.add_widget(self.dm_controls)

        self.add_widget(self.audio_controller)

        self.add_widget(self.move_party_button)
        self.move_party_button.bind(on_release=self.on_move_party_button)

        self.add_widget(self.save_button)

    def on_move_party_button(self, instance: Button) -> None:
        self.map_clicked = self.location_selected

    def on_click_save(self, instance: Button) -> None:
        save_file = os.path.join(
            CAMPAIGNS_DIR, f"{self.campaign.name}-{datetime.now().strftime('%Y%m%dT-%H%M%SZ')}.json"
        )
        self.save(save_file)

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

        # Get first parent with music
        tmp: Location = self.campaign.current_location
        # while tmp.parent is not None and len(tmp.music) == 0:
        #     tmp = self.campaign.get_location(tmp.parent)

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

    def clear_adjacent(self) -> None:
        if not self.adjacent:
            return

        for tile in self.adjacent:
            if tile in self.map_layout.canvas.children:
                self.map_layout.canvas.remove(tile)
        self.adjacent = None

    def change_map(self, name: str):
        new_location: Location = self.campaign.locations[name]
        self.map = new_location.map

        self.map_layout.canvas.clear()
        self.map.drawn_tiles = []
        self.map.map_rect = None
        self.map.get_zoom_for_surface(self.map_layout)
        # self._by_scroll()

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
        parent = super().leave()

        # Update music if applicable
        if len(parent.music) > 0:
            self.update_playlist(parent)

        return parent

    def arrive(self, location: Location, from_pos: tuple[int, int]) -> None:
        super().arrive(location, from_pos)

        # Update music if applicable
        if len(location.music) > 0:
            self.update_playlist(location)

        # Add button to leave location
        if self.leave_button not in self.children:
            self.add_widget(self.leave_button)

        # TODO: Send update

    def on_click_up(self, layout: FloatLayout, event: MotionEvent):
        if event.grab_current is None:
            return

        super().on_click_up(layout, event)

        if event.is_mouse_scrolling:  # and self.last_zoom != event.pos:
            return

        if self.moved:
            return

        (mouse_x, mouse_y) = event.pos

        # One of the buttons is already responding to this event, ignore
        if self.on_button(mouse_x, mouse_y):
            return

        if self.map:
            (map_x, map_y) = self.map_layout.pos
            (map_width, map_height) = self.map_layout.size

            # Ensure touch is on the map, ignore otherwise
            if map_x < mouse_x < map_x + map_width and map_y < mouse_y < map_y + map_height:
                x, y = self.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)
                if self.running:
                    self.map_clicked(x, y)
                else:
                    self.map.grid.flip_tile(x, y)
                self.draw()

    def interact(self, x: int, y: int) -> None:
        if self.selected:
            if (x, y) == self.selected:
                # Attempt to go to selected location
                if (x, y) == self.campaign.position and (x, y) in self.campaign.current_location.transitions:
                    self.arrive(
                        self.campaign.locations[self.campaign.current_location.transitions[(x, y)]],
                        (x, y),
                    )
                    self.clear_adjacent()
                self.selected = None

            # Move party to new location
            if self.selected == self.campaign.position and (x, y) in self.map.grid.adjacent(*self.campaign.position):
                self.move_party(x, y)

        elif self.map.revealed(x, y):
            self.selected = (x, y)
        elif self.map.hidden_tiles:
            self.map.flip_at_index(x, y)

        # TODO: Send update

    def move_party(self, x: int, y: int) -> None:
        self.campaign.position = (x, y)
        self.clear_adjacent()
        self.selected = None

        # Reveal adjacent tiles
        for adjacent in self.map.grid.adjacent(x, y):
            self.map.reveal(*adjacent)
