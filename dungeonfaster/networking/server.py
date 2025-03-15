

import socket
import threading
from select import epoll, EPOLLIN, EPOLLHUP
import time
from dungeonfaster.model.campaign import Campaign


class CampaignServer:
    campaign: Campaign
    sock: socket.socket
    clients: list[socket.socket]
    thread: threading.Thread

    def __init__(self, port=9191):
        self.port=port

        self.clients = []
        self.running = False
        # TODO: Add on_update function arg to Campaign to update parent

    def start_server(self, campaign: Campaign):
        self.campaign = campaign
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.listen(5)
        self.running = True

        self.thread = threading.Thread(target=self._run_server, args=())
        self.thread.start()

    def _run_server(self):

        with epoll(sizehint=5) as poller:
            poller.register(self.sock, EPOLLIN)

            while self.running:
                events: list[tuple[int, int]] = poller.poll()
                print(f"events: {events}")
                print(f"self.sock: {self.sock}")
                for fd, event in events:
                    if fd == self.sock.fileno():
                        # if event == EPOLLIN:
                        self._accept_client(self.sock)

                    elif fd in [c.fileno() for c in self.clients]:
                        if event == EPOLLIN:
                            self._receive_client_update(fd)
                        elif event == EPOLLHUP:
                            self._remove_client(fd)

                time.sleep(1)

    def _accept_client(self, sock: socket.socket):
        print("accepting")
        new_client, client_addr = sock.accept()
        print("accept cleint")
        # Receive username:password
        user_buf: bytes = new_client.recv(1028)
        username = user_buf.decode().split(":")[0]

        if not username in [player.name for player in self.campaign.party]:
            print(f"Invalid user name {username}")
            new_client.close()
            return
        
        print("sending campaign")
        with open(self.campaign.path, "rb") as campaign_file:
            campaign_bytes: bytes = campaign_file.read()
            new_client.send(campaign_bytes)
        print("sent campaign")

        self.clients.append(new_client)
        # TODO: Register new client


    def _receive_client_update(self, sock: socket.socket):
        pass

    def _remove_client(self, sock: socket.socket):
        pass

    def _send_client_update(self, fd: socket.socket):
        pass
