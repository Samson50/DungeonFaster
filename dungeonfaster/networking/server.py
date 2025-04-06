import socket
import threading
import time
from select import EPOLLHUP, EPOLLIN, epoll

from kivy.clock import mainthread

from dungeonfaster.gui.mapView import MapView
from dungeonfaster.model.campaign import Campaign


class CampaignServer:
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
                        if event == EPOLLIN:
                            self._receive_client_update(self.clients[fd])
                        elif event == EPOLLHUP:
                            self._remove_client(self.clients[fd])

                time.sleep(0.2)

    def _accept_client(self, sock: socket.socket):
        new_client, _ = sock.accept()
        # Receive username:password
        user_buf: bytes = new_client.recv(1028)
        username = user_buf.decode().split(":")[0]

        print([player.name for player in self.campaign.party])

        if username not in [player.name for player in self.campaign.party]:
            print(f"Invalid user name {username}")
            new_client.close()
            return

        with open(self.campaign.path, "rb") as campaign_file:
            campaign_bytes: bytes = campaign_file.read()
            new_client.send(campaign_bytes)

        self.clients[new_client.fileno()] = new_client
        self.players[new_client] = next(player for player in self.campaign.party if player.name == username)

    @mainthread
    def _receive_client_update(self, sock: socket.socket):
        player = self.players[sock]
        update_str = sock.recv(1024).decode("utf-8")

        if update_str.startswith("POS"):
            new_x = float(update_str.split(":")[1])
            new_y = float(update_str.split(":")[2])
            self.map_view.update_player_pos(player, (new_x, new_y))

    def _remove_client(self, sock: socket.socket):
        print("Removed client")
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
