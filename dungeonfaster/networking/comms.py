import socket
from abc import ABC, abstractmethod


class Comms(ABC):
    # Buffers for handling partila messages: socket.fileno() -> bytes
    message_buffers: dict[int, bytes] = {}  # noqa: RUF012

    def _receive(self, sock: socket.socket) -> list[str]:
        buffer = self.message_buffers[sock.fileno()]

        buffer = buffer + sock.recv(1024)
        updates = buffer.decode("utf-8").split("|")
        self.message_buffers[sock.fileno()] = updates[-1].encode("utf-8")

        return updates[:-1]

    @abstractmethod
    def send_update(self, message: str):
        pass

    @abstractmethod
    def stop(self):
        pass
