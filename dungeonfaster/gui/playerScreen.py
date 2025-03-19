import os
import time

from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from dungeonfaster.gui.menuManager import MenuManager
from dungeonfaster.gui.playerView import PlayerView
from dungeonfaster.model.campaign import Campaign
from dungeonfaster.networking.client import CampaignClient

USERS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "users")
# TODO: Add connection dialog box - username, password, server address


class PlayerScreen(Screen):
    client_connection: CampaignClient

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="Player")

        self.menuManager: MenuManager = manager

        self.player_view: PlayerView = PlayerView(self, size_hint=(1, 1))

        self.menuManager.add_widget(self)

        self.connectButton = Button(
            text="Connect",
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(0.2, 0.1),
        )
        self.connectButton.bind(on_press=self.connect_to_server)
        self.add_widget(self.connectButton)

    def connect_to_server(self, instance: Button):
        print("connect")

        self.connectButton.text = "Connecting..."
        self.client_connection = CampaignClient(self.player_view)

        self.client_connection.start_client(("127.0.0.1", 9191))

        while self.client_connection.established:
            print("Waiting...")
            time.sleep(1)

        # Load campaign
        self.player_view.campaign = Campaign()
        username = "user1"  # TODO: As input
        campaign_path = os.path.join(USERS_DIR, f"{username}.json")
        self.player_view.campaign.load(campaign_path, self.player_view.map_layout)
        self.player_view.map = self.player_view.campaign.current_location.map

        self.player_view.bind(on_touch_down=self.player_view.on_click)
        self.player_view.bind(on_touch_up=self.player_view.on_click_up)
        self.add_widget(self.player_view)
