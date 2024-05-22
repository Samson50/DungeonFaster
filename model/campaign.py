import os
import json

from model.map import Map


class Campaign:
    def __init__(self):
        self.name: str | os.PathLike = ""
        self.save_path: str | os.PathLike = ""
        self.overworld: Map = None
        self.position: tuple[int, int] = (0, 0)
        # TODO: self.locations: dict[tuple[int, int], Location] = None

    def save(self, out_path: str | os.PathLike) -> None | Exception:
        data_dict = {}
        data_dict["name"] = self.name
        data_dict["position"] = self.position
        if self.overworld:
            data_dict["over_world"] = self.overworld.save()

        try:
            json_data = json.dumps(data_dict, indent=4, separators=(",", ": "))
        except Exception as e:
            return e

        with open(out_path, "w") as out_file:
            out_file.write(json_data)

    def load(self, load_path: str | os.PathLike):

        with open(load_path, "r") as load_file:
            string_data = load_file.read()
            load_data = json.loads(string_data)

        self.name = load_data["name"]
        self.position = load_data["position"]

        self.overworld = Map(load_data["over_world"]["map_file"])
        self.overworld.load(load_data["over_world"])
