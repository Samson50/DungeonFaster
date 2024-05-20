#!/usr/bin/python3

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from gui.menuManager import MenuManager
from gui.newCampaignScreen import NewCampaignScreen


class DungeonFasterApp(App):
    def build(self):

        menuManager = MenuManager()
        menuManager.newCampaignScreen = NewCampaignScreen(menuManager)
        menuManager.addBackButton(menuManager.newCampaignScreen)

        return menuManager
