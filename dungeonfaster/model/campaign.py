import os
import json

from kivy.uix.widget import Widget

from dungeonfaster.model.location import Location
from dungeonfaster.model.player import Player
from dungeonfaster.model.map import Map


class Campaign:
    def __init__(self):
        self.name: str | os.PathLike = ""
        self.save_path: str | os.PathLike = ""
        self.position: tuple[int, int] = (0, 0)
        self.locations: dict[str, Location] = {}
        self.current_location: Location = None
        self.party: list[Player] = []

    def save(self, out_path: str | os.PathLike) -> None:
        data_dict = {"name": self.name, "position": self.position, "current_location": self.current_location.name}

        party: list[dict] = []
        for player in self.party:
            party.append(player.save())
        data_dict["party"] = party

        locations_dict = {}
        for name, location in self.locations.items():
            locations_dict[name] = location.save()
        data_dict["locations"] = locations_dict

        json_data = json.dumps(data_dict, indent=4, separators=(",", ": "))

        with open(out_path, "w") as out_file:
            out_file.write(json_data)

    def load(self, load_path: str | os.PathLike, surface: Widget):

        with open(load_path, "r") as load_file:
            string_data = load_file.read()
            load_data = json.loads(string_data)

        if "party" in load_data.keys():
            for player_dict in load_data["party"]:
                new_player: Player = Player()
                new_player.load(player_dict)
                self.party.append(new_player)

        self.name = load_data["name"]
        self.position = tuple(load_data["position"])

        # Load locations
        for name, location_data in load_data["locations"].items():
            self.locations[name] = Location(name, location_data)
            self.locations[name].load(surface)

        self.current_location = self.getLocation(load_data["current_location"])

    def getLocation(self, name: str, locations=None) -> Location | None:
        return self.locations.get(name, None)

    def goToLocation(self, x: int, y: int) -> None:
        pass

    def addPlayer(self, player: Player):
        self.party.append(player)
