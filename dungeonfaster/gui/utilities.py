import re
import os

from kivy.uix.accordion import AccordionItem
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from dungeonfaster.model.player import Player


class IconButton(Button):
    def __init__(self, source, **kwargs):
        super().__init__(**kwargs)

        self.image = Image(
            source=source,
            size=(self.size[0] * 0.8, self.size[1] * 0.8),
            pos=(self.x + self.width * 0.1, self.y + self.height * 0.1),
        )

        self.add_widget(self.image)

    def on_size(self, instance, value):
        self.image.size = (self.size[0] * 0.8, self.size[1] * 0.8)

        self.image.x = self.x + self.width * 0.1
        self.image.y = self.y + self.height * 0.1


class EditableListEntry(BoxLayout):
    def __init__(self, name: str, thing, edit_cb, delete_cb, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.thing = thing

        width_hint = 0.25
        label_width = 0.5
        if not edit_cb:
            label_width = width_hint + label_width

        self.label = Label(text=name, size_hint=(label_width, 1))
        self.add_widget(self.label)

        if edit_cb:
            self.edit_button = Button(text="edit", size_hint=(width_hint, 1))
            self.edit_button.bind(on_release=edit_cb)
            self.add_widget(self.edit_button)

        self.delete_button = Button(text="delete", size_hint=(width_hint, 1))
        if delete_cb:
            self.delete_button.bind(on_release=delete_cb)
        else:
            self.delete_button.bind(on_release=self.delete)
        self.add_widget(self.delete_button)

    def delete(self, instance):
        parent: BoxLayout = self.parent
        parent.remove_widget(self)


class CollapseItem(AccordionItem):
    def __init__(self, add_title: str, add_cb, **kwargs):
        super().__init__(**kwargs)
        self.add_cb = add_cb

        self.scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))

        self.list_layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 2),
        )
        self.initial_children = 5

        # Add item button
        self.new_item_button = Button(text=add_title)
        self.new_item_button.bind(on_release=self._add_cb)
        self.list_layout.add_widget(self.new_item_button)

        # Add placeholder items
        for x in range(self.initial_children - 1):
            self.list_layout.add_widget(Label(text=f"[...]"))

        self.scroll_view.add_widget(self.list_layout)

        self.add_widget(self.scroll_view)

    def _add_cb(self, instance):
        children = self.list_layout.children
        n_children = len(children)

        # Do we still have placeholders?
        replace_index = None
        if n_children == self.initial_children:
            for child in children:
                if child.__class__.__name__ == "Label":
                    replace_index = children.index(child)

        new_thing = self.add_cb(instance)

        if replace_index:
            self.list_layout.remove_widget(children[replace_index])
            self.list_layout.add_widget(new_thing, replace_index)
        else:
            self.list_layout.add_widget(new_thing)

        self.list_layout.size_hint = (1, 0.5 * n_children)

    def addEntry(self, entry: EditableListEntry):
        children = self.list_layout.children
        n_children = len(children)

        # Do we still have placeholders?
        replace_index = None
        for child in children:
            if child.__class__.__name__ == "Label":
                replace_index = children.index(child)

        if not replace_index:
            replace_index = n_children
        else:
            self.list_layout.remove_widget(children[replace_index])

        self.list_layout.add_widget(entry, replace_index)

    def removeEntry(self, entry: EditableListEntry):
        self.list_layout.remove_widget(entry)

        n_children = len(self.list_layout.children)
        if n_children < self.initial_children:
            self.list_layout.add_widget(Label(text="[...]"))

        self.list_layout.size_hint = (1, 0.5 * n_children)

    def clearList(self):
        for child in self.list_layout.children:
            if isinstance(child, EditableListEntry):
                self.removeEntry(child)


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


class LabeledTextInput(BoxLayout):
    def __init__(self, text: str, on_text, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.input_text = TextInput(size_hint=(0.7, 1))
        self.input_text.bind(text=on_text)
        self.input_label = Label(text=text, size_hint=(0.3, 1))
        self.add_widget(self.input_label)
        self.add_widget(self.input_text)


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


class SimpleDialog(BoxLayout):
    def __init__(
        self,
        popup_title="Something",
        select_text="Select",
        **kwargs,
    ):
        super().__init__(orientation="vertical", **kwargs)

        self._popup: Popup = None
        self.popup_title = popup_title

        self.content_layout = BoxLayout(orientation="vertical")

        self.buttonsLayout = BoxLayout(
            orientation="horizontal", height=30, size_hint_y=None
        )
        self.cancelButton = Button(text="Cancel")
        self.cancelButton.bind(on_release=self.closeDialog)
        self.selectButton = Button(text=select_text)
        self.buttonsLayout.add_widget(self.cancelButton)
        self.buttonsLayout.add_widget(self.selectButton)

        self.add_widget(self.content_layout)
        self.add_widget(self.buttonsLayout)

    def openDialog(self, ignored):
        if self._popup is None:
            self._popup = Popup(
                title=self.popup_title, content=self, size_hint=(0.9, 0.9)
            )

        self._popup.open()

    def closeDialog(self, ignored):
        self._popup.dismiss()


class NewPlayerDialog(SimpleDialog):
    player_name: str
    player_class: str
    player_race: str
    player_level: int = 1
    def __init__(self, on_select, **kwargs):
        super().__init__(
            popup_title="New Player",
            select_text="Add Player",
            **kwargs,
        )

        self.selectButton.bind(on_release=on_select)

        self.name_input = LabeledTextInput("Name: ", self.on_name)
        # TODO: Dropdown
        self.class_input = LabeledTextInput("Class: ", self.on_class)
        self.race_input = LabeledTextInput("Race: ", self.on_race)
        self.level_input = LabeledIntInput("Level", self.on_level, 1, 1)

        self.content_layout.add_widget(self.name_input)
        self.content_layout.add_widget(self.class_input)
        self.content_layout.add_widget(self.race_input)
        self.content_layout.add_widget(self.level_input)

    def on_name(self, instance, value):
        self.player_name = value

    def on_class(self, instance, value):
        self.player_class = value

    def on_race(self, instance, value):
        self.player_race = value

    def on_level(self, value: int):
        self.player_level = value

    def get_player(self) -> Player:
        return Player(name=self.player_name, cls=self.player_class, level=self.player_level, race=self.player_race)


class FileDialog(SimpleDialog):

    def __init__(
        self,
        select_text="Select",
        popup_title="Select File",
        on_select=None,
        path=os.path.expanduser("~"),
        **kwargs,
    ):
        super().__init__(
            popup_title=popup_title,
            select_text=select_text,
            **kwargs,
        )

        fileChooser = FileChooserListView(path=path)
        fileChooser.bind(selection=self.set_text)
        textInput = TextInput(size_hint_y=None, height=30)
        self.textInput = textInput

        if on_select:
            self.selectButton.bind(on_release=on_select)
        else:
            self.selectButton.bind(on_release=self.closeDialog)

        self.content_layout.add_widget(fileChooser)
        self.content_layout.add_widget(textInput)

    def set_text(self, obj, val):
        self.textInput.text = val[0]
