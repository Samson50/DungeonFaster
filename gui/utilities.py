import re
import os

from kivy.uix.accordion import AccordionItem
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


class EditableListEntry(BoxLayout):
    def __init__(self, name: str, thing, edit_cb, delete_cb, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)

        self.thing = thing

        self.label = Label(text=name, size_hint=(0.5, 1))
        self.add_widget(self.label)
        self.edit_button = Button(text="edit", size_hint=(0.25, 1))
        self.edit_button.bind(on_release=edit_cb)
        self.add_widget(self.edit_button)
        self.delete_button = Button(text="delete", size_hint=(0.25, 1))
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

        self._popup = None
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
        if self._popup is None:
            self._popup = Popup(
                title=self.popup_title, content=self, size_hint=(0.9, 0.9)
            )

        self._popup.open()

    def closeDialog(self, ignored):
        self._popup.dismiss()

    def set_text(self, obj, val):
        self.textInput.text = val[0]
