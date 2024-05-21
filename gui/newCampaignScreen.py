import os
import re

from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from gui.menuManager import MenuManager
from gui.utilities import FileDialog, LabeledIntInput

from model.map import Map
from model.campaign import Campaign


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager
        self.fileChooser = None
        self.map: Map = None
        self.campaign: Campaign = Campaign()

        saveDialog = FileDialog(
            select_text="Save",
            popup_title="Save Campaign",
            on_select=self.onSaveCampaign,
            path="/home/minalan/repos/DungeonFaster/campaigns",
        )
        self.saveDialog = saveDialog

        loadDialog = FileDialog(
            select_text="Load",
            popup_title="Load Campaign",
            on_select=self.onLoadCampaign,
            path="/home/minalan/repos/DungeonFaster/campaigns",
        )
        self.loadDialog = loadDialog

        save_button = Button(
            text="Save",
            pos_hint={"center_x": 0.9, "center_y": 0.9},
            size_hint=(0.15, 0.05),
        )
        save_button.bind(on_release=saveDialog.openDialog)
        self.add_widget(save_button)
        load_button = Button(
            text="Load",
            pos_hint={"center_x": 0.9, "center_y": 0.85},
            size_hint=(0.15, 0.05),
        )
        load_button.bind(on_release=loadDialog.openDialog)
        self.add_widget(load_button)

        layout = BoxLayout(orientation="vertical")

        layout.add_widget(
            Label(
                font_size=20,
                text="New Campaign",
                size_hint=(1, 0.2),
            )
        )

        editor_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.8))
        layout.add_widget(editor_layout)

        self.controls_layout = ControllerLayout(self)
        editor_layout.add_widget(self.controls_layout)

        self.map_layout = BoxLayout(orientation="vertical", size_hint=(0.7, 1))
        getMapButton = Button(text="Select Overworld Map")
        getMapButton.bind(on_release=self.selectOverworldMapDialog)
        self.map_layout.add_widget(getMapButton)
        editor_layout.add_widget(self.map_layout)

        self.add_widget(layout)
        self.menuManager.add_widget(self)

    def onSaveCampaign(self, instance):
        saveFile = self.saveDialog.textInput.text
        # TODO: try...
        self.campaign.save(saveFile)

        self.saveDialog.closeDialog(None)

    def onLoadCampaign(self, instance):
        loadFile = self.loadDialog.textInput.text
        # TODO: try...
        print(loadFile)
        self.loadDialog.closeDialog(None)
        try:
            self.campaign.load(loadFile)
            self.map = self.campaign.overworld
        except Exception as e:
            print(e)
            return

        # Clear widgets from map_layout
        self.map_layout.clear_widgets()

        # self.map.getZoomForSurface(self.map_layout)
        self.map.drawSparse(self.map_layout)

    def selectOverworldMapDialog(self, instance):
        self.overworldMapDialog = FileDialog(
            popup_title="Select Overworld Map",
            on_select=self.saveOverworldMap,
            path="/home/minalan/repos/DungeonFaster/example/chult",
        )

        self.overworldMapDialog.openDialog(None)

    def saveOverworldMap(self, instance):
        # Set overworld map file
        self.overworldMapFile = self.overworldMapDialog.textInput.text

        # Clear widgets from map_layout
        self.map_layout.clear_widgets()

        self.overworldMapDialog.closeDialog(None)

        self.map = Map(self.overworldMapFile)
        self.campaign.overworld = self.map

        self.map.getZoomForSurface(self.map_layout)
        self.map.drawSparse(self.map_layout)


class ControllerLayout(BoxLayout):

    def __init__(self, screen: NewCampaignScreen, **kwargs):
        super().__init__(orientation="vertical", size_hint=(0.3, 1), **kwargs)

        self.screen = screen

        self.add_rocker_controller("Map Zoom", self.zoomIn, self.zoomOut)
        self.add_rocker_controller("Scroll X", self.mapLeft, self.mapRight)
        self.add_rocker_controller("Scroll Y", self.mapDown, self.mapUp)

        self.density_controller = LabeledIntInput(
            "Box Size", self.setDensity, 0.5, 100, size_hint=(1, 0.08)
        )
        self.add_widget(self.density_controller)
        self.xOffsetController = LabeledIntInput(
            "X Offset", self.setXOffset, 1, 0, size_hint=(1, 0.08)
        )
        self.add_widget(self.xOffsetController)
        self.yOffsetController = LabeledIntInput(
            "Y Offset", self.setYOffset, 1, 0, size_hint=(1, 0.08)
        )
        self.add_widget(self.yOffsetController)

        self.xMarginController = LabeledIntInput(
            "X Margin", self.setXMargin, 1, 1, size_hint=(1, 0.08)
        )
        self.add_widget(self.xMarginController)
        self.yMarginController = LabeledIntInput(
            "Y Margin", self.setYMargin, 1, 1, size_hint=(1, 0.08)
        )
        self.add_widget(self.yMarginController)

        # hex-or-square: Switch
        hex_switch_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        hex_switch_layout.add_widget(Label(text="Hex Grid"))
        hex_switch_layout.add_widget(Switch())
        self.add_widget(hex_switch_layout)

        # Has hidden info: Switch
        hidden_switch_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        hidden_switch_layout.add_widget(Label(text="Has hidden areas"))
        hidden_switch_layout.add_widget(Switch())
        self.add_widget(hidden_switch_layout)

        # Empty layout for spacing
        self.add_widget(BoxLayout(size_hint=(1, 0.4)))

    def add_rocker_controller(self, name, on_plus, on_minus):
        rocker_box = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        rocker_box.add_widget(Label(text=name))
        plus_button = Button(text="+", size_hint=(0.3, 1))
        plus_button.bind(on_release=on_plus)
        rocker_box.add_widget(plus_button)
        minus_button = Button(text="-", size_hint=(0.3, 1))
        minus_button.bind(on_release=on_minus)
        rocker_box.add_widget(minus_button)

        self.add_widget(rocker_box)

    def zoomIn(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.zoom -= 1
        self.screen.map.drawSparse(self.screen.map_layout)

    def zoomOut(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.zoom += 1
        self.screen.map.drawSparse(self.screen.map_layout)

    def mapLeft(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.map_x_offset += 5
        self.screen.map.drawSparse(self.screen.map_layout)

    def mapRight(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.map_x_offset -= 5
        self.screen.map.drawSparse(self.screen.map_layout)

    def mapUp(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.map_y_offset -= 5
        self.screen.map.drawSparse(self.screen.map_layout)

    def mapDown(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.map_y_offset += 5
        self.screen.map.drawSparse(self.screen.map_layout)

    def setXOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid_x_offset = value
        self.screen.map.drawSparse(self.screen.map_layout)

    def setYOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid_y_offset = value
        self.screen.map.drawSparse(self.screen.map_layout)

    def setXMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.x_margin = value
        self.screen.map.update_grid()
        self.screen.map.drawSparse(self.screen.map_layout)

    def setYMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.y_margin = value
        self.screen.map.update_grid()
        self.screen.map.drawSparse(self.screen.map_layout)

    def setDensity(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.pixel_density = value
        self.screen.map.update_grid()
        self.screen.map.drawSparse(self.screen.map_layout)
