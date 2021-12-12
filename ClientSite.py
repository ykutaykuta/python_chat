import socket
from threading import Thread
from enum import Enum
MSG_MAX_SIZE = 1024
SEPARATE_TOKEN = "#"


class Client:
    class MsgType(Enum):
        REG = 0
        MSG = 1
        DIS = 2
        FIL = 3
    def __init__(self,server_addr:str, server_port:int, name:str, password:str):
        self.name = name
        self.password = password
        self.server_addr = server_addr
        self.server_port = server_port
        self.socket: socket.socket = None
        self.thread_receive: Thread = None
        self.running = False
        self.start()

    def start(self):
        if self.running:
            return
        self.socket = socket.socket()
        self.socket.connect((self.server_addr, self.server_port))
        self.thread_receive = Thread(target=self.receive_from_server)
        self.thread_receive.daemon = True
        self.thread_receive.start()
        self.socket.send(f"{Client.MsgType.REG.name}#{self.name}#{self.password}")

    def stop(self):
        self.running = False
        if self.thread_receive is not None:
            self.thread_receive.join()
        if self.socket is not None:
            self.socket.close()

    def send_to_server(self, msg:str):
        if not self.running:
            print("Client is not connect to server!!!")
            return
        self.socket.send(msg)

    def receive_from_server(self):
        while self.running:
            try:
                msg = self.socket.recv(MSG_MAX_SIZE).decode()
                if msg.startswith("ACK#"):
                    msg = msg[4:]
                    tokens = msg.split(SEPARATE_TOKEN)
                    msg_type = tokens[0]
                    msg_value = tokens[1]
                    if msg_type == Client.MsgType.REG.name:
                        if msg_value == f"{True}":
                            pass
                        else:
                            pass

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
                self.stop()


if __name__ == "__main__":
    client = Client("127.0.0.1", 8000)
    while True:
        pass
