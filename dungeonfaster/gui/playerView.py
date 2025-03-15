import os

from kivy.core.audio import Sound
from kivy.core.window import Window, WindowBase
from kivy.graphics import Rectangle
from kivy.input.motionevent import MotionEvent
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from dungeonfaster.gui.mapView import MapView
from dungeonfaster.model.location import Location
from dungeonfaster.model.map import Map
from dungeonfaster.model.campaign import Campaign

class PlayerView(MapView):

    def __init__(self, screen: Screen, **kwargs):
        super().__init__(screen, **kwargs)
