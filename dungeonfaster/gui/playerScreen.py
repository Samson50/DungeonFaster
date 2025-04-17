import os
import time

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from dungeonfaster.gui.menuManager import MenuManager
from dungeonfaster.gui.playerView import PlayerView
from dungeonfaster.gui.utilities import LabeledTextInput
from dungeonfaster.model.campaign import Campaign
from dungeonfaster.networking.client import CampaignClient

USERS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "users")
# TODO: Add connection dialog box - username, password, server address


class PlayerScreen(Screen):
    client_connection: CampaignClient

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="Player")

        self.host_addr = "127.0.0.1"
        self.host_port = 9191

        self.player_name = "Hoome"
        self.password = "password"

        self.menu_manager: MenuManager = manager

        self.player_view: PlayerView = PlayerView(self, size_hint=(1, 1))

        self.menu_manager.add_widget(self)

        self.connect_layout = BoxLayout(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(0.5, 0.2),
            orientation="vertical",
        )

        self.name_input = LabeledTextInput("Player Name:", self.on_player_str)
        self.password_input = LabeledTextInput("Password:", self.on_password_str, default_text="Ignore me")
        self.host_input = LabeledTextInput("Host Address:", self.on_host_str, default_text="127.0.0.1:9191")
        self.connect_button = Button(text="Connect")

        self.connect_button.bind(on_press=self.connect_to_server)
        self.connect_layout.add_widget(self.host_input)
        self.connect_layout.add_widget(self.name_input)
        self.connect_layout.add_widget(self.password_input)
        self.connect_layout.add_widget(self.connect_button)
        self.add_widget(self.connect_layout)

    def on_host_str(self, instance, value):
        # TODO: Validate address

        self.host_addr = value
        if ":" in value:
            self.host_addr = value.split(":")[0]
            self.host_port = int(value.split(":")[1])

    def on_player_str(self, instance, value):
        self.player_name = value
        self.player_view.name = value

    def on_password_str(self, instance, value):
        self.password = value

    def connect_to_server(self, instance: Button):
        self.connect_button.text = "Connecting..."
        # self.client_connection = CampaignClient(self.player_view, self.player_name)

        self.player_view.connect(self.player_name, (self.host_addr, self.host_port))

        while not self.player_view.comms.established and self.player_view.comms.running:
            time.sleep(1)

        self.remove_widget(self.connect_layout)

        if not self.player_view.comms.running:
            print("Client not running")
            return

        # Load campaign
        self.player_view.campaign = Campaign()
        campaign_path = os.path.join(USERS_DIR, f"{self.player_name}.json")

        files_needed = self.player_view.campaign.get_files(campaign_path)
        self.player_view.request_files(files_needed)

        self.player_view.campaign.load(campaign_path, self.player_view.map_layout)
        self.player_view.map = self.player_view.campaign.current_location.map
        self.player_view.populate_tiles(self.player_view.campaign.current_location)

        self.player_view.bind(on_touch_down=self.player_view.on_click)
        self.player_view.bind(on_touch_up=self.player_view.on_click_up)
        self.add_widget(self.player_view)
