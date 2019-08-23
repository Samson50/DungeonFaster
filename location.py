import json
import pygame
import os

from pygame import *
from map.gridmap import GridMap
from map.hexmap import HexMap
from audio.mixer import Mixer


class Location:
    def __init__(self, path):
        self.name = path.split('/')[-1]

        self.data_file = path + "/" + self.name + ".data"
        with open(self.data_file, 'r') as data_file:
            raw_data = data_file.read()
            self.data = json.loads(raw_data)

        music_file = self.name + ".music"
        self.mixer = Mixer(music_file, path + "/")
        self.mixer.play()

        if self.data["type"] == "hexagon":
            self.map = HexMap(
                self.data["map"],
                self.data["x_margin"],
                self.data["y_margin"],
                self.data["pixel_density"],
                self.data["grid"],
                path + "/"
            )
        elif self.data["type"] == "square":
            self.map = GridMap(
                self.data["map"],
                self.data["x_margin"],
                self.data["y_margin"],
                self.data["pixel_density"],
                self.data["grid"],
                path + "/"
            )
        else:
            raise Exception

        self.save_file = path + "/" + self.name + ".save"
        if os.path.exists(self.save_file):
            self.load()

    def load(self):
        with open(self.save_file, 'r') as save_file:
            save_data = json.loads(save_file.read())
            self.map.load(save_data)

    def save(self):
        with open(self.save_file, 'w+') as save_file:
            save_data = {}
            self.map.save(save_data)
            save_file.write(json.dumps(save_data))

    def draw(self, surface):
        self.map.draw(surface)
        
    def update(self, events, surface):
        # Mouse Position
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        current_hex = self.map.get_grid(mouse_x, mouse_y)
        if current_hex:
            self.map.highlight_grid(surface, current_hex[0], current_hex[1])

        # Keyboard Input
        for game_event in events:
            if game_event.type == MOUSEBUTTONUP:
                self.map.flip_grid(mouse_x, mouse_y)
            if game_event.type == KEYDOWN:
                if game_event.key == K_RIGHT:
                    self.map.shift_right()
                elif game_event.key == K_LEFT:
                    self.map.shift_left()
                elif game_event.key == K_UP:
                    self.map.shift_up()
                elif game_event.key == K_DOWN:
                    self.map.shift_down()
                elif game_event.key == K_KP8:
                    self.map.zoom_in()
                elif game_event.key == K_KP2:
                    self.map.zoom_out()

                # Mixer
                elif game_event.key == K_PERIOD:
                    self.mixer.volume_up()
                elif game_event.key == K_COMMA:
                    self.mixer.volume_down()
                elif game_event.key == K_c:
                    self.mixer.switch_combat()


if __name__ == "__main__":
    print("working")
