class Player:
    def __init__(self, name=None, cls=None, race=None, level=1):
        self.name: str = name
        self.cls: str = cls
        self.race: str = race
        self.level: int = level

        self.position: tuple[int, int] = (0, 0)
        self.image: str = None # TODO

    def save(self) -> dict:
        data_dict = {}

        data_dict["name"] = self.name
        data_dict["class"] = self.cls
        data_dict["race"] = self.race
        data_dict["level"] = self.level
        data_dict["position"] = self.position
        data_dict["image"] = self.image

        return data_dict

    def load(self, data_dict: dict) -> None:
        self.name = data_dict["name"]
        self.cls = data_dict["class"]
        self.race = data_dict["race"]
        self.level = data_dict["level"]
        self.position = eval(data_dict.get("position", "(0, 0)"))
        self.image = data_dict.get("image", "party.png")
