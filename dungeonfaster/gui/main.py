#!/usr/bin/python3

# import os

# os.environ["KIVY_AUDIO"] = "ffpyplayer"

from kivy.app import App

from dungeonfaster.gui.loadCampaignScreen import LoadCampaignScreen
from dungeonfaster.gui.menuManager import MenuManager
from dungeonfaster.gui.newCampaignScreen import NewCampaignScreen
from dungeonfaster.gui.playerScreen import PlayerScreen
from dungeonfaster.gui.runCampaignScreen import RunCampaignScreen


class DungeonFasterApp(App):
    def build(self):
        menu_manager = MenuManager()
        menu_manager.newCampaignScreen = NewCampaignScreen(menu_manager)
        menu_manager.add_back_button(menu_manager.newCampaignScreen)
        menu_manager.loadCampaignScreen = LoadCampaignScreen(menu_manager)
        menu_manager.add_back_button(menu_manager.loadCampaignScreen)
        menu_manager.runCampaignScreen = RunCampaignScreen(menu_manager)
        menu_manager.playerScreen = PlayerScreen(menu_manager)
        # TODO: Exit campaign button?

        return menu_manager
