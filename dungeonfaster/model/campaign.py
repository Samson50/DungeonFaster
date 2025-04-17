import json
import os
from typing import Any

from kivy.uix.widget import Widget

from dungeonfaster.model.location import Location
from dungeonfaster.model.player import Player

FILES_PATH = "campaigns/files"


class Campaign:
    path: str
    current_location: Location

    def __init__(self):
        self.name: str | os.PathLike = ""
        self.save_path: str | os.PathLike = ""
        self.position: tuple[int, int] = (0, 0)
        self.locations: dict[str, Location] = {}
        self.party: list[Player] = []

    def save(self, out_path: str | os.PathLike) -> None:
        data_dict = {"name": self.name, "position": str(self.position), "current_location": self.current_location.name}

        party: list[dict] = []
        for player in self.party:
            party.append(player.save())
        data_dict["party"] = party

        locations_dict = {}
        for name, location in self.locations.items():
            locations_dict[name] = location.save()
        data_dict["locations"] = locations_dict

        json_data = json.dumps(data_dict, indent=4, separators=(",", ": "))

        with open(out_path, "w", encoding="utf-8") as out_file:
            out_file.write(json_data)

    def load(self, load_path: str | os.PathLike, surface: Widget):
        self.path = load_path

        with open(load_path, encoding="utf-8") as load_file:
            string_data = load_file.read()
            load_data = json.loads(string_data)

        for player_dict in load_data.get("party", {}):
            new_player: Player = Player()
            new_player.load(player_dict)
            self.party.append(new_player)

        self.name = load_data["name"]
        self.position = eval(load_data["position"])

        # Load locations
        for name, location_data in load_data["locations"].items():
            self.locations[name] = Location(name, location_data)
            self.locations[name].load(surface)

        self.current_location = self.get_location(load_data["current_location"])

    def get_location(self, name: str) -> Location:
        try:
            return self.locations[name]
        except KeyError:
            return self.locations["overworld"]

    def add_player(self, player: Player):
        self.party.append(player)

    def set_player_pos(self, player_name: str, pos: tuple[int, int]):
        player = next(player for player in self.party if player.name == player_name)

        player.position = pos

    def get_files(self, load_path: str) -> list[str]:
        files: list[str] = []

        with open(load_path, encoding="utf-8") as load_file:
            string_data = load_file.read()
            load_data: dict[str, Any] = json.loads(string_data)

        for player_dict in load_data.get("party", {}):
            image_file = player_dict.get("image", None)
            if image_file and "/" in image_file:
                image_file = image_file.split("/")[-1]
            files.append(os.path.join(FILES_PATH, image_file))

        for location_dict in load_data.get("locations", {}).values():
            image_file = location_dict["map"]["map_file"]
            if "/" in image_file:
                image_file = image_file.split("/")[-1]
            files.append(os.path.join(FILES_PATH, image_file))

        return files
