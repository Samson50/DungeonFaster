from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

from dungeonfaster.gui.utilities import LabeledTextInput, SimpleDialog
from dungeonfaster.model.entity.npc import NPC


class NPCDialog(SimpleDialog):
    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)

        self.npc = NPC()

        self.selectButton.bind(on_release=on_select)

        self.content_layout.add_widget(LabeledTextInput("Name", self.on_name_select, height=30, size_hint_y=None))
        self.content_layout.add_widget(LabeledTextInput("Race", self.on_race_select, height=30, size_hint_y=None))
        self.content_layout.add_widget(BoxLayout())

    def on_name_select(self, instance: TextInput, value: str):
        self.npc.name = value

    def on_race_select(self, instance: TextInput, value: str):
        self.npc.race = value
