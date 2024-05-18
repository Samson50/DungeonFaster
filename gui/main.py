#!/usr/bin/python3

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label


def dummy_callback(instance):
    print(f"Button {instance} pressed")


class MenuManager(ScreenManager):

    def __init__(self):
        super().__init__()

        self.mainMenuScreen = MainMenuScreen(self)
        self.last_screen = self.mainMenuScreen.name

        self.newCampaignScreen = NewCampaignScreen(self)
        self.addBackButton(self.newCampaignScreen)

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


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager

        layout = FloatLayout()
        layout = FloatLayout(size=(400, 400))

        layout.add_widget(
            Label(
                font_size=20,
                text="New Campaign",
                pos_hint={"center_x": 0.5, "center_y": 0.9},
            )
        )

        self.add_widget(layout)
        self.menuManager.add_widget(self)


class LoadCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="LoadCampaign")

        self.menuManager = manager

        layout = FloatLayout()
        layout = FloatLayout(size=(400, 400))

        layout.add_widget(
            Label(
                font_size=20,
                text="Load Campaign",
                pos_hint={"center_x": 0.5, "center_y": 0.9},
            )
        )

        self.add_widget(layout)
        self.menuManager.add_widget(self)


class MainMenuScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="Menu")

        self.menuManager = manager

        layout = FloatLayout()
        layout = FloatLayout(size=(400, 400))

        # with layout.canvas:
        #     Color(rgba=(0, 0, 1, 1))
        #     Rectangle(size_hint={1, 1}, pos_hint={"center_x": 0.5, "center_y": 0.5})

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
            size_hint={0.15, 0.1},
        )
        layout.add_widget(loadCampaignButton)
        loadCampaignButton.bind(on_press=self.menuManager.toLoadCampaignScreen)

        newCampaignButton = Button(
            text="New Campaign",
            pos_hint={"center_x": 0.5, "center_y": 0.3},
            size_hint={0.15, 0.1},
        )
        layout.add_widget(newCampaignButton)
        newCampaignButton.bind(on_press=self.menuManager.toNewCampaignScreen)

        self.add_widget(layout)

        self.menuManager.add_widget(self)


class DungeonFasterApp(App):
    def build(self):

        return MenuManager()


if __name__ == "__main__":
    DungeonFasterApp().run()
