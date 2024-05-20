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
from kivy.uix.textinput import TextInput

from gui.menuManager import MenuManager


class FloatInput(TextInput):

    pat = re.compile("[^0-9]")

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if "." in self.text:
            s = re.sub(pat, "", substring)
        else:
            s = ".".join(re.sub(pat, "", s) for s in substring.split(".", 1))
        return super().insert_text(s, from_undo=from_undo)


class LabeledIntInput(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.value: float = 0.0

        self.text = Label(text="Test", size_hint=(0.3, 1))
        self.add_widget(self.text)
        self.input = FloatInput(
            text=str(self.value), multiline=False, size_hint=(0.3, 1)
        )
        self.add_widget(self.input)
        dec_button = Button(text="<", size_hint=(0.2, 1))
        # dec_button.bind(on_release=self.lower_value)
        self.add_widget(dec_button)
        inc_button = Button(text=">", size_hint=(0.2, 1))
        # inc_button.bind(on_release=self.raise_value)
        self.add_widget(inc_button)


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager
        self.fileChooser = None

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

        controls_layout = BoxLayout(orientation="vertical", size_hint=(0.3, 1))
        # offset: Label, TextInput, Button(<), Button(>)
        controls_layout.add_widget(LabeledIntInput(size_hint=(1, 0.1)))
        # box size: Label, TextInput, Button(<), Button(>)
        controls_layout.add_widget(LabeledIntInput(size_hint=(1, 0.1)))
        # hex-or-square: Switch
        editor_layout.add_widget(controls_layout)

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
        fileChooser = FileChooserListView(path=os.path.expanduser("~"))
        self.fileChooser = fileChooser
        fileChooser.bind(on_selection=self.selectOverworldMap)
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

    def selectOverworldMap(self, instance: FileChooserListView):
        self.overworldMapFile = instance.selection
        print(self.overworldMapFile)

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

        # Create image from overworld map file
        self.map_image = Image(
            source=self.overworldMapFile,
            width=self.map_layout.width,
            height=self.map_layout.height,
        )
        # Add image to map layout

        self.map_layout.add_widget(self.map_image)
        # TODO: Add zoom in/out buttons
        self._popup.dismiss()

    def cancelPopup(self, instance):
        self._popup.dismiss()
