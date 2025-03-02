import os

from kivy.uix.screenmanager import Screen

from dungeonfaster.gui.campaignView import CampaignView
from dungeonfaster.gui.menuManager import MenuManager


class RunCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="RunCampaign")

        self.menuManager: MenuManager = manager

        self.campaign_view: CampaignView = CampaignView(self, size_hint=(1, 1))
        self.campaign_view.running = True
        self.campaign_view.bind(on_touch_down=self.campaign_view.on_click)
        self.campaign_view.bind(on_touch_up=self.campaign_view.on_click_up)
        self.add_widget(self.campaign_view)

        self.menuManager.add_widget(self)

        # Add exit button (return to main menu)

        # Add general DM controls
        self.campaign_view.add_controls()

    def load(self, campaign_path: os.PathLike) -> None:
        self.campaign_view.load(campaign_path)
