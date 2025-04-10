import os
import shutil

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from dungeonfaster.gui.campaignView import CampaignView
from dungeonfaster.gui.dialogs import NPCDialog
from dungeonfaster.gui.menuManager import MenuManager
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
CAMP_FILE_DIR = os.path.join(CAMPAIGNS_DIR, "files")


class NewCampaignScreen(Screen):
    overworld_map_dialog: FileDialog

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager
        self.fileChooser = None

        self.walls: dict[Ellipse, tuple[float, float]] = {}
        self.lines: list[Line] = []
        self.line = Line(points=[], width=2)
        self.grabbed_wall: Ellipse | None = None
        self.wall_moved: bool = False
        self.active_wall: Ellipse | None = None
        self.wall_segments: list[list[Ellipse]] = [[]]

        layout = BoxLayout(orientation="vertical")

        # Header layout items
        self.saveDialog = FileDialog(
            select_text="Save",
            popup_title="Save Campaign",
            on_select=self.on_save_campaign,
            path=CAMPAIGNS_DIR,
        )

        self.loadDialog = FileDialog(
            select_text="Load",
            popup_title="Load Campaign",
            on_select=self.on_load_campaign,
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
        self.campaign_view.bind(on_touch_up=self.campaign_view.on_click_up)
        self.get_map_button = Button(text="Select Overworld Map")
        self.get_map_button.bind(on_release=self.select_overworld_map_dialog)
        self.campaign_view.add_widget(self.get_map_button)

        # Override normal map draw
        self.campaign_view.draw = self.draw

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

    def draw(self):
        self.campaign_view.map.draw()
        if not self.campaign_view.moving_token:
            self.campaign_view.draw_party()
        self.campaign_view.draw_selected()

        self.draw_walls()

    def wall_pos_to_map(self, pos: tuple[float, float]) -> tuple[float, float]:
        wall_x, wall_y = pos
        circle_x = wall_x / self.campaign_view.map.window.zoom - self.campaign_view.map.window.x
        circle_y = wall_y / self.campaign_view.map.window.zoom - self.campaign_view.map.window.y
        return (circle_x, circle_y)

    def draw_walls(self):
        for wall, wall_pos in self.walls.items():
            if wall == self.grabbed_wall:
                wall.size = (60, 60)
            elif wall == self.active_wall:
                wall.size = (40, 40)
            else:
                wall.size = (20, 20)

            if wall not in self.campaign_view.map.window.surface.canvas.children:
                self.campaign_view.map.window.surface.canvas.add(wall)

            wall.pos = self.wall_pos_to_map(wall_pos)
            wall.pos = (wall.pos[0] - wall.size[0] / 2, wall.pos[1] - wall.size[1] / 2)

        # Draw lines in between walls
        for line, segments in zip(self.lines, self.campaign_view.map.walls, strict=True):
            points = []
            for wall in segments:
                x, y = self.wall_pos_to_map(wall)
                points.append(x)
                points.append(y)
            line.points = points
            if line not in self.campaign_view.map.window.surface.canvas.children:
                self.campaign_view.map.window.surface.canvas.add(line)

    def on_touch_move(self, touch: MotionEvent):
        if self.grabbed_wall:
            self.wall_moved = True
            cursor_x, cursor_y = touch.pos
            wall_x: float = (self.campaign_view.map.window.x + cursor_x) * self.campaign_view.map.window.zoom
            wall_y: float = (self.campaign_view.map.window.y + cursor_y) * self.campaign_view.map.window.zoom

            wall_dot = self.grabbed_wall
            wall_dot.pos = (cursor_x - wall_dot.size[0] / 2, cursor_y - wall_dot.size[1] / 2)
            self.walls[wall_dot] = (wall_x, wall_y)
        self.draw_walls()

    def collides_with_wall(self, pos: tuple[float, float]) -> Ellipse:
        for wall in self.walls:
            if self.wall_collide(pos, wall):
                return wall

        return None

    def wall_collide(self, pos: tuple[float, float], wall: Ellipse) -> bool:
        wall_x, wall_y = wall.pos
        wall_width, wall_height = wall.size
        cursor_x, cursor_y = pos
        x_offset = self.campaign_view.map_layout.x
        y_offset = self.campaign_view.map_layout.y

        return bool(
            cursor_x < wall_x + wall_width + x_offset
            and cursor_x > wall_x
            and cursor_y < wall_y + wall_height + y_offset
            and cursor_y > wall_y
        )

    def wall_resize(self, wall: Ellipse, size: tuple[float, float]):
        wall_x, wall_y = wall.pos
        circle_x = wall_x / self.campaign_view.map.window.zoom - self.campaign_view.map.window.x
        circle_y = wall_y / self.campaign_view.map.window.zoom - self.campaign_view.map.window.y
        wall.pos = (circle_x - wall.size[0] / 2, circle_y - wall.size[1] / 2)

    def wall_touch_down(self, layout: FloatLayout, event: MotionEvent):
        collission = self.collides_with_wall(event.pos)
        if self.collides_with_wall(event.pos):
            wall_pos = self.walls[collission]
            self.grabbed_wall = collission
            self.grabbed_wall.size = (60, 60)
            wall_x, wall_y = wall_pos
            circle_x = wall_x / self.campaign_view.map.window.zoom - self.campaign_view.map.window.x
            circle_y = wall_y / self.campaign_view.map.window.zoom - self.campaign_view.map.window.y
            collission.pos = (circle_x - collission.size[0] / 2, circle_y - collission.size[1] / 2)
            return

        if self.grabbed_wall:
            self.grabbed_wall = None

        self.campaign_view.on_click(layout, event)

    def handle_wall_up(self, event: MotionEvent):
        # If current grabbing wall
        if self.grabbed_wall:
            wall = self.grabbed_wall
            wall_x, wall_y = self.walls[self.grabbed_wall]
            self.grabbed_wall = None
            circle_x = wall_x / self.campaign_view.map.window.zoom - self.campaign_view.map.window.x
            circle_y = wall_y / self.campaign_view.map.window.zoom - self.campaign_view.map.window.y
            wall.pos = (circle_x - wall.size[0] / 2, circle_y - wall.size[1] / 2)
            if self.wall_moved:
                self.wall_moved = False
                return

        collission = self.collides_with_wall(event.pos)
        # If we're clicking on a wall and no wall is currently active
        if not self.active_wall:
            if collission:
                self.active_wall = collission
                return
        # If there's already an active wall and we're clicking on a wall
        elif collission:
            if self.active_wall == collission:
                self.active_wall = None
                return
            self.active_wall = collission
            return

        cursor_x, cursor_y = event.pos
        wall_x: float = (self.campaign_view.map.window.x + cursor_x) * self.campaign_view.map.window.zoom
        wall_y: float = (self.campaign_view.map.window.y + cursor_y) * self.campaign_view.map.window.zoom

        wall_dot = Ellipse(segments=3, size=(20, 20), pos=(cursor_x, cursor_y))
        wall_dot.pos = (wall_dot.pos[0] - wall_dot.size[0] / 2, wall_dot.pos[1] - wall_dot.size[1] / 2)
        self.walls[wall_dot] = (wall_x, wall_y)
        self.campaign_view.map_layout.canvas.add(wall_dot)

        # Get active wall segment by current active wall
        if self.active_wall:
            wall = self.walls[self.active_wall]
            for segments in self.campaign_view.map.walls:
                for segment in segments:
                    if wall == segment:
                        segments.append((wall_x, wall_y))
                        break
        else:
            # Add new Line to self.lines
            self.lines.append(Line(points=[], width=2))
            self.campaign_view.map.walls.append([(wall_x, wall_y)])

        self.active_wall = wall_dot

    def wall_touch_up(self, layout: FloatLayout, event: MotionEvent):
        if self.campaign_view.moved:
            return

        if event.grab_current:
            return

        self.handle_wall_up(event)

        self.draw_walls()

    def wall_move(self):
        pass

    def on_text(self, instance: TextInput, value: str) -> None:
        self.campaign_view.campaign.name = value

    def select_overworld_map_dialog(self, instance):
        self.overworld_map_dialog = FileDialog(
            popup_title="Select Overworld Map",
            on_select=self.save_overworld_map,
        )

        self.overworld_map_dialog.open_dialog(None)

    def save_overworld_map(self, instance):
        # Set overworld map file
        overworld_map_file = self.overworld_map_dialog.text_input.text
        self.campaign_view.remove_widget(self.get_map_button)
        self.overworld_map_dialog.close_dialog(None)
        # TODO: Move map file to campaigns/files

        base_location = Location("overworld", {})
        base_location.set_map(overworld_map_file)
        self.campaign_view.map = base_location.map

        self.campaign_view.add_location(base_location, "overworld")

        self.campaign_view.map.get_zoom_for_surface(self.campaign_view.map_layout)
        self.campaign_view.draw()

        self.campaign_view.set_sliders()

    def location_back_cb(self, instance):
        current_location = self.campaign_view.leave()

        if current_location.parent is None:
            self.remove_widget(self.location_back_button)

        self.to_location(current_location)

    def on_save_campaign(self, instance):
        save_file = self.saveDialog.text_input.text
        self.campaign_view.save(save_file)

        self.saveDialog.close_dialog(None)

    def on_load_campaign(self, instance):
        load_file = self.loadDialog.text_input.text
        self.loadDialog.close_dialog(None)

        self.campaign_view.load(load_file)

        self.campaign_view.remove_widget(self.get_map_button)

        # If location.parent, add back button
        if self.campaign_view.campaign.current_location.parent is not None:
            self.add_back_button()

        # Update campaign name from loaded
        self.campaign_name.text = self.campaign_view.campaign.name

        # Add players
        for player in self.campaign_view.campaign.party:
            new_player_entry = EditableListEntry(player.name, player, None, None)
            self.controls_layout.players_list.add_entry(new_player_entry)

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
            self.controls_layout.add_location_entry(location)

        # Add walls for display
        for segment in self.campaign_view.map.walls:
            points = []
            for wall_x, wall_y in segment:
                circle_x = wall_x * self.campaign_view.map.window.zoom - self.campaign_view.map.window.x
                circle_y = wall_y * self.campaign_view.map.window.zoom - self.campaign_view.map.window.y
                wall_dot = Ellipse(segments=3, size=(20, 20), pos=(circle_x, circle_y))
                wall_dot.pos = (wall_dot.pos[0] - wall_dot.size[0] / 2, wall_dot.pos[1] - wall_dot.size[1] / 2)
                self.walls[wall_dot] = (wall_x, wall_y)

                points.append(wall_dot.pos[0] + wall_dot.size[0] / 2)
                points.append(wall_dot.pos[1] + wall_dot.size[1] / 2)
            # Add any lines between walls
            self.lines.append(Line(points=points, width=2))

        # Add musics for current location
        for music in self.campaign_view.campaign.current_location.music:
            self.controls_layout.add_music_entry(music, self.controls_layout.music_list)
        for combat_music in self.campaign_view.campaign.current_location.combat_music:
            self.controls_layout.add_music_entry(combat_music, self.controls_layout.combat_music_list)

    def add_back_button(self):
        # Add back button to go back to higher location
        if self.location_back_button not in self.children:
            self.add_widget(self.location_back_button)

    def to_location(self, location: Location):
        self.campaign_view.campaign.current_location = location

        self.controls_layout.map_editor_layout.name_input.text = location.name

        # Add back button to go back to higher location
        if location.parent is not None:
            self.add_back_button()

        # Update switches
        self.controls_layout.map_editor_layout.hidden_switch.active = self.campaign_view.map.hidden_tiles

        # TODO: Set music and item collapse view items

    def edit_location_cb(self, instance: Button):
        parent: EditableListEntry = instance.parent
        location: Location = parent.thing
        self.to_location(location)
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

        self.density_controller = LabeledIntInput("Box Size", self.set_density, 0.5, 100, size_hint=(1, 0.08))
        self.add_widget(self.density_controller)
        self.xOffsetController = LabeledIntInput("X Offset", self.set_x_offset, 1, 0, size_hint=(1, 0.08))
        self.add_widget(self.xOffsetController)
        self.yOffsetController = LabeledIntInput("Y Offset", self.set_y_offset, 1, 0, size_hint=(1, 0.08))
        self.add_widget(self.yOffsetController)

        self.xMarginController = LabeledIntInput("X Margin", self.set_x_margin, 1, 1, size_hint=(1, 0.08))
        self.add_widget(self.xMarginController)
        self.yMarginController = LabeledIntInput("Y Margin", self.set_y_margin, 1, 1, size_hint=(1, 0.08))
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

        # Add walls: Switch
        self.walls_switch_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        self.walls_switch_layout.add_widget(Label(text="Adding walls"))
        self.walls_switch = Switch(active=False)
        self.walls_switch.bind(active=self.walls_cb)
        self.walls_switch_layout.add_widget(self.walls_switch)
        self.add_widget(self.walls_switch_layout)

        self.hide_buttons_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.08))
        all_on_button = Button(text="All On")
        all_on_button.bind(on_release=self.all_on)
        all_off_button = Button(text="All Off")
        all_off_button.bind(on_release=self.all_off)
        invert_button = Button(text="Invert Tiles")
        invert_button.bind(on_release=self.invert_tiles)
        self.hide_buttons_layout.add_widget(all_on_button)
        self.hide_buttons_layout.add_widget(all_off_button)
        self.hide_buttons_layout.add_widget(invert_button)

    def on_text(self, instance: TextInput, value: str) -> None:
        self.screen.campaign_view.campaign.current_location.name = value

    def all_on(self, instance):
        for i in range(self.screen.campaign_view.map.grid.x):
            for j in range(self.screen.campaign_view.map.grid.y):
                if (i, j) not in self.screen.campaign_view.map.grid.matrix:
                    self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

    def all_off(self, instance):
        for tile in self.screen.campaign_view.map.grid.matrix:
            self.screen.campaign_view.map.grid.flip_tile(*tile)
        self.screen.campaign_view.map.draw()

    def invert_tiles(self, instance):
        for i in range(self.screen.campaign_view.map.grid.x):
            for j in range(self.screen.campaign_view.map.grid.y):
                self.screen.campaign_view.map.grid.flip_tile(i, j)
        self.screen.campaign_view.map.draw()

    def update_from_map(self, map_arg: Map):
        self.map_file_label.text = os.path.basename(map_arg.map_file)
        self.density_controller.input.text = str(map_arg.grid.pixel_density)
        self.density_controller.value = map_arg.grid.pixel_density
        self.xOffsetController.input.text = str(map_arg.grid.x_offset)
        self.xOffsetController.value = map_arg.grid.x_offset
        self.yOffsetController.input.text = str(map_arg.grid.y_offset)
        self.yOffsetController.value = map_arg.grid.y_offset
        self.xMarginController.input.text = str(map_arg.grid.x_margin)
        self.xMarginController.value = map_arg.grid.x_margin
        self.yMarginController.input.text = str(map_arg.grid.y_margin)
        self.yMarginController.value = map_arg.grid.y_margin

    def hex_switch_cb(self, instance: Switch, state: bool):
        if not self.screen.campaign_view.map:
            return

        if state:
            self.screen.campaign_view.map.to_hex()
        else:
            self.screen.campaign_view.map.to_square()

        self.screen.campaign_view.map.draw()

    def walls_cb(self, instance: Switch, state: bool):
        if state:
            # Remove current on_touch and set walls on_touch
            self.screen.campaign_view.unbind(on_touch_down=self.screen.campaign_view.on_click)
            self.screen.campaign_view.unbind(on_touch_up=self.screen.campaign_view.on_click_up)

            self.screen.campaign_view.bind(on_touch_down=self.screen.wall_touch_down)
            self.screen.campaign_view.bind(on_touch_up=self.screen.wall_touch_up)
        else:
            # Remove walls on_touch and set default on_touch
            self.screen.campaign_view.unbind(on_touch_down=self.screen.wall_touch_down)
            self.screen.campaign_view.unbind(on_touch_up=self.screen.wall_touch_up)

            self.screen.campaign_view.bind(on_touch_down=self.screen.campaign_view.on_click)
            self.screen.campaign_view.bind(on_touch_up=self.screen.campaign_view.on_click_up)

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

    def set_x_offset(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.x_offset = value
        self.screen.campaign_view.map.draw()

    def set_y_offset(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.y_offset = value
        self.screen.campaign_view.map.draw()

    def set_x_margin(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.x_margin = value
        self.screen.campaign_view.map.update()
        self.screen.campaign_view.map.draw()

    def set_y_margin(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.y_margin = value
        self.screen.campaign_view.map.update()
        self.screen.campaign_view.map.draw()

    def set_density(self, value: float):
        if self.screen.campaign_view.map is None:
            return
        self.screen.campaign_view.map.grid.pixel_density = value
        self.screen.campaign_view.map.update()
        self.screen.campaign_view.map.draw()


class ControllerLayout(BoxLayout):
    file_selection_dialog: FileDialog
    new_x: int
    new_y: int

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

        # NPCs
        self.npc_list = CollapseItem("Add NPC", self.add_npc_cb, title="NPCs")
        self.accordion.add_widget(self.npc_list)

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
            self.file_selection_dialog = FileDialog(
                select_text="Select",
                popup_title="Select New Location Map",
                on_select=self.on_new_location_map_selection,
                path=os.path.expanduser("~"),
            )
            self.file_selection_dialog.open_dialog(None)

    def on_new_location_map_selection(self, instance: Button):
        location_map_file = self.file_selection_dialog.text_input.text
        self.file_selection_dialog.close_dialog(None)
        map_name = os.path.basename(location_map_file).split("/")[-1]

        # Move map file to campaigns/files
        new_map_file = os.path.join(CAMP_FILE_DIR, map_name)
        if new_map_file != location_map_file:
            shutil.copy(location_map_file, new_map_file)

        current_location: Location = self.screen.campaign_view.campaign.current_location

        # Create new location instance
        new_location = Location(map_name, {})
        new_location.set_map(new_map_file)
        new_location.parent = current_location.name
        new_location.entrances[(self.new_x, self.new_y)] = (0, 0)
        current_location.transitions[(self.new_x, self.new_y)] = map_name

        self.screen.campaign_view.add_location(new_location, map_name)

        self.screen.to_location(new_location)
        self.screen.campaign_view.arrive(new_location, (self.new_x, self.new_y))

        # Replace "Selecting location..." label with CollapseEntry instance for the new location
        self.add_location_entry(new_location)

    def on_new_player_select(self, instance: Button):
        # Add player to list of players in collapsable
        new_player = self.new_player_dialog.get_player()

        self.screen.campaign_view.campaign.add_player(new_player)

        new_player_entry = EditableListEntry(new_player.name, new_player, None, None)
        self.players_list.add_entry(new_player_entry)

        dialog: NewPlayerDialog = instance.parent.parent
        dialog.close_dialog(None)

    def add_location_entry(self, location: Location):
        new_location_entry = EditableListEntry(
            f"{location.name}\n{os.path.basename(location.map.map_file)}",
            location,
            self.screen.edit_location_cb,
            self.screen.delete_location_cb,
        )

        self.locations_list.add_entry(new_location_entry)

    def add_music_cb(self, instance: Button) -> Label:
        # File selection dialog
        file_selection_dialog = FileDialog(
            select_text="Select",
            popup_title="Select Music File",
            on_select=self.on_new_music_selection,
            path=os.path.expanduser("~"),
        )
        file_selection_dialog.open_dialog(None)

        return Label(text="Selecting music...")

    def add_combat_music_cb(self, instance: Button) -> Label:
        # File selection dialog
        file_selection_dialog = FileDialog(
            select_text="Select",
            popup_title="Select New Combat Music",
            on_select=self.on_new_combat_music_selection,
            path=os.path.expanduser("~"),
        )
        file_selection_dialog.open_dialog(None)

        return Label(text="Selecting music...")

    def on_new_combat_music_selection(self, instance: Button):
        dialog: FileDialog = instance.parent.parent
        music_file = dialog.text_input.text
        dialog.close_dialog(None)

        self.add_music_entry(music_file, self.combat_music_list)

        self.screen.campaign_view.add_combat_music(music_file)

    def on_new_music_selection(self, instance: Button):
        dialog: FileDialog = instance.parent.parent
        music_file = dialog.text_input.text
        dialog.close_dialog(None)

        self.add_music_entry(music_file, self.music_list)

        self.screen.campaign_view.add_music(music_file)

    def add_npc_cb(self, insatnce: Button):
        # NPC Creation Dialog
        npc_selection_dialog = NPCDialog(
            self.on_new_npc_selection,
            select_text="Select",
            popup_title="Select New NPC",
        )
        npc_selection_dialog.open_dialog(None)

        return Label(text="Selecting NPC...")

    def on_new_npc_selection(self, instance: Button):
        dialog: NPCDialog = instance.parent.parent

        # TODO: Add the npc
        # new_npc: NPC = dialog.npc
        print("WIP")

        dialog.close_dialog(None)

    def add_music_entry(self, music_file: str, music_list: CollapseItem):
        delete = self.delete_combat_music_cb
        if music_list == self.music_list:
            delete = self.delete_music_cb

        new_music_entry = EditableListEntry(
            music_file,
            self.screen.campaign_view.campaign.current_location,
            None,
            delete,
        )
        music_list.add_entry(new_music_entry)

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
