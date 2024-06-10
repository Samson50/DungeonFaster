#!/usr/bin/python3
import os

os.environ["KIVY_AUDIO"] = "ffpyplayer"
# pip install ffpyplayer

# from location.location import Location
from gui.main import DungeonFasterApp


if __name__ == "__main__":
    DungeonFasterApp().run()
