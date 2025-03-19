import os

from kivy.graphics import Rectangle, Color
from kivy.input.motionevent import MotionEvent
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from dungeonfaster.gui.menuManager import MenuManager
from dungeonfaster.gui.campaignView import CampaignView
from dungeonfaster.gui.utilities import (
    CollapseItem,
    EditableListEntry,
    FileDialog,
    LabeledIntInput,
    LabeledTextInput,
    NewPlayerDialog,
)

from dungeonfaster.model.location import Location
from dungeonfaster.model.map import Map
from dungeonfaster.model.player import Player

CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")


class NewCampaignScreen(Screen):
    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager
        self.fileChooser = None

        layout = BoxLayout(orientation="vertical")

        # Header layout items
        self.saveDialog = FileDialog(
            select_text="Save",
            popup_title="Save Campaign",
            on_select=self.onSaveCampaign,
            path=CAMPAIGNS_DIR,
        )

        self.loadDialog = FileDialog(
            select_text="Load",
            popup_title="Load Campaign",
            on_select=self.onLoadCampaign,
            path=CAMPAIGNS_DIR,
        )

        save_button = Button(
            text="Save",
            pos_hint={"center_x": 0.9, "center_y": 0.9},
            size_hint=(0.15, 0.05),
        )
        save_button.bind(on_release=self.saveDialog.open_dialog)
        self.add_widget(save_button)
        load_button = Button(
            text="Load",
            pos_hint={"center_x": 0.9, "center_y": 0.85},
            size_hint=(0.15, 0.05),
        )
        load_button.bind(on_release=self.loadDialog.open_dialog)
        self.add_widget(load_button)

        layout.add_widget(
            Label(
                font_size=20,
                text="New Campaign",
                size_hint=(1, 0.2),
            )
        )

        self.campaign_name = TextInput(size_hint=(0.3, 0.05), pos_hint={"center_x": 0.5, "center_y": 0.85})
        self.campaign_name.bind(text=self.on_text)
        self.add_widget(self.campaign_name)

        # Main layout
        editor_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.8))
        layout.add_widget(editor_layout)

        # Map layout
        self.campaign_view = CampaignView(self, size_hint=(0.7, 1))
        self.campaign_view.bind(on_touch_down=self.campaign_view.on_click)
        self.getMapButton = Button(text="Select Overworld Map")
        self.getMapButton.bind(on_release=self.selectOverworldMapDialog)
        self.campaign_view.add_widget(self.getMapButton)

        editor_layout.add_widget(self.campaign_view)

        # Map controls layout
        self.controls_layout = ControllerLayout(self)
        editor_layout.add_widget(self.controls_layout)

        self.add_widget(layout)
        self.menuManager.add_widget(self)

        self.location_back_button = Button(
            text="Back",
            pos_hint={"x": 0.025, "y": 0.7},
            top=self.campaign_view.top,
            x=self.campaign_view.x,
            size_hint=(0.1, 0.075),
        )
        self.location_back_button.bind(on_release=self.location_back_cb)

    def on_text(self, instance: TextInput, value: str) -> None:
        self.campaign_view.campaign.name = value

    def selectOverworldMapDialog(self, instance):
        self.overworldMapDialog = FileDialog(
            popup_title="Select Overworld Map",
            on_select=self.saveOverworldMap,
        )

        self.overworldMapDialog.open_dialog(None)

    def saveOverworldMap(self, instance):
        # Set overworld map file
        overworldMapFile = self.overworldMapDialog.textInput.text
        self.campaign_view.remove_widget(self.getMapButton)
        self.overworldMapDialog.close_dialog(None)
        # TODO: Move map file to campaigns/files

        base_location = Location("overworld", {})
        base_location.set_map(overworldMapFile)
        self.campaign_view.map = base_location.map

        self.campaign_view.add_location(base_location, "overworld")

        self.campaign_view.map.get_zoom_for_surface(self.campaign_view.map_layout)
        self.campaign_view.draw()

        self.campaign_view.set_sliders()

    def location_back_cb(self, instance):
        current_location = self.campaign_view.leave()

        if current_location.parent is None:
            self.remove_widget(self.location_back_button)

        self.toLocation(current_location)

    def onSaveCampaign(self, instance):
        saveFile = self.saveDialog.textInput.text
        self.campaign_view.save(saveFile)

        self.saveDialog.close_dialog(None)

    def onLoadCampaign(self, instance):
        loadFile = self.loadDialog.textInput.text
        self.loadDialog.close_dialog(None)
        try:
            self.campaign_view.load(loadFile)
        except Exception as e:
            print(e)
            return
        self.campaign_view.remove_widget(self.getMapButton)

        # If location.parent, add back button
        if self.campaign_view.campaign.current_location.parent is not None:
            self.addBackButton()

        # Update campaign name from loaded
        self.campaign_name.text = self.campaign_view.campaign.name

        # Update controllers with values loaded from campaign
        self.controls_layout.map_editor_layout.update_from_map(self.campaign_view.map)
        self.controls_layout.map_editor_layout.name_input.text = self.campaign_view.campaign.current_location.name

        # Make sure we show hidden tiles if necessary
        if self.campaign_view.map.hidden_tiles:
            self.controls_layout.map_editor_layout.hidden_switch.active = True
        else:
            # Activating switch will re-draw map otherwise
            self.campaign_view.map.draw()

        # Add any loaded locations to self.controls_layout.locations_list
        for location in self.campaign_view.campaign.locations.values():
            self.controls_layout.addLocationEntry(location)

        # Add musics for current location
        for music in self.campaign_view.campaign.current_location.music:
            self.controls_layout.addMusicEntry(music, self.controls_layout.music_list)
        for combat_music in self.campaign_view.campaign.current_location.combat_music:
            self.controls_layout.addMusicEntry(combat_music, self.controls_layout.combat_music_list)

    def addBackButton(self):
        # Add back button to go back to higher location
        if self.location_back_button not in self.children:
            self.add_widget(self.location_back_button)

    def toLocation(self, location: Location):
        self.campaign_view.campaign.current_location = location

        self.controls_layout.map_editor_layout.name_input.text = location.name

        # Add back button to go back to higher location
        if location.parent is not None:
            self.addBackButton()

        # Update switches
        self.controls_layout.map_editor_layout.hidden_switch.active = self.campaign_view.map.hidden_tiles

        # TODO: Set music and item collapse view items

    def edit_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing
        self.toLocation(location)
        self.campaign_view.arrive(location, (0, 0))

    def delete_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing

        # Remove location from which ever location contains it
        del self.campaign_view.locations[location.name]

        self.controls_layout.locations_list.remove_entry(parent)


