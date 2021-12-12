import socket
from enum import Enum
from threading import Thread

MSG_MAX_SIZE = 1024
SEPARATE_TOKEN = "#"


class Server:
    class MsgType(Enum):
        REG = 0
        MSG = 1
        DIS = 2
        FIL = 3

    def __init__(self, port: int = 8000, max_client: int = 10):
        self.port = port
        self.max_client = max_client
        self.clients = dict()
        self.socket: socket.socket = None
        self.thread_accept: Thread = None
        self.running: bool = False
        self.start()

    def start(self):
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("0.0.0.0", self.port))
        self.socket.listen(self.max_client)
        self.running = True
        self.thread_accept = Thread(target=self.accept_loop())
        self.thread_accept.daemon = True
        self.thread_accept.start()

    def stop(self):
        self.running = False
        if self.thread_accept is not None:
            self.thread_accept.join()

    def accept_loop(self):
        while self.running:
            client_socket, client_addr = self.socket.accept()
            print(f"New client connected: {client_addr}")
            thread_receive = Thread(target=self.read_from_client, args=(client_socket,))
            thread_receive.daemon = True
            thread_receive.start()

    def send_to_client(self, received_socket: socket.socket, message: str):
        received_socket.send(message)

    def send_ack(self, client: socket.socket, msg_type: MsgType, value: bool):
        client.send(f"ACK#{msg_type.name}#{value}")

    def read_from_client(self, client: socket.socket):
        while True:
            try:
                msg = client.recv(MSG_MAX_SIZE).decode()
                if msg.startswith("REG#"):
                    msg = msg[4:]
                    tokens = msg.split("#")
                    client_name = tokens[0]
                    client_pass = tokens[1]
                    if client_name not in self.clients:
                        self.clients.update({client_name: (client, client_pass)})
                        self.send_ack(client, Server.MsgType.REG, True)
                    else:
                        self.send_ack(client, Server.MsgType.REG, False)

                elif msg.startswith("MSG#"):
                    # TODO
                    pass
                elif msg.startswith("DIS#"):
                    # TODO
                    pass
                elif msg.startswith("FIL#"):
                    # TODO
                    pass
            except Exception as e:
                print(e)
                self.clients.remove(client)


if __name__ == "__main__":
    server = Server()
