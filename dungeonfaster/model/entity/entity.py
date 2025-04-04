from typing import Any


STAT_STR = "str"
STAT_DEX = "dex"
STAT_CON = "con"
STAT_INT = "int"
STAT_WIS = "wis"
STAT_CHA = "cha"


class Entity:
    name: str
    size: str
    race: str
    alignment: list[str]

    armor_class: int
    hit_points: int
    speed: dict[str, int]

    strength: int
    constitution: int
    dexterity: int
    intelligence: int
    wisdom: int
    charisma: int

    languages: list[str]

    def load(self, data: dict[str, Any]) -> None:
        self.name = data.get("name", "Unknown")
        self.size = data.get("size", "M")
        self.race = data.get("race", "Unknown")
        self.alignment = data.get("alignment", ["U"])

        self.armor_class = data.get("ac", 13)
        self.hit_points = data.get("hp")
        self.speed = data.get("speed", {"walk": 30})

        self.strength = data.get(STAT_STR)
        self.dexterity = data.get(STAT_DEX)
        self.constitution = data.get(STAT_CON)
        self.intelligence = data.get(STAT_INT)
        self.wisdom = data.get(STAT_WIS)
        self.charisma = data.get(STAT_CHA)

        self.languages = data.get("languages", ["Common"])

    def save(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "race": self.race,
            "alignment": self.alignment,
            "ac": self.armor_class,
            "hp": self.hit_points,
            "speed": self.speed,
            STAT_STR: self.strength,
            STAT_DEX: self.dexterity,
            STAT_CON: self.constitution,
            STAT_INT: self.intelligence,
            STAT_WIS: self.wisdom,
            STAT_CHA: self.charisma,
            "languages": self.languages,
        }

    def bestiary_load(self, data: dict[str, Any]) -> None:
        self.name = data.get("name", "Unknown")
        self.size = data.get("size", "M")
        self.race = data.get("type", "Unknown")
        self.alignment = data.get("alignment", ["U"])

        self.armor_class = data.get("ac", [{"ac": 13, "from": "natural armor"}])[0]["ac"]
        self.hit_points = data.get("hp", {"average": None})["average"]
        self.speed = data.get("speed", {"walk": 30})

        self.strength = data.get(STAT_STR)
        self.dexterity = data.get(STAT_DEX)
        self.constitution = data.get(STAT_CON)
        self.intelligence = data.get(STAT_INT)
        self.wisdom = data.get(STAT_WIS)
        self.charisma = data.get(STAT_CHA)

        self.languages = data.get("languages", ["Common"])
