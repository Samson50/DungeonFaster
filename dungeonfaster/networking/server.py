

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
    poller: epoll

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
            self.poller = poller
            poller.register(self.sock, EPOLLIN | EPOLLHUP)

            while self.running:
                events: list[tuple[int, int]] = poller.poll(0.5)
                for fd, event in events:
                    if fd == self.sock.fileno():
                        if event & EPOLLIN:
                            self._accept_client(self.sock)

                    elif fd in [c.fileno() for c in self.clients]:
                        if event == EPOLLIN:
                            self._receive_client_update(fd)
                        elif event == EPOLLHUP:
                            self._remove_client(fd)

                time.sleep(0.2)

    def _accept_client(self, sock: socket.socket):
        new_client, client_addr = sock.accept()
        # Receive username:password
        user_buf: bytes = new_client.recv(1028)
        username = user_buf.decode().split(":")[0]

        if not username in [player.name for player in self.campaign.party]:
            print(f"Invalid user name {username}")
            new_client.close()
            return
        
        with open(self.campaign.path, "rb") as campaign_file:
            campaign_bytes: bytes = campaign_file.read()
            new_client.send(campaign_bytes)

        self.clients.append(new_client)
        # TODO: Register new client


    def _receive_client_update(self, sock: socket.socket):
        pass

    def _remove_client(self, sock: socket.socket):
        pass

    def _send_client_update(self, fd: socket.socket):
        pass

    def stop(self):
        self.running = False
        self.sock.close()
        self.poller.close()
        self.thread.join()
