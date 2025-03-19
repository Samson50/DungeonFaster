from kivy.uix.screenmanager import Screen

from dungeonfaster.gui.mapView import MapView


class PlayerView(MapView):
    def __init__(self, screen: Screen, **kwargs):
        super().__init__(screen, **kwargs)
