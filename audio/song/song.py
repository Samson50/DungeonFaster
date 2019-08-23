import pygame


class Song:
    def __init__(self, file_name, audio_type, environment, path):
        self.path = path

        self.file_name = file_name
        self.track = pygame.mixer.Sound(path + self.file_name)

        self.type = audio_type
        self.environment = environment

    def play(self, combat=False):
        if not combat:
            self.track.play(loops=-1, fade_ms=3000)
        else:
            self.track.play(loops=-1, fade_ms=50)

    def stop(self):
        self.track.stop()

    def volume_down(self):
        volume = self.track.get_volume() * 0.8
        self.track.set_volume(volume)

    def volume_up(self):
        volume = self.track.get_volume() / 0.8
        self.track.set_volume(volume)

    def set_volume(self, volume):
        self.track.set_volume(volume)


if __name__ == "__main__":
    print("working")
