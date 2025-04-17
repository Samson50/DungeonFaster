from typing import override

from kivy.input.motionevent import MotionEvent
from kivy.uix.floatlayout import FloatLayout

from dungeonfaster.gui.mapView import MapView
from dungeonfaster.networking.client import CampaignClient


class PlayerView(MapView):
    name: str

    def connect(self, name: str, addr: tuple[str, int]):
        self.comms = CampaignClient(self, name)
        self.comms.start_client(addr)

    def request_files(self, files_needed: list[str]):
        self.comms.request_files(files_needed)

    @override
    def on_click(self, layout: FloatLayout, event: MotionEvent):
        # One of the buttons is already responding to this event, ignore
        if not self.collide_point(*event.pos) or self.on_button(*event.pos):
            return

        if event.is_touch:
            self.mouse_x, self.mouse_y = event.pos
            event.grab(self)
            self.moved = False
            if self.grabbing_token(event):
                self.moving_token = True

    @override
    def grabbing_token(self, event: MotionEvent):
        mouse_x, mouse_y = event.pos
        (map_x, map_y) = self.map_layout.pos
        cursor_inedx = self.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)

        player_token = next(token for token in self.party_tiles if self.name == token.name)
        if player_token.index == cursor_inedx:
            self.active_tile = player_token
            return True

        return False
