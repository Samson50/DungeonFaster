import os

from kivy.core.audio import SoundLoader, Sound
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from dungeonfaster.gui.utilities import IconButton


class AudioPlayer:
    def __init__(self, playlist: list[Sound]):
        self.playlist = playlist
        self.resume_position = 0
        self.index = 0
        self.volume = 0  # 0.5
        self.started = 0

    def change_playlist(self, playlist: list[Sound]):
        self._stop(self.playlist[self.index])
        self.index = 0
        self.playlist = playlist
        self.play()

    def play(self):
        self.playlist[self.index].play()
        # TODO: Resume isn't working and I don't know why
        if self.resume_position != 0:
            self.playlist[self.index].seek(self.resume_position)
            self.resume_position = 0
        self.playlist[self.index].volume = self.volume
        self.playlist[self.index].bind(on_stop=self._play_next)

    def _play_next(self, instance: Sound):
        self._stop(instance)
        self.index = (self.index + 1) % len(self.playlist)
        self.resume_position = 0
        self.play()

    def play_next(self):
        sound: Sound = self.playlist[self.index]
        self._play_next(sound)

    def _stop(self, sound: Sound) -> None:
        sound.unbind(on_stop=self._play_next)
        sound.stop()

    def pause(self):
        self.resume_position = self.playlist[self.index].get_pos()
        self._stop(self.playlist[self.index])

    def volume_up(self):
        self.volume = self.volume + 0.05
        self.volume = min(self.volume, 1)
        self.playlist[self.index].volume = self.volume

    def volume_down(self):
        self.volume = self.volume - 0.05
        self.volume = max(self.volume, 0)
        self.playlist[self.index].volume = self.volume
