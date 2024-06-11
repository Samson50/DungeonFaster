import os

os.environ["KIVY_AUDIO"] = "ffpyplayer"
os.environ["DUNGEONFASTER_PATH"] = os.path.dirname(os.path.realpath(__file__))

from dungeonfaster.gui.main import DungeonFasterApp

DungeonFasterApp().run()
