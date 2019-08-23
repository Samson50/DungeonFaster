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

        self.ambient = None
        self.atmosphere = None
        self.combat = None
        self.set_songs()

        self.in_combat = False

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

    def play(self):
        if self.in_combat:
            self.combat.play()
        else:
            self.ambient.play()
            self.atmosphere.play()

    def switch_combat(self):
        if self.in_combat:
            self.in_combat = False
            self.combat.stop()

            self.ambient.play()
            self.atmosphere.play()

        else:
            self.in_combat = True
            self.ambient.stop()
            self.atmosphere.stop()

            self.combat.play()


if __name__ == "__main__":
    print("working")
