#!/usr/bin/python3

from kivy.app import App

from gui.menuManager import MenuManager
from gui.newCampaignScreen import NewCampaignScreen


class DungeonFasterApp(App):
    def build(self):

        menuManager = MenuManager()
        menuManager.newCampaignScreen = NewCampaignScreen(menuManager)
        menuManager.addBackButton(menuManager.newCampaignScreen)

        return menuManager
