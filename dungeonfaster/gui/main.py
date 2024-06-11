#!/usr/bin/python3

# import os

# os.environ["KIVY_AUDIO"] = "ffpyplayer"

from kivy.app import App

from dungeonfaster.gui.loadCampaignScreen import LoadCampaignScreen
from dungeonfaster.gui.menuManager import MenuManager
from dungeonfaster.gui.newCampaignScreen import NewCampaignScreen
from dungeonfaster.gui.runCampaignScreen import RunCampaignScreen


class DungeonFasterApp(App):
    def build(self):

        menuManager = MenuManager()
        menuManager.newCampaignScreen = NewCampaignScreen(menuManager)
        menuManager.addBackButton(menuManager.newCampaignScreen)
        menuManager.loadCampaignScreen = LoadCampaignScreen(menuManager)
        menuManager.addBackButton(menuManager.loadCampaignScreen)
        menuManager.runCampaignScreen = RunCampaignScreen(menuManager)
        # TODO: Exit campaign button?

        return menuManager
