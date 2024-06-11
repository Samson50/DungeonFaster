from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager


class MenuManager(ScreenManager):

    def __init__(self):
        super().__init__()

        self.mainMenuScreen: Screen = MainMenuScreen(self)
        self.last_screen: Screen = self.mainMenuScreen.name

        self.newCampaignScreen: Screen = None
        self.loadCampaignScreen: Screen = None
        self.runCampaignScreen: Screen = None

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
