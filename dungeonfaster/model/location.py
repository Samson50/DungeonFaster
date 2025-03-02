import os

from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader, Sound

from dungeonfaster.model.map import Map


class Location:
    def __init__(self, name: str, location_data: dict):
        self.parent: str | None = location_data.get("parent", None)
        self.name: str = name
        self.map: Map = Map()
        self.map_data: dict = location_data.get("map", {})
        self.position: tuple[int, int] = location_data.get("position", (0, 0))
        self.music: list[str] = location_data.get("music", [])
        self.combat_music: list[str] = location_data.get("combat_music", [])

        # self.transitions: dict[tuple[int, int], str] = location_data.get("transitions", {})
        self.transitions = {}
        for transition, location in location_data.get("transitions", {}).items():
            self.transitions[eval(transition)] = location

        # self.entrances: dict[tuple[int, int], tuple[int, int]] = location_data.get("entrances", {})
        self.entrances = {}
        for entrance, position in location_data.get("entrances", {}).items():
            self.entrances[eval(entrance)] = eval(position)

    def set_map(self, map_file: os.PathLike):
        self.map = Map(map_file=map_file)
        self.map.load_image(map_file)

    def save(self) -> dict:
        save_dict = {"name": self.name, "map": self.map.save(), "music": self.music, "combat_music": self.combat_music,
                     "position": self.position, "transitions": self.transitions}

        return save_dict

    def load(self, surface: Widget) -> None:
        self.map.load(self.map_data, surface)

        # for song_file in load_json["music"]:
        #     self.music.append(SoundLoader.load(song_file))

        # for song_file in load_json["combat_music"]:
        #     self.music.append(SoundLoader.load(song_file))

    def interact(self, x: int, y: int):
        pass

    def leave(self):
        # Prepare to "leave" location, stop any location specific routines
        pass

    def arrive(self):
        # Initialize values for location display and use
        pass
