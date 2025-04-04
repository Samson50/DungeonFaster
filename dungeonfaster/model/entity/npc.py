import os
import shutil
from typing import Any

from dungeonfaster.model.entity.entity import Entity

TOOLS_IMG_DIR = os.path.expanduser("~/Documents/5e.tools/5etools-src/img")
CAMPAIGNS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "campaigns")
CAMP_FILE_DIR = os.path.join(CAMPAIGNS_DIR, "files")


class NPC(Entity):
    saves: dict[str, int]
    skills: dict[str, str]
    passive: int
    traits: dict[str, str]
    action: dict[str, str]

    icon: str

    def load(self, data: dict[str, Any]):
        """
        Standard load-from-campaign file function
        """
        super().load(data)

        self.saves = data.get("saves", {})
        self.skills = data.get("skills", {})
        self.passive = data.get("passive", 10)
        self.icon = data.get("icon")

    def save(self) -> dict[str, Any]:
        data = super().save()

        data["saves"] = self.saves
        data["skills"] = self.skills
        data["passive"] = self.passive
        data["icon"] = self.icon

        return data

    def bestiary_load(self, data: dict[str, Any]):
        """
        Load from a 5e.tools bestiary `.json` file
        """
        super().bestiary_load(data)

        self.saves = data.get("save", {})
        self.skills = data.get("skill", {})
        self.passive = data.get("passive", 10)

        # Get image by tools directory and copy to files
        source = data.get("source")
        if source:
            bestiary_file = os.path.join(TOOLS_IMG_DIR, source, f"{self.name}.webp")
            campaign_file = os.path.join(CAMP_FILE_DIR, f"{self.name}.webp")
            shutil.copyfile(bestiary_file, campaign_file)
            self.icon = campaign_file
