from kivy.graphics import Rectangle, Color
from kivy.input.motionevent import MotionEvent
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch

from gui.menuManager import MenuManager
from gui.utilities import FileDialog, LabeledIntInput

from model.map import Map
from model.campaign import Campaign

DELTA_X_SHIFT = 15
DELTA_Y_SHIFT = 15


class NewCampaignScreen(Screen):

    def __init__(self, manager: MenuManager, **kwargs):
        super().__init__(name="NewCampaign")

        self.menuManager = manager
        self.fileChooser = None
        self.map: Map = None
        self.campaign: Campaign = Campaign()

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

        self.map_layout = BoxLayout(orientation="vertical", size_hint=(0.7, 1))
        getMapButton = Button(text="Select Overworld Map")
        getMapButton.bind(on_release=self.selectOverworldMapDialog)
        self.map_layout.add_widget(getMapButton)
        editor_layout.add_widget(self.map_layout)

        self.controls_layout = ControllerLayout(self)
        editor_layout.add_widget(self.controls_layout)

        self.add_widget(layout)
        self.menuManager.add_widget(self)

    # TODO: How to catch going full-screen?
    def on_size(self, instance, value):
        if self.map:
            self.map.drawSparse()

    def onSaveCampaign(self, instance):
        saveFile = self.saveDialog.textInput.text
        self.campaign.save(saveFile)

        self.saveDialog.closeDialog(None)

    def onLoadCampaign(self, instance):
        loadFile = self.loadDialog.textInput.text
        self.loadDialog.closeDialog(None)
        try:
            self.campaign.load(loadFile)
            self.map = self.campaign.overworld
        except Exception as e:
            print(e)
            return

        # Update controllers with values loaded from campaign
        self.controls_layout.update_from_map(self.map)

        # Prepare to display map
        self.map_layout.clear_widgets()
        self.map.window.surface = self.map_layout

        # Make sure we show hidden tiles if necessary
        if self.map.hidden_tiles:
            self.controls_layout.hidden_switch.active = True
        else:
            # Activating switch will re-draw map otherwise
            self.map.drawSparse()

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
        self.map.drawSparse()


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

        # Empty layout for spacing
        self.empty_layout = BoxLayout(size_hint=(1, 0.4))
        self.add_widget(self.empty_layout)

    def on_size(self, instance, value):
        # Re-draw black background
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def allOn(self, instance):
        for i in range(len(self.screen.map.grid.matrix)):
            for j in range(len(self.screen.map.grid.matrix[i])):
                self.screen.map.grid.matrix[i][j] = 1
        self.screen.map.drawSparse()

    def allOff(self, instance):
        for i in range(len(self.screen.map.grid.matrix)):
            for j in range(len(self.screen.map.grid.matrix[i])):
                self.screen.map.grid.matrix[i][j] = 0
        self.screen.map.drawSparse()

    def invertTiles(self, instance):
        for i in range(len(self.screen.map.grid.matrix)):
            for j in range(len(self.screen.map.grid.matrix[i])):
                self.screen.map.grid.matrix[i][j] = abs(
                    self.screen.map.grid.matrix[i][j] - 1
                )
        self.screen.map.drawSparse()

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

        if state:
            self.screen.map.toHex()
        else:
            self.screen.map.toSquare()

        self.screen.map.drawSparse()

    def hidden_cb(self, instance: Switch, state: bool):
        if self.screen.map:
            self.screen.map.hidden_tiles = state

        if state:
            # Add show tile buttons
            self.remove_widget(self.empty_layout)
            self.add_widget(self.hide_buttons_layout)
            self.add_widget(self.empty_layout)
            # Register on_click listener for self.screen.map_layout
            self.screen.map_layout.bind(on_touch_down=self.tile_flip_cb)
        else:
            # Remove / hide tile buttons
            self.remove_widget(self.hide_buttons_layout)
            # Remove on_click listener
            self.screen.map_layout.unbind(on_touch_down=self.tile_flip_cb)

        self.screen.map.drawSparse()

    def tile_flip_cb(self, layout: BoxLayout, event: MotionEvent):
        (mouse_x, mouse_y) = event.pos
        (map_x, map_y) = self.screen.map_layout.pos
        (map_width, map_height) = self.screen.map_layout.size

        # Ensure touch is on the map, ignore otherwise
        if map_x < mouse_x < map_x + map_width and map_y < mouse_y < map_y + map_height:
            self.screen.map.flip_at_coordinate(mouse_x - map_x, mouse_y - map_y)
            self.screen.map.drawSparse()

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
        self.screen.map.drawSparse()

    def zoomOut(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.window.zoom += 1
        self.screen.map.update()
        self.screen.map.drawSparse()

    def mapLeft(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.x += DELTA_X_SHIFT
        self.screen.map.drawSparse()

    def mapRight(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.x -= DELTA_X_SHIFT
        self.screen.map.drawSparse()

    def mapUp(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.y -= DELTA_Y_SHIFT
        self.screen.map.drawSparse()

    def mapDown(self, value: int) -> None:
        if self.screen.map is None:
            return
        self.screen.map.window.y += DELTA_Y_SHIFT
        self.screen.map.drawSparse()

    def setXOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.x_offset = value
        self.screen.map.drawSparse()

    def setYOffset(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.y_offset = value
        self.screen.map.drawSparse()

    def setXMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.x_margin = value
        self.screen.map.update()
        self.screen.map.drawSparse()

    def setYMargin(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.y_margin = value
        self.screen.map.update()
        self.screen.map.drawSparse()

    def setDensity(self, value: float):
        if self.screen.map is None:
            return
        self.screen.map.grid.pixel_density = value
        self.screen.map.update()
        self.screen.map.drawSparse()
