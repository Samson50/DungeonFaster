import os

from kivy.graphics import Rectangle, Color
from kivy.input.motionevent import MotionEvent
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch

from gui.menuManager import MenuManager
from gui.utilities import FileDialog, LabeledIntInput

from model.location import Location
from model.map import Map
from model.campaign import Campaign

DELTA_X_SHIFT = 15
DELTA_Y_SHIFT = 15


class CollapseItem(AccordionItem):
    def __init__(self, add_title: str, add_cb, **kwargs):
        super().__init__(**kwargs)
        self.add_cb = add_cb

        self.scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))

        self.list_layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 2),
        )

        # Add item button
        self.new_item_button = Button(text=add_title)
        self.new_item_button.bind(on_release=self._add_cb)
        self.list_layout.add_widget(self.new_item_button)

        # Add placeholder items
        for x in range(4):
            self.list_layout.add_widget(Label(text=f"Placeholder {x}"))

        self.scroll_view.add_widget(self.list_layout)

        self.add_widget(self.scroll_view)

    # TODO: Resizes on scroll, but we need to resize on item addition
    def _add_cb(self, instance):
        children = self.list_layout.children
        n_children = len(children)

        # Do we still have placeholders?
        replace_index = None
        if n_children == 5:
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
        self.delete_button.bind(on_release=delete_cb)
        self.add_widget(self.delete_button)


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")
        # TODO: Add campaign_name text input box

        self.menuManager = manager
        self.fileChooser = None
        self.map: Map = None
        self.campaign: Campaign = Campaign()
        self.current_location: Location = None
        self.location_back_button: Button = None

        layout = BoxLayout(orientation="vertical")

        # Header layout items
        saveDialog = FileDialog(
            select_text="Save",
            popup_title="Save Campaign",
            on_select=self.onSaveCampaign,
            path="campaigns",
        )
        self.saveDialog = saveDialog

        loadDialog = FileDialog(
            select_text="Load",
            popup_title="Load Campaign",
            on_select=self.onLoadCampaign,
            path="campaigns",
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

        layout.add_widget(
            Label(
                font_size=20,
                text="New Campaign",
                size_hint=(1, 0.2),
            )
        )

        # Main layout
        editor_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.8))
        layout.add_widget(editor_layout)

        # Map layout
        self.map_layout = BoxLayout(orientation="vertical", size_hint=(0.7, 1))
        getMapButton = Button(text="Select Overworld Map")
        getMapButton.bind(on_release=self.selectOverworldMapDialog)
        self.map_layout.add_widget(getMapButton)
        editor_layout.add_widget(self.map_layout)

        # Map controls layout
        self.controls_layout = ControllerLayout(self)
        editor_layout.add_widget(self.controls_layout)

        self.add_widget(layout)
        self.menuManager.add_widget(self)

    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.map.draw()

    def changeMap(self, map: Map):
        self.map = map

        self.map_layout.canvas.clear()
        self.map.drawn_tiles = []
        self.map.map_rect = None
        self.map.getZoomForSurface(self.map_layout)
        self.map.draw()
        # TODO: Set controller layout values from map

    def location_back_cb(self, instance):
        location = self.current_location

        self.current_location = location.parent
        if location.parent is None:
            # Back to overworld
            self.changeMap(self.campaign.overworld)

            # Remove back button
            self.remove_widget(self.location_back_button)

            # TODO: Set music and items list items
        else:
            self.toLocation(location.parent)

    def onSaveCampaign(self, instance):
        saveFile = self.saveDialog.textInput.text
        self.campaign.save(saveFile)

        self.saveDialog.closeDialog(None)

    def onLoadCampaign(self, instance):
        loadFile = self.loadDialog.textInput.text
        self.loadDialog.closeDialog(None)
        try:
            self.campaign.load(loadFile, self.map_layout)
            self.map = self.campaign.overworld
        except Exception as e:
            print(e)
            return

        # Update controllers with values loaded from campaign
        self.controls_layout.update_from_map(self.map)

        # Prepare to display map
        self.map_layout.clear_widgets()

        # Make sure we show hidden tiles if necessary
        if self.map.hidden_tiles:
            self.controls_layout.hidden_switch.active = True
        else:
            # Activating switch will re-draw map otherwise
            self.map.draw()

        # Add any loaded locations to self.controls_layout.locations_list
        for location_index in self.campaign.locations.keys():
            self.addLocationEntry(self.campaign.locations[location_index])

    def addLocationEntry(self, location: Location):
        new_location_entry = EditableListEntry(
            f"{location.index}\n{os.path.basename(location.map.map_file)}",
            location,
            self.edit_location_cb,
            self.delete_location_cb,
        )

        children = self.controls_layout.locations_list.list_layout.children
        n_children = len(children)

        # Do we still have placeholders?
        replace_index = None
        for child in children:
            if child.__class__.__name__ == "Label":
                replace_index = children.index(child)

        if not replace_index:
            replace_index = n_children
        else:
            self.controls_layout.locations_list.list_layout.remove_widget(
                children[replace_index]
            )

        self.controls_layout.locations_list.list_layout.add_widget(
            new_location_entry, replace_index
        )

    def toLocation(self, location: Location):
        self.current_location = location

        # TODO: Set music and item collapse view items

        # Add back button to go back to higher location
        if self.location_back_button is None:
            self.location_back_button = Button(
                text="Back",
                top=self.map_layout.top,
                x=self.map_layout.x,
                size_hint=(0.2, 0.1),
            )
            self.location_back_button.bind(on_release=self.location_back_cb)
            self.add_widget(self.location_back_button)

        self.changeMap(location.map)

    def edit_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        self.toLocation(parent.thing)

    def delete_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing
        # TODO: Remove location from which ever location contains it
        index = self.controls_layout.locations_list.list_layout.children.index(parent)
        self.controls_layout.locations_list.list_layout.remove_widget(parent)
        self.controls_layout.locations_list.list_layout.add_widget(
            Label(text="Deleted..."), index
        )

    def dummy(self, ignored):
        print("asdf")

    def selectOverworldMapDialog(self, instance):
        self.overworldMapDialog = FileDialog(
            popup_title="Select Overworld Map",
            on_select=self.saveOverworldMap,
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
        self.map.draw()


class ControllerLayout(BoxLayout):

    def __init__(self, screen: NewCampaignScreen, **kwargs):
        super().__init__(orientation="vertical", size_hint=(0.3, 1), **kwargs)

        self.bg_color = Color(0.0, 0.0, 0.0)
        self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.canvas.add(self.bg_color)
        self.canvas.add(self.bg_rect)

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
        hex_switch = Switch()
        hex_switch.bind(active=self.hex_switch_cb)
        hex_switch_layout.add_widget(hex_switch)
        self.add_widget(hex_switch_layout)

        # Has hidden info: Switch
        hidden_switch_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        hidden_switch_layout.add_widget(Label(text="Has hidden areas"))
        self.hidden_switch = Switch(active=False)
        self.hidden_switch.bind(active=self.hidden_cb)
        hidden_switch_layout.add_widget(self.hidden_switch)
        self.add_widget(hidden_switch_layout)

        self.hide_buttons_layout = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.08)
        )
        all_on_button = Button(text="All On")
        all_on_button.bind(on_release=self.allOn)
        all_off_button = Button(text="All Off")
        all_off_button.bind(on_release=self.allOff)
        invert_button = Button(text="Invert Tiles")
        invert_button.bind(on_release=self.invertTiles)
        self.hide_buttons_layout.add_widget(all_on_button)
        self.hide_buttons_layout.add_widget(all_off_button)
        self.hide_buttons_layout.add_widget(invert_button)

        # TODO: Only activate once map is selected / loaded

        # Collapsible view for optional items: sub-locations, music, and combat music
        self.accordion = Accordion(orientation="vertical", size_hint=(1, 1))

        self.locations_list = CollapseItem(
            "Add Location", self.add_location_cb, title="Locations"
        )
        self.accordion.add_widget(self.locations_list)

        self.music_list = CollapseItem("Add Music", self.add_music_cb, title="Music")
        self.accordion.add_widget(self.music_list)

        self.combat_music_list = CollapseItem(
            "Add Combat Music", self.add_music_cb, title="Combat Music"
        )
        self.accordion.add_widget(self.combat_music_list)

        # TODO: Add items / other markers to map
        # self.items_list = ...

        self.add_widget(self.accordion)

    def add_location_cb(self, instance):
        # Set map_layout click to selecting tile for location
        self.screen.map_layout.unbind(on_touch_down=self.tile_flip_cb)
        self.screen.map_layout.bind(on_touch_down=self.select_location_tile)

        # Return temporary instructive placeholder for new location entry
        return Label(text="Selecting tile...")

    def select_location_tile(self, layout: BoxLayout, event: MotionEvent):
        (mouse_x, mouse_y) = event.pos
        (map_x, map_y) = self.screen.map_layout.pos
        (map_width, map_height) = self.screen.map_layout.size

        # Ensure touch is on the map, ignore otherwise
        if map_x < mouse_x < map_x + map_width and map_y < mouse_y < map_y + map_height:
            (x, y) = self.screen.map.grid.pixel_to_index(
                mouse_x - map_x, mouse_y - map_y
            )
            print(f"Adding new location for tile ({x}, {y})")
            self.new_x = x
            self.new_y = y

            self.screen.map_layout.unbind(on_touch_down=self.select_location_tile)
            self.screen.map_layout.bind(on_touch_down=self.tile_flip_cb)

            # File selection dialog
            self.fileSelectDialog = FileDialog(
                select_text="Select",
                popup_title="Select New Location Map",
                on_select=self.onNewLocationMapSelection,
                path=os.path.expanduser("~"),
            )
            self.fileSelectDialog.openDialog(None)

    def onNewLocationMapSelection(self, instance):
        locationMapFile = self.fileSelectDialog.textInput.text
        self.fileSelectDialog.closeDialog(None)

        print(f"Selected file {locationMapFile}")

        # Create new location instance
        new_location = Location("todo", self.new_x, self.new_y)
        new_location.set_map(locationMapFile)
        # TODO: set parent (if overworld?)

        # Add location to current location or campaign
        if self.screen.current_location is None:
            self.screen.campaign.locations[(self.new_x, self.new_y)] = new_location
        else:
            self.screen.current_location.locations[(self.new_x, self.new_y)] = (
                new_location
            )
        self.current_location = new_location

        self.screen.toLocation(new_location)

        # Replace "Selecting location..." label with CollapseEntry instance for the new location
        self.screen.addLocationEntry(new_location)

    def add_music_cb(self, instance):
        pass

    def on_size(self, instance, value):
        # Re-draw black background
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def allOn(self, instance):
        for i in range(len(self.screen.map.grid.matrix)):
            for j in range(len(self.screen.map.grid.matrix[i])):
                if self.screen.map.grid.matrix[i][j] == 0:
                    self.screen.map.grid.flip_tile(i, j)
        self.screen.map.draw()

    def allOff(self, instance):
        for i in range(len(self.screen.map.grid.matrix)):
            for j in range(len(self.screen.map.grid.matrix[i])):
                if self.screen.map.grid.matrix[i][j] == 1:
                    self.screen.map.grid.flip_tile(i, j)
        self.screen.map.draw()

    def invertTiles(self, instance):
        for i in range(len(self.screen.map.grid.matrix)):
            for j in range(len(self.screen.map.grid.matrix[i])):
                self.screen.map.grid.flip_tile(i, j)
        self.screen.map.draw()

    def update_from_map(self, map: Map):
        self.density_controller.input.text = str(map.grid.pixel_density)
        self.density_controller.value = map.grid.pixel_density
        self.xOffsetController.input.text = str(map.grid.x_offset)
        self.xOffsetController.value = map.grid.x_offset
        self.yOffsetController.input.text = str(map.grid.y_offset)
        self.yOffsetController.value = map.grid.y_offset
        self.xMarginController.input.text = str(map.grid.x_margin)
        self.xMarginController.value = map.grid.x_margin
        self.yMarginController.input.text = str(map.grid.y_margin)
        self.yMarginController.value = map.grid.y_margin

    def hex_switch_cb(self, instance: Switch, state: bool):
        if not self.screen.map:
            return

        if state:
            self.screen.map.toHex()
        else:
            self.screen.map.toSquare()

        self.screen.map.draw()

    def hidden_cb(self, instance: Switch, state: bool):
        if self.screen.map:
            self.screen.map.hidden_tiles = state
        else:
            return

        if state:
            # Add show tile buttons
            self.add_widget(self.hide_buttons_layout)
            # Register on_click listener for self.screen.map_layout
            self.screen.map_layout.bind(on_touch_down=self.tile_flip_cb)
        else:
            # Remove / hide tile buttons
            self.remove_widget(self.hide_buttons_layout)
            # Remove on_click listener
            self.screen.map_layout.unbind(on_touch_down=self.tile_flip_cb)

        self.screen.map.draw()

    def tile_flip_cb(self, layout: BoxLayout, event: MotionEvent):
        (mouse_x, mouse_y) = event.pos
        (map_x, map_y) = self.screen.map_layout.pos
        (map_width, map_height) = self.screen.map_layout.size

        # Ensure touch is on the map, ignore otherwise
        if map_x < mouse_x < map_x + map_width and map_y < mouse_y < map_y + map_height:
            try:
                self.screen.map.flip_at_coordinate(mouse_x - map_x, mouse_y - map_y)
                self.screen.map.draw()
            # TODO: Deliberate error message and catching index error
            except Exception as e:
                print(e)

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
        self.screen.map.window.zoom -= 1
        self.screen.map.update()
        self.screen.map.draw()

    def zoomOut(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.window.zoom += 1
        self.screen.map.update()
        self.screen.map.draw()

    def mapLeft(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.x += DELTA_X_SHIFT
        self.screen.map.draw()

    def mapRight(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.x -= DELTA_X_SHIFT
        self.screen.map.draw()

    def mapUp(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.y -= DELTA_Y_SHIFT
        self.screen.map.draw()

    def mapDown(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.y += DELTA_Y_SHIFT
        self.screen.map.draw()

    def setXOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.x_offset = value
        self.screen.map.draw()

    def setYOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.y_offset = value
        self.screen.map.draw()

    def setXMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.x_margin = value
        self.screen.map.update()
        self.screen.map.draw()

    def setYMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.y_margin = value
        self.screen.map.update()
        self.screen.map.draw()

    def setDensity(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.pixel_density = value
        self.screen.map.update()
        self.screen.map.draw()
