import os
import json

from kivy.uix.widget import Widget

from dungeonfaster.model.location import Location
from dungeonfaster.model.map import Map


class Campaign:
    def __init__(self):
        self.name: str | os.PathLike = ""
        self.save_path: str | os.PathLike = ""
        self.position: tuple[int, int] = (0, 0)
        self.locations: dict[tuple[int, int], Location] = {}
        self.current_location: Location = None

    def save(self, out_path: str | os.PathLike) -> None | Exception:
        data_dict = {}
        data_dict["name"] = self.name
        data_dict["position"] = self.position

        data_dict["current_location"] = self.current_location.name

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
        self.position = tuple(load_data["position"])

        # Load base (overworld) location
        base_data = load_data["locations"][str((0, 0))]
        base_location = Location(base_data["name"], 0, 0)
        base_location.load(base_data, surface)
        self.locations[(0, 0)] = base_location

        self.current_location = self.getLocation(load_data["current_location"])

    def getLocation(self, name: str, locations=None) -> Location | None:
        if locations is None:
            locations = self.locations

        for location in locations.values():
            if location.name == name:
                return location
            else:
                ret = self.getLocation(name, location.locations)
                if ret:
                    return ret
        return None

    def goToLocation(self, x: int, y: int) -> None:
        pass
