
import os
import socket
import threading
from select import epoll, EPOLLIN, EPOLLHUP

from dungeonfaster.gui.campaignView import CampaignView
from dungeonfaster.gui.playerView import PlayerView
from dungeonfaster.model.campaign import Campaign

USERS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "users")
RECV_SIZE = 256

class CampaignClient:
    campaign: Campaign
    sock: socket.socket
    server: socket.socket
    thread: threading.Thread

    def __init__(self, player_view: PlayerView):
        self.established = False
        self.running = False
        self.player_view = player_view
        # TODO: Add on_update function arg to Campaign to update parent

    def start_client(self, address: tuple[str, int]):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

        self.thread = threading.Thread(target=self._run_client, args=(address))
        self.thread.start()

    def _run_client(self, addr: str, port: int):

        self.sock.connect((addr, port))
        self._establish_session()
        

        with epoll(sizehint=5) as poller:
            poller.register(self.sock, EPOLLIN | EPOLLHUP)

            while self.running:
                events: list[tuple[int, int]] = poller.poll()

                for fd, event in events:
                    if fd == self.sock.fileno():
                        if event == EPOLLIN:
                            self._receive_update(self.sock)
                        if event == EPOLLHUP:
                            self._shutdown()


    def _establish_session(self):
        username = "user1" # TODO: As input
        campaign_path = os.path.join(USERS_DIR, f"{username}.json")

        print("sending username")
        # Send username and password
        self.sock.send(f"{username}:password".encode())

        print("receiving campaign")
        # Receive campaign json from server
        self._receive_campaign(campaign_path)

        self.established = True

    def _receive_campaign(self, campaign_path):
        
        user_file = open(campaign_path, "wb")

        buf = self.sock.recv(RECV_SIZE)
        print("asdf")
        while len(buf) == RECV_SIZE:
            user_file.write(buf)
            print("asdf")
            buf = self.sock.recv(RECV_SIZE)
        user_file.write(buf)

        user_file.close()

        # TODO: Receive any missing files

    def _receive_update(self, sock: socket.socket):
        pass

    def send_update(self, update: str):
        pass

    def _shutdown(self):
        pass
