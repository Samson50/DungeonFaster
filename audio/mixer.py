import json

from audio.song.song import Song

MP3_DIR = "resources/songs/"


class Mixer:
    def __init__(self, playlist_file, path):
        self.path = path

        self.playlist_file = playlist_file
        with open(path + self.playlist_file, 'r') as play_file:
            raw_playlist = play_file.read()
            self.playlist = json.loads(raw_playlist)

        self.volume = 1

        self.ambient = None
        self.atmosphere = None
        self.combat = None
        self.set_songs()

        self.in_combat = False

    def save(self, save_data):
        save_data["volume"] = self.volume

    def load(self, save_data):
        self.volume = save_data["volume"]
        self.set_volume(self.volume)

    def set_songs(self):
        for song in self.playlist:
            current_song = Song(
                song["file"],
                song["type"],
                song["environment"],
                MP3_DIR
            )

            if song["type"] == "ambient":
                self.ambient = current_song
            elif song["type"] == "atmosphere":
                self.atmosphere = current_song
            elif song["type"] == "combat":
                self.combat = current_song
            else:
                raise Exception

    def volume_up(self):
        self.volume = self.volume / 0.8
        self.set_volume(self.volume)

    def volume_down(self):
        self.volume = self.volume * 0.8
        self.set_volume(self.volume)

    def set_volume(self, volume):
        if self.in_combat:
            self.combat.set_volume(volume)
        else:
            self.ambient.set_volume(volume)
            self.atmosphere.set_volume(volume)

    def play(self):
        if self.in_combat:
            self.combat.play()
        else:
            self.ambient.play()
            self.atmosphere.play()
        self.set_volume(self.volume)

    def stop(self):
        if self.in_combat:
            self.combat.stop()
        else:
            self.ambient.stop()
            self.atmosphere.stop()

    def switch_combat(self):
        self.stop()
        self.in_combat = not self.in_combat
        self.play()


if __name__ == "__main__":
    print("working")
