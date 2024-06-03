import os
import json

from kivy.uix.widget import Widget

from model.location import Location
from model.map import Map


class Campaign:
    def __init__(self):
        self.name: str | os.PathLike = ""
        self.save_path: str | os.PathLike = ""
        self.overworld: Map = None
        self.position: tuple[int, int] = (0, 0)
        self.locations: dict[tuple[int, int], Location] = {}

    def save(self, out_path: str | os.PathLike) -> None | Exception:
        data_dict = {}
        data_dict["name"] = self.name
        data_dict["position"] = self.position
        if self.overworld:
            data_dict["over_world"] = self.overworld.save()

        locations_dict = {}
        for location in self.locations.keys():
            locations_dict[str(location)] = self.locations[location].save()
        data_dict["locations"] = locations_dict

        try:
            json_data = json.dumps(data_dict, indent=4, separators=(",", ": "))
        except Exception as e:
            return e

        with open(out_path, "w") as out_file:
            out_file.write(json_data)

    def load(self, load_path: str | os.PathLike, surface: Widget):

        with open(load_path, "r") as load_file:
            string_data = load_file.read()
            load_data = json.loads(string_data)

        self.name = load_data["name"]
        self.position = load_data["position"]

        self.overworld = Map(load_data["over_world"]["map_file"])
        self.overworld.load(load_data["over_world"], surface)

        for location in load_data["locations"].keys():
            new_index = eval(load_data["locations"][location]["index"])
            self.overworld.points_of_interest.append(new_index)
            new_name = load_data["locations"][location]["name"]
            new_location = Location(new_name, new_index[0], new_index[1])
            new_location.load(load_data["locations"][location], surface)
            self.locations[new_index] = new_location

    def goToLocation(self, x: int, y: int) -> None:
        pass
