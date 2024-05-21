import re
import os

from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


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


class FileDialog(BoxLayout):

    def __init__(
        self,
        select_text="select",
        popup_title="Select File",
        on_select=None,
        path=os.path.expanduser("~"),
        **kwargs,
    ):
        super().__init__(orientation="vertical", **kwargs)

        self.popup_title = popup_title

        fileChooser = FileChooserListView(path=path)
        fileChooser.bind(selection=self.set_text)
        textInput = TextInput(size_hint_y=None, height=30)
        self.textInput = textInput

        buttonsLayout = BoxLayout(orientation="horizontal", height=30, size_hint_y=None)
        cancelButton = Button(text="cancel")
        cancelButton.bind(on_release=self.closeDialog)
        selectButton = Button(text=select_text)
        if on_select:
            selectButton.bind(on_release=on_select)
        else:
            selectButton.bind(on_release=self.closeDialog)
        buttonsLayout.add_widget(cancelButton)
        buttonsLayout.add_widget(selectButton)

        self.add_widget(fileChooser)
        self.add_widget(textInput)
        self.add_widget(buttonsLayout)

    def openDialog(self, ignored):
        self._popup = Popup(title=self.popup_title, content=self, size_hint=(0.9, 0.9))
        self._popup.open()

    def closeDialog(self, ignored):
        self._popup.dismiss()

    def set_text(self, obj, val):
        print(obj, val)
        self.textInput.text = val[0]
