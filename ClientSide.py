import socket
import time
from threading import Thread
from typing import List

from Common import *


class Client:
    def __init__(self, server_addr: str, server_port: int, name: str, password: str):
        self.name = name
        self.password = password
        self.server_addr = server_addr
        self.server_port = server_port
        self.socket: Optional[socket.socket] = None
        self.thread_receive: Optional[Thread] = None
        self.socket_connected = False
        self.ack: Optional[bool] = None
        self.online_clients: List[str] = list()

    def wait_for_ack(self) -> bool:
        while self.socket_connected:
            if self.ack == AckResult.Success:
                self.ack = None
                return True
            elif self.ack == AckResult.Failed:
                self.ack = None
                return False
            time.sleep(0.1)

    def sign_up(self):
        data = chr(MsgType.SignUp.value).encode() + make_packet(self.name.encode()) + make_packet(self.password.encode())
        self.socket.send(data)
        if self.wait_for_ack():
            print("successfully! update UI here")
            self.ui_update_sign_up(True)
        else:
            print("failed! update UI here")
            self.ui_update_sign_up(False)

    def login(self):
        data = chr(MsgType.LogIn.value).encode() + make_packet(self.name.encode()) + make_packet(self.password.encode())
        self.socket.send(data)
        if self.wait_for_ack():
            print("successfully! update UI here")
            self.ui_update_login(True)
        else:
            print("failed! update UI here")
            self.ui_update_login(False)

    def logout(self):
        data = chr(MsgType.LogOut.value).encode() + make_packet(self.name.encode()) + make_packet(self.password.encode())
        self.socket.send(data)
        if self.wait_for_ack():
            print("successfully! update UI here")
            self.ui_update_logout(True)
        else:
            print("failed! update UI here")
            self.ui_update_logout(False)

    def send_message(self, receiver: str, message: str):
        data = chr(MsgType.LogOut.value).encode() + make_packet(self.name.encode()) + make_packet(receiver.encode()) + make_packet(message.encode())
        self.socket.send(data)
        if self.wait_for_ack():
            print("successfully! update UI here")
        else:
            print("failed! update UI here")

    def send_file(self, receiver: str, file_name: str) -> bool:
        try:
            with open(file_name, "rb") as f:
                d = f.read()
        except Exception as e:
            print(e)
            return False
        segments = [bytearray(chr(0).encode() + d[i:i + MAX_SEG_LEN]) for i in range(0, len(d), MAX_SEG_LEN)]
        segments[0][0] += SEG_START
        segments[len(segments) - 1][0] += SEG_END
        for idx, segment in enumerate(segments):
            segment[0] += idx
            data = chr(MsgType.File.value).encode() \
                   + make_packet(self.name.encode()) \
                   + make_packet(receiver.encode()) \
                   + make_packet(file_name.encode()) \
                   + make_packet(segment)
            self.socket.send(data)
        if self.wait_for_ack():
            print("successfully! update UI here")
        else:
            print("failed! update UI here")
        return True

    def get_list(self):
        data = chr(MsgType.GetList.value).encode()
        self.socket.send(data)

    def socket_connect(self):
        if self.socket_connected:
            return
        self.socket = socket.socket()
        self.socket.connect((self.server_addr, self.server_port))
        self.socket_connected = True
        self.thread_receive = Thread(target=self.receive_from_server)
        self.thread_receive.daemon = True
        self.thread_receive.start()

    def socket_disconnect(self):
        self.socket_connected = False
        if self.thread_receive is not None:
            self.thread_receive.join()
        if self.socket is not None:
            self.socket.close()

    def handle_receive_file(self, sender: str, file_name: str, segment_dhr: int, segment_data: bytes):
        if segment_dhr & SEG_START:
            self.ui_update_start_receive_file(sender, file_name)
        with open(file_name, "ab") as f:
            f.write(segment_data)
        if segment_dhr & SEG_END:
            self.ui_update_complete_receive_file(sender, file_name)

    def receive_from_server(self):
        while self.socket_connected:
            try:
                data = self.socket.recv(MAX_TCP_PKT_LEN)
                msg_type = data[0]
                if msg_type == MsgType.Ack:
                    ack_type = data[1]
                    if ack_type == MsgType.GetList:
                        nb_client = data[2]
                        self.online_clients = list()
                        curr_pos = 3
                        for i in range(nb_client):
                            size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                            curr_pos += 2
                            name = data[curr_pos:curr_pos + size].decode()
                            curr_pos += size
                            self.online_clients.append(name)
                        self.ui_update_list_online()
                    else:  # case SignUp, Login, Logout, Message, File
                        self.ack = data[2]
                elif msg_type == MsgType.Message:
                    curr_pos = 1
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    sender = data[curr_pos:curr_pos + size].decode()
                    curr_pos += size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos = curr_pos + 2 + size
                    message = data[curr_pos:curr_pos + size].decode()
                    self.ui_update_message(sender, message)
                elif msg_type == MsgType.File:
                    curr_pos = 1
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    sender = data[curr_pos:curr_pos + size].decode()
                    curr_pos += size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos = curr_pos + 2 + size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    file_name = data[curr_pos:curr_pos + size].decode()
                    curr_pos += size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    segment_hdr = data[curr_pos]
                    curr_pos += 1
                    segment_data = data[curr_pos:curr_pos+size-1]
                    self.handle_receive_file(sender, file_name, segment_hdr, segment_data)
            except Exception as e:
                print(e)

    def ui_update_sign_up(self, result: bool):
        pass

    def ui_update_login(self, result: bool):
        pass

    def ui_update_logout(self, result: bool):
        pass

    def ui_update_start_receive_file(self, sender: str, file_name: str):
        pass

    def ui_update_complete_receive_file(self, sender: str, file_name: str):
        pass

    def ui_update_list_online(self):
        pass

    def ui_update_message(self, sender: str, message: str):
        pass


if __name__ == "__main__":
    client = Client("127.0.0.1", 8000, "name", "password")
    while True:
        pass
