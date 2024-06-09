import os
import json
from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView

CAMPAIGNS_DIR = "campaigns"


class MenuManager(ScreenManager):

    def __init__(self):
        super().__init__()

        self.mainMenuScreen = MainMenuScreen(self)
        self.last_screen = self.mainMenuScreen.name

        self.newCampaignScreen: Screen = None

        self.loadCampaignScreen = LoadCampaignScreen(self)
        self.addBackButton(self.loadCampaignScreen)
        # self.runCampaignScreen = RunCampaignScreen(self)
        # self.addBackButton

        self.current = self.mainMenuScreen.name

    def addBackButton(self, screen: Screen):
        backButton = Button(
            text="<",
            pos_hint={"center_x": 0.1, "center_y": 0.9},
            size_hint={0.15, 0.1},
        )
        backButton.bind(on_release=self.toLastScreen)

        screen.add_widget(backButton)

    def toNewCampaignScreen(self, instance):
        self.last_screen = self.current
        self.current = self.newCampaignScreen.name

    def toLoadCampaignScreen(self, instance):
        self.last_screen = self.current
        self.current = self.loadCampaignScreen.name

    def toMainMenuScreen(self, instance):
        self.last_screen = self.current
        self.current = self.mainMenuScreen.name

    def toLastScreen(self, instance):
        self.current = self.last_screen


class LoadCampaignEntry(BoxLayout):
    def __init__(self, campaign_path, load_cb, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        self.campaign_path = campaign_path

        # Load from campaign file
        campaign_path = os.path.join(CAMPAIGNS_DIR, campaign_path)
        with open(campaign_path, "r") as campaign_file:
            string_data = campaign_file.read()
            load_data = json.loads(string_data)
            campaign_name = load_data["name"]

        campaign_mtime = os.path.getmtime(campaign_path)
        mtime_str = datetime.fromtimestamp(campaign_mtime).strftime("%H:%M %d-%m-%Y")

        name_label = Label(
            text=campaign_name, halign="left", valign="middle", size_hint=(0.25, 1)
        )
        name_label.text_size = name_label.size
        file_label = Label(text=campaign_path, halign="left", size_hint=(0.25, 1))
        last_modified_label = Label(text=mtime_str, halign="left", size_hint=(0.25, 1))
        load_button = Button(text="Load", size_hint=(0.25, 1))
        load_button.bind(on_press=load_cb)

        self.add_widget(name_label)
        self.add_widget(file_label)
        self.add_widget(last_modified_label)
        self.add_widget(load_button)


class LoadCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="LoadCampaign")

        self.menuManager = manager

        layout = BoxLayout(orientation="vertical")

        head_layout = BoxLayout(size_hint=(1, 0.2))
        head_layout.add_widget(
            Label(
                font_size=20,
                text="Load Campaign",
            )
        )
        layout.add_widget(head_layout)

        campaigns_layout = ScrollView(do_scroll_x=False, size_hint=(1, 0.8))
        list_layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 2),
        )
        layout.add_widget(campaigns_layout)
        self.add_widget(layout)

        campaigns = []
        for campaign_file in os.listdir(CAMPAIGNS_DIR):
            if campaign_file.endswith(".json"):
                campaigns.append(LoadCampaignEntry(campaign_file, self.load_cb))

        # TODO: I hate this relative size bull$#!7. How can I set explicit sizes and use relative positions?
        # n_layouts = int(list_layout.height / 10)

        for campaign in campaigns:
            list_layout.add_widget(campaign)

        # for i in range(n_layouts - len(campaigns)):
        if len(campaigns) < 10:
            for i in range(10 - len(campaigns)):
                list_layout.add_widget(Label(text="----Placeholder----"))

        list_layout.size_hint = (1, 1.5 * len(list_layout.children) / 10.0)

        campaigns_layout.add_widget(list_layout)

        self.menuManager.add_widget(self)

    def load_cb(self, instance: Button):
        parent: LoadCampaignEntry = instance.parent
        print(f"Loading campaign: {parent.campaign_path}")


class MainMenuScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="Menu")

        self.menuManager = manager

        layout = FloatLayout()
        layout = FloatLayout(size=(400, 400))

        layout.add_widget(
            Label(
                font_size=40,
                text="DungeonFaster",
                pos_hint={"center_x": 0.5, "center_y": 0.8},
            )
        )

        loadCampaignButton = Button(
            text="Load Campaign",
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint={0.2, 0.1},
        )
        layout.add_widget(loadCampaignButton)
        loadCampaignButton.bind(on_press=self.menuManager.toLoadCampaignScreen)

        newCampaignButton = Button(
            text="New/Edit Campaign",
            pos_hint={"center_x": 0.5, "center_y": 0.3},
            size_hint={0.2, 0.1},
        )
        layout.add_widget(newCampaignButton)
        newCampaignButton.bind(on_press=self.menuManager.toNewCampaignScreen)

        self.add_widget(layout)

        self.menuManager.add_widget(self)
