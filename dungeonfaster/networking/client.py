import os
import socket
import threading
from select import EPOLLHUP, EPOLLIN, epoll

from dungeonfaster.gui.playerView import PlayerView
from dungeonfaster.model.campaign import Campaign

USERS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "users")
RECV_SIZE = 256


class CampaignClient:
    campaign: Campaign
    sock: socket.socket
    server: socket.socket
    thread: threading.Thread

    established: bool

    def __init__(self, player_view: PlayerView, name: str):
        self.established = False
        self.running = False

        self.player_view = player_view
        self.username = name
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
                events: list[tuple[int, int]] = poller.poll(0.5)

                for fd, event in events:
                    if fd == self.sock.fileno():
                        if event == EPOLLIN:
                            self._receive_update(self.sock)
                        if event == EPOLLHUP:
                            self._shutdown()

    def _establish_session(self):
        campaign_path = os.path.join(USERS_DIR, f"{self.username}.json")
        print(f"establish {campaign_path}")

        # Send username and password
        self.sock.send(f"{self.username}:password".encode())

        # Receive campaign json from server
        self._receive_campaign(campaign_path)

        self.established = True

    def _receive_campaign(self, campaign_path):
        with open(campaign_path, "wb") as user_file:
            buf = self.sock.recv(RECV_SIZE)
            total = 0
            while len(buf) == RECV_SIZE:
                user_file.write(buf)
                buf = self.sock.recv(RECV_SIZE)
                total += len(buf)

            if total == 0:
                print("closed by server")
                self.running = False
                return

            user_file.write(buf)

            user_file.close()

            # TODO: Receive any missing files

    def _receive_update(self, sock: socket.socket):
        pass

    def send_update(self, update: str):
        pass

    def _shutdown(self):
        pass
