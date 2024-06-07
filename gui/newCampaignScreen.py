import os

from kivy.graphics import Rectangle, Color
from kivy.input.motionevent import MotionEvent
from kivy.uix.accordion import Accordion
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch

from gui.menuManager import MenuManager
from gui.campaignView import CampaignView
from gui.utilities import FileDialog, LabeledIntInput, EditableListEntry, CollapseItem

from model.location import Location
from model.map import Map
from model.campaign import Campaign


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")
        # TODO: Add campaign_name text input box

        self.menuManager = manager
        self.fileChooser = None

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
        self.campaign_view = CampaignView(self, size_hint=(0.7, 1))
        self.campaign_view.bind(on_touch_down=self.campaign_view.on_click)
        editor_layout.add_widget(self.campaign_view)

        # Map controls layout
        self.controls_layout = ControllerLayout(self)
        editor_layout.add_widget(self.controls_layout)

        self.add_widget(layout)
        self.menuManager.add_widget(self)

        self.location_back_button = Button(
            text="Back",
            top=self.campaign_view.top,
            x=self.campaign_view.x,
            size_hint=(0.2, 0.1),
        )
        self.location_back_button.bind(on_release=self.location_back_cb)

    def location_back_cb(self, instance):
        current_location = self.campaign_view.leave()

        if current_location.parent is None:
            self.remove_widget(self.location_back_button)

        self.toLocation(current_location)

    def onSaveCampaign(self, instance):
        saveFile = self.saveDialog.textInput.text
        self.campaign_view.save(saveFile)

        self.saveDialog.closeDialog(None)

    def onLoadCampaign(self, instance):
        loadFile = self.loadDialog.textInput.text
        self.loadDialog.closeDialog(None)
        try:
            self.campaign_view.load(loadFile)
        except Exception as e:
            print(e)
            return

        # If location.parent, add back button
        if self.campaign_view.campaign.current_location.parent is not None:
            self.addBackButton()

        # Update controllers with values loaded from campaign
        self.controls_layout.update_from_map(self.campaign_view.map)

        # Make sure we show hidden tiles if necessary
        if self.campaign_view.map.hidden_tiles:
            self.controls_layout.hidden_switch.active = True
        else:
            # Activating switch will re-draw map otherwise
            self.campaign_view.map.draw()

        # Add any loaded locations to self.controls_layout.locations_list
        # TODO: Change from overworld to root location then call toLocation on campaign root
        for (
            location_index
        ) in self.campaign_view.campaign.current_location.locations.keys():
            self.controls_layout.addLocationEntry(
                self.campaign_view.campaign.current_location.locations[location_index]
            )

    def addBackButton(self):
        # Add back button to go back to higher location
        if self.location_back_button not in self.children:
            self.add_widget(self.location_back_button)

    def toLocation(self, location: Location):
        # TODO: Set music and item collapse view items

        # Add back button to go back to higher location
        if location.parent is not None:
            self.addBackButton()

        # Update switches
        self.controls_layout.hidden_switch.active = self.campaign_view.map.hidden_tiles

        # Replace sub-locations with entries from new location
        self.controls_layout.set_locations(location.locations)

    def edit_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        self.toLocation(parent.thing)
        self.campaign_view.arrive(parent.thing)

    def delete_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing

        # Remove location from which ever location contains it
        if location.parent:
            location.parent.map.points_of_interest.remove(location.index)
            del location.parent.locations[location.index]

        self.controls_layout.locations_list.removeEntry(parent)


