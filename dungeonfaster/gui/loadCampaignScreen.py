import json
import os
import shutil
from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from dungeonfaster.gui.menuManager import MenuManager
from dungeonfaster.gui.utilities import FileDialog

CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")


class LoadCampaignEntry(BoxLayout):
    def __init__(self, campaign_path, load_cb, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        self.campaign_path = campaign_path

        # Load from campaign file
        campaign_path = os.path.join(CAMPAIGNS_DIR, campaign_path)
        with open(campaign_path) as campaign_file:
            string_data = campaign_file.read()
            load_data = json.loads(string_data)
            campaign_name = load_data["name"]

        campaign_mtime = os.path.getmtime(campaign_path)
        mtime_str = datetime.fromtimestamp(campaign_mtime).strftime("%H:%M %d-%m-%Y")

        name_label = Label(text=campaign_name, halign="left", valign="middle", size_hint=(0.25, 1))
        name_label.text_size = name_label.size
        display_path = campaign_path
        if len(display_path) > 50:
            display_path = display_path[:15] + "..." + display_path[-15:]
        file_label = Label(text=display_path, halign="left", size_hint=(0.25, 1))
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

        self.loadDialog = FileDialog(
            select_text="Load",
            popup_title="Load Campaign",
            on_select=self.on_load_other,
        )

        self.load_other_button = Button(
            text="Load Other",
            size_hint=(0.15, 0.1),
            pos_hint={"center_x": 0.9, "center_y": 0.9},
        )
        self.load_other_button.bind(on_release=self.loadDialog.open_dialog)
        self.add_widget(self.load_other_button)

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

        # TODO: Use RelativeLayout

        for campaign in campaigns:
            list_layout.add_widget(campaign)

        if len(campaigns) < 10:
            for _ in range(10 - len(campaigns)):
                list_layout.add_widget(Label(text="----Placeholder----"))

        list_layout.size_hint = (1, 1.5 * len(list_layout.children) / 10.0)

        campaigns_layout.add_widget(list_layout)

        self.menuManager.add_widget(self)

    def load(self, campaign_path: os.PathLike | str) -> None:
        self.manager.runCampaignScreen.load(campaign_path)
        self.manager.last_screen = self.name
        self.manager.current = self.manager.runCampaignScreen.name

    def load_cb(self, instance: Button):
        parent: LoadCampaignEntry = instance.parent

        path = os.path.join(CAMPAIGNS_DIR, parent.campaign_path)

        self.load(path)

    def on_load_other(self, instance: Button):
        campaign_path = self.loadDialog.textInput.text
        self.loadDialog.close_dialog(None)

        self.load(campaign_path)

        # Save a copy of campaign file in campaigns directory
        campaign_name = os.path.basename(campaign_path)
        shutil.copyfile(campaign_path, os.path.join(CAMPAIGNS_DIR, campaign_name))
