import os
import socket
import struct
import threading
from select import EPOLLHUP, EPOLLIN, epoll

from dungeonfaster.gui.mapView import MapView
from dungeonfaster.model.campaign import Campaign
from dungeonfaster.networking.comms import Comms


class CampaignServer(Comms):
    map_view: MapView
    campaign: Campaign
    sock: socket.socket
    clients: dict[int, socket.socket]
    thread: threading.Thread
    poller: epoll

    def __init__(self, port=9191):
        self.port = port

        # socket file descriptors to sockets
        self.clients = {}
        # socket to player
        self.players = {}

        self.running = False
        # TODO: Add on_update function arg to Campaign to update parent

    def start_server(self, map_view: MapView):
        self.map_view: MapView = map_view
        self.campaign: Campaign = map_view.campaign
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.listen(5)
        self.running = True

        self.thread = threading.Thread(target=self._run_server, args=())
        self.thread.start()

    def _run_server(self):
        with epoll(sizehint=5) as poller:
            self.poller = poller
            poller.register(self.sock, EPOLLIN | EPOLLHUP)

            while self.running:
                events: list[tuple[int, int]] = poller.poll(0.5)
                for fd, event in events:
                    if fd == self.sock.fileno():
                        if event & EPOLLIN:
                            self._accept_client(self.sock)

                    elif fd in self.clients:
                        if event & EPOLLIN:
                            self._receive_message(self.clients[fd])
                        elif event & EPOLLHUP:
                            self._remove_client(self.clients[fd])

    def _accept_client(self, sock: socket.socket):
        new_client, _ = sock.accept()
        # Receive username:password
        user_buf: bytes = new_client.recv(1028)
        username = user_buf.decode().split(":")[0]

        if username not in [player.name for player in self.campaign.party]:
            print(f"Invalid user name {username}")
            new_client.close()
            return

        with open(self.campaign.path, "rb") as campaign_file:
            campaign_bytes: bytes = campaign_file.read()
            new_client.send(campaign_bytes)

        self.clients[new_client.fileno()] = new_client
        self.players[new_client] = next(player for player in self.campaign.party if player.name == username)
        self.message_buffers[new_client.fileno()] = b""

        self.poller.register(new_client, EPOLLIN | EPOLLHUP)

    def _receive_message(self, sock: socket.socket):
        updates: list[str] = self._receive(sock)
        for update in updates:
            message: list[str] = update.split(":")

            command = message[0]

            if command in ["POS", "INDEX"]:
                self._handle_update(message)
                self._forward_update(sock, update.encode("utf-8"))

            elif command == "FILE":
                print(f"File requested: {message[1]}")
                self._send_file(sock, message[1])

    def _send_file(self, sock: socket.socket, file_path: str):
        abs_path = os.path.join(os.environ["DUNGEONFASTER_PATH"], file_path)

        # Check file exists
        if not os.path.exists(abs_path):
            sock.send(b"\xff\xff\xff\xff")
        else:
            # Get file size and serialize
            size = os.stat(abs_path).st_size
            sock.send(struct.pack("!I", size))
            nsent = 0

            # Read & send loop
            with open(abs_path, "rb") as send_file:
                while nsent < size:
                    send_bytes = send_file.read(min(1024, size - nsent))

                    s = sock.send(send_bytes)
                    if s <= 0:
                        return
                    nsent += s

    def _handle_update(self, message: list[str]):
        command = message[0]
        if command == "POS":
            player: str = message[1]
            pos: tuple[float, float] = eval(message[2])
            # print(f"Updated for {player}: {pos}")
            self.map_view.receive_player_pos(player, pos)
        elif command == "INDEX":
            player: str = message[1]
            index: tuple[int, int] = eval(message[2])
            # print(f"Updated for {player}: {pos}")
            self.map_view.receive_player_index(player, index)

    def _forward_update(self, sock: socket.socket, update: bytes):
        recipients = [client for client in self.clients.values() if client != sock]

        for recipient in recipients:
            recipient.send(update)

    def _remove_client(self, sock: socket.socket):
        sock.close()
        del self.clients[sock.fileno()]
        del self.players[sock]

    def _send_client_update(self, fd: socket.socket):
        pass

    def stop(self):
        self.running = False
        self.sock.close()
        self.poller.close()
        self.thread.join()

    def send_update(self, message: str):
        for _, client in self.clients.items():
            # print(f"Sending update to {fd}")
            client.send(message.encode() + b"|")
