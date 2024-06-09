#!/usr/bin/python3

from kivy.app import App

from gui.loadCampaignScreen import LoadCampaignScreen
from gui.menuManager import MenuManager
from gui.newCampaignScreen import NewCampaignScreen
from gui.runCampaignScreen import RunCampaignScreen


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
