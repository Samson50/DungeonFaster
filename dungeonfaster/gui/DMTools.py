from collections.abc import Callable

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.layout import Layout
from kivy.uix.scrollview import ScrollView


class ToolBox(BoxLayout):
    def __init__(self, name: str, focus: Callable, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.name = name
        self.expanded = False
        self.initial_size = self.size

        self.button = Button(text=name)
        self.button.bind(on_press=focus)
        self.add_widget(self.button)

        self.sub_layout = BoxLayout(orientation="vertical")

        # for i in range(3):
        #     self.sub_layout.add_widget(Button(text=f"button{i}"))

    def num_display(self):
        return len(self.sub_layout.children)

    def expand(self):
        if self.expanded:
            self.remove_widget(self.sub_layout)
            self.expanded = False
            self.size_hint[1] = 1
        else:
            self.add_widget(self.sub_layout)
            self.expanded = True
            self.sub_layout.size_hint[1] = self.num_display()
            self.size_hint[1] = self.num_display() + 1


class DMTools(BoxLayout):
    def __init__(self, view: Layout, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.expanded = False
        self.view = view
        self.selected: ToolBox = None
        self.tools_button = Button(text="DM Tools", size_hint=(1, 1))
        self.tools_button.bind(on_press=self._expand)
        self.add_widget(self.tools_button)

        self.initial_size_hint = kwargs["size_hint"]

        self.scroll_view = ScrollView(do_scroll_x=False)

        self.controls_layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
        )

        self._add_players_box()
        self.controls_layout.add_widget(ToolBox("NPCs", self._box_on_click))
        self.controls_layout.add_widget(ToolBox("Locations", self._box_on_click))
        self.controls_layout.add_widget(ToolBox("Encounters", self._box_on_click))

        self.scroll_view.add_widget(self.controls_layout)

    def _add_players_box(self):
        self.players_box = ToolBox("Players", self._box_on_click)
        self.controls_layout.add_widget(self.players_box)

    def _num_display(self):
        num_display = len(self.controls_layout.children)
        if self.selected:
            num_display += self.selected.num_display()

        return num_display

    def _expand(self, instance: Button):
        if self.expanded:
            self.expanded = False
            self.remove_widget(self.scroll_view)
            self.size_hint[1] = self.initial_size_hint[1]

        else:
            self.expanded = True
            self.add_widget(self.scroll_view)
            self.size_hint[1] = self.initial_size_hint[1] * (self._num_display() + 1)

        self.scroll_view.size_hint[1] = self._num_display()

    def _box_on_click(self, instance: Button):
        tool_box: ToolBox = instance.parent

        if self.selected:
            self.selected.expand()
            if self.selected == tool_box:
                self.selected = None
                self.size_hint[1] = self.initial_size_hint[1] * (self._num_display() + 1)
                self.scroll_view.size_hint[1] = self._num_display()
                return

        self.selected = tool_box
        self.selected.expand()

        self.size_hint[1] = self.initial_size_hint[1] * (self._num_display() + 1)
        self.scroll_view.size_hint[1] = self._num_display()
