import os

from kivy.uix.widget import Widget

from model.map import Map


class Location:
    def __init__(self, name: str, x: int, y: int):
        self.parent = None
        self.name: str = name
        self.map: Map = Map()
        self.index: tuple[int, int] = (x, y)
        self.locations: dict[tuple[int, int], Location] = {}
        # TODO: self.music
        # TODO: self.combat_music
        # TODO: self.items
        pass

    def set_map(self, map_file: os.PathLike):
        self.map = Map(map_file=map_file)
        self.map.load_image(map_file)

    def save(self) -> dict:
        save_dict = {}
        save_dict["name"] = self.name
        save_dict["map"] = self.map.save()
        save_dict["index"] = str(self.index)

        locations_dict = {}
        for location in self.locations.keys():
            locations_dict[str(location)] = self.locations[location].save()
        save_dict["locations"] = locations_dict

        return save_dict

    def load(self, load_json: dict, surface: Widget) -> None:
        self.name = load_json["name"]
        self.map.load(load_json["map"], surface)
        self.index = eval(load_json["index"])

        for location in load_json["locations"].keys():
            new_index = eval(load_json["locations"][location]["index"])
            new_name = load_json["locations"][location]["name"]
            new_location = Location(new_name, new_index[0], new_index[1])
            new_location.load(load_json["locations"][location], surface)