class ControllerLayout(BoxLayout):

    def __init__(self, screen: NewCampaignScreen, **kwargs):
        super().__init__(orientation="vertical", size_hint=(0.3, 1), **kwargs)

        self.bg_color = Color(0.0, 0.0, 0.0)
        self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.canvas.add(self.bg_color)
        self.canvas.add(self.bg_rect)

        self.screen = screen

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
        self.hidden_switch_layout = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.08)
        )
        self.hidden_switch_layout.add_widget(Label(text="Has hidden areas"))
        self.hidden_switch = Switch(active=False)
        self.hidden_switch.bind(active=self.hidden_cb)
        self.hidden_switch_layout.add_widget(self.hidden_switch)
        self.add_widget(self.hidden_switch_layout)

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

    def set_locations(self, locations: dict[tuple[int, int], Location]):
        self.locations_list.clearList()
        for index in locations.keys():
            self.addLocationEntry(locations[index])

    def addLocationEntry(self, location: Location):
        new_location_entry = EditableListEntry(
            f"{location.index}\n{os.path.basename(location.map.map_file)}",
            location,
            self.screen.edit_location_cb,
            self.screen.delete_location_cb,
        )

        self.locations_list.addEntry(new_location_entry)

    def add_location_cb(self, instance):
        # Set campaign_view click to selecting tile for location
        self.screen.campaign_view.unbind(
            on_touch_down=self.screen.campaign_view.on_click
        )
        self.screen.campaign_view.bind(on_touch_down=self.select_location_tile)

        # Return temporary instructive placeholder for new location entry
        return Label(text="Selecting tile...")

    def select_location_tile(self, layout: BoxLayout, event: MotionEvent):
        (mouse_x, mouse_y) = event.pos
        (map_x, map_y) = self.screen.campaign_view.pos
        (map_width, map_height) = self.screen.campaign_view.size

        # Ensure touch is on the map, ignore otherwise
        if map_x < mouse_x < map_x + map_width and map_y < mouse_y < map_y + map_height:
            (x, y) = self.screen.campaign_view.map.grid.pixel_to_index(
                mouse_x - map_x, mouse_y - map_y
            )
            self.new_x = x
            self.new_y = y

            self.screen.campaign_view.unbind(on_touch_down=self.select_location_tile)
            self.screen.campaign_view.bind(
                on_touch_down=self.screen.campaign_view.on_click
            )

            # File selection dialog
            self.fileSelectDialog = FileDialog(
                select_text="Select",
                popup_title="Select New Location Map",
                on_select=self.onNewLocationMapSelection,
                path=os.path.expanduser("~"),
            )
            self.fileSelectDialog.openDialog(None)

    def onNewLocationMapSelection(self, instance: Button):
        locationMapFile = self.fileSelectDialog.textInput.text
        self.fileSelectDialog.closeDialog(None)

        # Create new location instance
        new_location = Location("todo", self.new_x, self.new_y)
        new_location.set_map(locationMapFile)
        new_location.parent = self.screen.campaign_view.campaign.current_location

        self.screen.campaign_view.add_location(new_location, self.new_x, self.new_y)

        self.screen.toLocation(new_location)
        self.screen.campaign_view.arrive(new_location)

        # Replace "Selecting location..." label with CollapseEntry instance for the new location
        self.addLocationEntry(new_location)

    def onNewMusicSelection(self, instance: Button):
        dialog: FileDialog = instance.parent.parent
        musicFile = dialog.textInput.text
        dialog.closeDialog(None)
        new_music_entry = EditableListEntry(
            f"{musicFile}",
            None,
            self.screen.edit_location_cb,
            None,
        )

        self.music_list.addEntry(new_music_entry)

    def add_music_cb(self, instance):
        # File selection dialog
        fileSelectDialog = FileDialog(
            select_text="Select",
            popup_title="Select New Location Map",
            on_select=self.onNewMusicSelection,
            path=os.path.expanduser("~"),
        )
        fileSelectDialog.openDialog(None)

        return Label(text="Selecting music...")

    def on_size(self, instance, value):
        # Re-draw black background
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def allOn(self, instance):
        for i in range(len(self.screen.campaign_view.map.grid.matrix)):
            for j in range(len(self.screen.campaign_view.map.grid.matrix[i])):
                if self.screen.campaign_view.map.grid.matrix[i][j] == 0:
                    self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

    def allOff(self, instance):
        for i in range(len(self.screen.campaign_view.map.grid.matrix)):
            for j in range(len(self.screen.campaign_view.map.grid.matrix[i])):
                if self.screen.campaign_view.map.grid.matrix[i][j] == 1:
                    self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

    def invertTiles(self, instance):
        for i in range(len(self.screen.campaign_view.map.grid.matrix)):
            for j in range(len(self.screen.campaign_view.map.grid.matrix[i])):
                self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

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
        if not self.screen.campaign_view.map:
            return

        if state:
            self.screen.campaign_view.map.toHex()
        else:
            self.screen.campaign_view.map.toSquare()

        self.screen.campaign_view.map.draw()

    def hidden_cb(self, instance: Switch, state: bool):
        if self.screen.campaign_view.map:
            self.screen.campaign_view.map.hidden_tiles = state
        else:
            return

        if state:
            # Add show tile buttons
            index = self.children.index(self.hidden_switch_layout)
            self.add_widget(self.hide_buttons_layout, index)
        else:
            # Remove / hide tile buttons
            self.remove_widget(self.hide_buttons_layout)

        self.screen.campaign_view.map.draw()

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

    def setXOffset(self, value: float):
        if self.screen.campaign_view.map is None:
            print("What?")
            return
        self.screen.campaign_view.map.grid.x_offset = value
        self.screen.campaign_view.map.draw()

    def setYOffset(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.y_offset = value
        self.screen.campaign_view.map.draw()

    def setXMargin(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.x_margin = value
        self.screen.campaign_view.map.update()
        self.screen.campaign_view.map.draw()

    def setYMargin(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.y_margin = value
        self.screen.campaign_view.map.update()
        self.screen.campaign_view.map.draw()

    def setDensity(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.pixel_density = value
        self.screen.campaign_view.map.update()
        self.screen.campaign_view.map.draw()