class MapEditorLayout(BoxLayout):
    def __init__(self, screen: NewCampaignScreen, **kwargs):
        super().__init__(orientation="vertical", size_hint=(1, 1), **kwargs)
        self.screen = screen

        self.name_input = LabeledTextInput("Name: ", self.on_text, size_hint=(1, 0.08))
        self.add_widget(self.name_input)

        # TODO: Add map file entry and edit button to change current location map
        self.map_file_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        self.map_file_layout.add_widget(Label(text="Map File:", size_hint=(0.3, 1)))
        self.map_file_label = Label(text="None", size_hint=(0.5, 1))
        self.map_file_layout.add_widget(self.map_file_label)
        self.map_file_button = Button(text="edit", size_hint=(0.2, 1))
        self.map_file_layout.add_widget(self.map_file_button)
        self.add_widget(self.map_file_layout)

        self.density_controller = LabeledIntInput("Box Size", self.setDensity, 0.5, 100, size_hint=(1, 0.08))
        self.add_widget(self.density_controller)
        self.xOffsetController = LabeledIntInput("X Offset", self.setXOffset, 1, 0, size_hint=(1, 0.08))
        self.add_widget(self.xOffsetController)
        self.yOffsetController = LabeledIntInput("Y Offset", self.setYOffset, 1, 0, size_hint=(1, 0.08))
        self.add_widget(self.yOffsetController)

        self.xMarginController = LabeledIntInput("X Margin", self.setXMargin, 1, 1, size_hint=(1, 0.08))
        self.add_widget(self.xMarginController)
        self.yMarginController = LabeledIntInput("Y Margin", self.setYMargin, 1, 1, size_hint=(1, 0.08))
        self.add_widget(self.yMarginController)

        # hex-or-square: Switch
        hex_switch_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        hex_switch_layout.add_widget(Label(text="Hex Grid"))
        hex_switch = Switch()
        hex_switch.bind(active=self.hex_switch_cb)
        hex_switch_layout.add_widget(hex_switch)
        self.add_widget(hex_switch_layout)

        # Has hidden info: Switch
        self.hidden_switch_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        self.hidden_switch_layout.add_widget(Label(text="Has hidden areas"))
        self.hidden_switch = Switch(active=False)
        self.hidden_switch.bind(active=self.hidden_cb)
        self.hidden_switch_layout.add_widget(self.hidden_switch)
        self.add_widget(self.hidden_switch_layout)

        self.hide_buttons_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        all_on_button = Button(text="All On")
        all_on_button.bind(on_release=self.allOn)
        all_off_button = Button(text="All Off")
        all_off_button.bind(on_release=self.allOff)
        invert_button = Button(text="Invert Tiles")
        invert_button.bind(on_release=self.invertTiles)
        self.hide_buttons_layout.add_widget(all_on_button)
        self.hide_buttons_layout.add_widget(all_off_button)
        self.hide_buttons_layout.add_widget(invert_button)

    def on_text(self, instance: TextInput, value: str) -> None:
        self.screen.campaign_view.campaign.current_location.name = value

    def allOn(self, instance):
        for i in range(self.screen.campaign_view.map.grid.x):
            for j in range(self.screen.campaign_view.map.grid.y):
                if (i, j) not in self.screen.campaign_view.map.grid.matrix:
                    self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

    def allOff(self, instance):
        for tile in self.screen.campaign_view.map.grid.matrix:
            self.screen.campaign_view.map.grid.flip_tile(*tile)
        self.screen.campaign_view.map.draw()

    def invertTiles(self, instance):
        for i in range(self.screen.campaign_view.map.grid.x):
            for j in range(self.screen.campaign_view.map.grid.y):
                self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

    def update_from_map(self, map: Map):
        self.map_file_label.text = os.path.basename(map.map_file)
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
            self.screen.campaign_view.map.to_hex()
        else:
            self.screen.campaign_view.map.to_square()

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


