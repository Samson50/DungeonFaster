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

from model.map import Map


class LabeledIntInput(BoxLayout):
    def __init__(self, name, callback, delta, default, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.value: float = default
        self.update_value = callback
        self.delta = delta

        self.text = Label(text=name, size_hint=(0.3, 1))
        self.add_widget(self.text)
        self.input = FloatInput(
            self, text=str(self.value), multiline=False, size_hint=(0.3, 1)
        )
        self.add_widget(self.input)
        dec_button = Button(text="<", size_hint=(0.2, 1))
        dec_button.bind(on_release=self.lower_value)
        self.add_widget(dec_button)
        inc_button = Button(text=">", size_hint=(0.2, 1))
        inc_button.bind(on_release=self.raise_value)
        self.add_widget(inc_button)

    def raise_value(self, instance):
        self.value += self.delta
        self.input.text = str(self.value)
        self.update_value(self.value)

    def lower_value(self, instance):
        self.value -= self.delta
        self.input.text = str(self.value)
        self.update_value(self.value)


class FloatInput(TextInput):
    # ^([0-9]+.?)?[0-9]*$
    # pat = re.compile("^([0-9]+.?)?[0-9]*$")

    def __init__(self, container: LabeledIntInput, **kwargs):
        super().__init__(**kwargs)

        self.container = container
        self.pat = re.compile("[^0-9]")

    def insert_text(self, substring, from_undo=False):
        if "." in self.text:
            s = re.sub(self.pat, "", substring)
        else:
            s = ".".join(re.sub(self.pat, "", s) for s in substring.split(".", 1))
        super().insert_text(s, from_undo=from_undo)

        self.container.value = float(self.text)
        self.container.update_value(self.container.value)

        return None


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager
        self.fileChooser = None
        self.map: Map = None

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

    def selectOverworldMapDialog(self, instance):
        selectLayout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        fileChooser = FileChooserListView(
            path="/home/minalan/repos/DungeonFaster/example/chult"
        )
        # fileChooser = FileChooserListView(path=os.path.expanduser("~"))
        self.fileChooser = fileChooser
        # fileChooser.bind(on_selection=self.selectOverworldMap)
        buttonsLayout = BoxLayout(orientation="horizontal", size_hint=(1, 0.2))
        selectLayout.add_widget(fileChooser)
        selectLayout.add_widget(buttonsLayout)

        selectButton = Button(text="Select", size_hint=(0.5, 1))
        selectButton.bind(on_release=self.saveOverworldMap)
        cancelButton = Button(text="Cancel", size_hint=(0.5, 1))
        cancelButton.bind(on_release=self.cancelPopup)
        buttonsLayout.add_widget(selectButton)
        buttonsLayout.add_widget(cancelButton)

        self._popup = Popup(
            title="Select Overworld Map", content=selectLayout, size_hint=(0.8, 0.8)
        )
        self._popup.open()

    # def selectOverworldMap(self, instance: FileChooserListView):
    #     self.overworldMapFile = instance.selection
    #     print(self.overworldMapFile)

    def saveOverworldMap(self, instance):
        # Set overworld map file
        if len(self.fileChooser.selection) == 1:
            self.overworldMapFile = self.fileChooser.selection[0]
            print(self.overworldMapFile)
        else:
            # TODO: Error?
            return

        # Clear widgets from map_layout
        self.map_layout.clear_widgets()

        self._popup.dismiss()

        self.map = Map(self.overworldMapFile)

        self.map.getZoomForSurface(self.map_layout)
        self.map.draw(self.map_layout)

    def cancelPopup(self, instance):
        self._popup.dismiss()


class ControllerLayout(BoxLayout):

    def __init__(self, screen: NewCampaignScreen, **kwargs):
        super().__init__(orientation="vertical", size_hint=(0.3, 1), **kwargs)

        self.screen = screen

        self.add_rocker_controller("Map Zoom", self.zoomIn, self.zoomOut)
        self.add_rocker_controller("Scroll X", self.dummy_button, self.dummy_button)
        self.add_rocker_controller("Scroll Y", self.dummy_button, self.dummy_button)

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

    def dummy_button(self, value):
        pass

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
        self.screen.map.draw(self.screen.map_layout)

    def zoomOut(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.zoom += 1
        self.screen.map.draw(self.screen.map_layout)

    def setXOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.x_offset = value
        self.screen.map.draw(self.screen.map_layout)

    def setYOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.y_offset = value
        self.screen.map.draw(self.screen.map_layout)

    def setXMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.x_margin = value
        self.screen.map.update_grid()
        self.screen.map.draw(self.screen.map_layout)

    def setYMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.y_margin = value
        self.screen.map.update_grid()
        self.screen.map.draw(self.screen.map_layout)

    def setDensity(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.pixel_density = value
        self.screen.map.update_grid()
        self.screen.map.draw(self.screen.map_layout)
