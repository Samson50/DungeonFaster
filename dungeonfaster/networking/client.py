import os
import socket
import threading
from select import EPOLLHUP, EPOLLIN, epoll

from dungeonfaster.gui.mapView import MapView
from dungeonfaster.model.campaign import Campaign
from dungeonfaster.networking.comms import Comms

USERS_DIR = os.path.join(os.environ["DUNGEONFASTER_PATH"], "users")
RECV_SIZE = 256


class CampaignClient(Comms):
    campaign: Campaign
    sock: socket.socket
    server: socket.socket
    thread: threading.Thread

    established: bool

    def __init__(self, player_view: MapView, name: str):
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
                        if event & EPOLLIN:
                            self._receive_update(self.sock)
                        if event & EPOLLHUP:
                            self._shutdown()

    def _establish_session(self):
        campaign_path = os.path.join(USERS_DIR, f"{self.username}.json")

        # Send username and password
        self.sock.send(f"{self.username}:password".encode())

        # Receive campaign json from server
        self._receive_campaign(campaign_path)

        self.message_buffers[self.sock.fileno()] = b""

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
        updates = self._receive(sock)
        for update in updates:
            message: list[str] = update.split(":")

            command = message[0]

            if command == "POS":
                player: str = message[1]
                pos: tuple[float, float] = eval(message[2])
                # print(f"Updated for {player}: {pos}")
                self.player_view.receive_player_pos(player, pos)
            if command == "INDEX":
                player: str = message[1]
                index: tuple[int, int] = eval(message[2])
                # print(f"Updated for {player}: {pos}")
                self.player_view.receive_player_index(player, index)

    def send_update(self, message: str):
        self.sock.send(message.encode() + b"|")

    def stop(self):
        pass