class ControllerLayout(BoxLayout):
    def __init__(self, screen: NewCampaignScreen, **kwargs):
        super().__init__(orientation="vertical", size_hint=(0.3, 1), **kwargs)

        # TODO: Overarching input for campaign name

        self.bg_color = Color(0.0, 0.0, 0.0)
        self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.canvas.add(self.bg_color)
        self.canvas.add(self.bg_rect)

        self.screen = screen

        self.new_player_dialog = NewPlayerDialog(self.on_new_player_select)

        # TODO: Only activate once map is selected / loaded

        self.accordion = Accordion(orientation="vertical", size_hint=(1, 0.6))

        self.map_editor_layout = MapEditorLayout(self.screen)
        map_item = AccordionItem(title="Edit Map")
        map_item.add_widget(self.map_editor_layout)
        self.accordion.add_widget(map_item)

        # Locations
        self.locations_list = CollapseItem("Add Location", self.add_location_cb, title="Locations")
        self.accordion.add_widget(self.locations_list)

        # Players
        self.players_list = CollapseItem("Add Player", self.add_player_cb, title="Party")
        self.accordion.add_widget(self.players_list)

        # Music
        self.music_list = CollapseItem("Add Music", self.add_music_cb, title="Music")
        self.accordion.add_widget(self.music_list)

        self.combat_music_list = CollapseItem("Add Combat Music", self.add_combat_music_cb, title="Combat Music")
        self.accordion.add_widget(self.combat_music_list)

        self.accordion.select(map_item)

        # TODO: Add items / other markers to map
        # self.items_list = ...

        self.add_widget(self.accordion)

    def on_size(self, instance, value):
        # Re-draw black background
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def add_location_cb(self, instance: Button) -> Label:
        # Set campaign_view click to selecting tile for location
        self.screen.campaign_view.unbind(on_touch_down=self.screen.campaign_view.on_click)
        self.screen.campaign_view.bind(on_touch_down=self.select_location_tile)

        # Return temporary instructive placeholder for new location entry
        return Label(text="Selecting tile...")

    def select_location_tile(self, layout: BoxLayout, event: MotionEvent):
        (mouse_x, mouse_y) = event.pos
        (map_x, map_y) = self.screen.campaign_view.pos
        (map_width, map_height) = self.screen.campaign_view.size

        # Ensure touch is on the map, ignore otherwise
        if map_x < mouse_x < map_x + map_width and map_y < mouse_y < map_y + map_height:
            (x, y) = self.screen.campaign_view.map.grid.pixel_to_index(mouse_x - map_x, mouse_y - map_y)
            self.new_x = x
            self.new_y = y

            self.screen.campaign_view.unbind(on_touch_down=self.select_location_tile)
            self.screen.campaign_view.bind(on_touch_down=self.screen.campaign_view.on_click)

            # File selection dialog
            self.fileSelectDialog = FileDialog(
                select_text="Select",
                popup_title="Select New Location Map",
                on_select=self.onNewLocationMapSelection,
                path=os.path.expanduser("~"),
            )
            self.fileSelectDialog.open_dialog(None)

    def onNewLocationMapSelection(self, instance: Button):
        locationMapFile = self.fileSelectDialog.textInput.text
        self.fileSelectDialog.close_dialog(None)
        map_name = os.path.basename(locationMapFile).split("/")[-1]

        # TODO: Move map file to campaigns/files

        current_location: Location = self.screen.campaign_view.campaign.current_location

        # Create new location instance
        new_location = Location(map_name, {})
        new_location.set_map(locationMapFile)
        new_location.parent = current_location.name
        current_location.transitions[(self.new_x, self.new_y)] = map_name

        self.screen.campaign_view.add_location(new_location, map_name)

        self.screen.toLocation(new_location)
        self.screen.campaign_view.arrive(new_location)

        # Replace "Selecting location..." label with CollapseEntry instance for the new location
        self.addLocationEntry(new_location)

    def on_new_player_select(self, instance: Button):
        # Add player to list of players in collapsable
        new_player = self.new_player_dialog.get_player()

        self.screen.campaign_view.campaign.add_player(new_player)

        new_player_entry = EditableListEntry(new_player.name, new_player, None, None)
        self.players_list.add_entry(new_player_entry)

        dialog: NewPlayerDialog = instance.parent.parent
        dialog.close_dialog(None)

    def addLocationEntry(self, location: Location):
        new_location_entry = EditableListEntry(
            f"{location.name}\n{os.path.basename(location.map.map_file)}",
            location,
            self.screen.edit_location_cb,
            self.screen.delete_location_cb,
        )

        self.locations_list.add_entry(new_location_entry)

    def add_music_cb(self, instance: Button) -> Label:
        # File selection dialog
        fileSelectDialog = FileDialog(
            select_text="Select",
            popup_title="Select Music File",
            on_select=self.onNewMusicSelection,
            path=os.path.expanduser("~"),
        )
        fileSelectDialog.open_dialog(None)

        return Label(text="Selecting music...")

    def add_combat_music_cb(self, instance: Button) -> Label:
        # File selection dialog
        fileSelectDialog = FileDialog(
            select_text="Select",
            popup_title="Select New Combat Music",
            on_select=self.onNewCombatMusicSelection,
            path=os.path.expanduser("~"),
        )
        fileSelectDialog.open_dialog(None)

        return Label(text="Selecting music...")

    def onNewCombatMusicSelection(self, instance: Button):
        dialog: FileDialog = instance.parent.parent
        musicFile = dialog.textInput.text
        dialog.close_dialog(None)

        self.addMusicEntry(musicFile, self.combat_music_list)

        self.screen.campaign_view.add_combat_music(musicFile)

    def onNewMusicSelection(self, instance: Button):
        dialog: FileDialog = instance.parent.parent
        musicFile = dialog.textInput.text
        dialog.close_dialog(None)

        self.addMusicEntry(musicFile, self.music_list)

        self.screen.campaign_view.add_music(musicFile)

    def addMusicEntry(self, musicFile: str, musicList: CollapseItem):
        delete = self.delete_combat_music_cb
        if musicList == self.music_list:
            delete = self.delete_music_cb

        new_music_entry = EditableListEntry(
            musicFile,
            self.screen.campaign_view.campaign.current_location,
            None,
            delete,
        )
        musicList.add_entry(new_music_entry)

    def delete_music_cb(self, instance: Button) -> None:
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing

        # Remove music from location
        location.music.remove(parent.label.text)

        self.music_list.remove_entry(parent)

    def delete_combat_music_cb(self, instance: Button) -> None:
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing

        # Remove music from location
        location.combat_music.remove(parent.label.text)

        self.combat_music_list.remove_entry(parent)

    def add_player_cb(self, instance: Button) -> Label:
        # Create dialog for creating new player w/ callback to on_new_player()

        # self.new_player_dialog.clear()
        self.new_player_dialog.open_dialog(None)

        return Label(text="New Challenger?!")

    def on_new_player(self, player: Player):
        self.new_player_dialog.close_dialog(None)
