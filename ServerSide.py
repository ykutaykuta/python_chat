import multiprocessing
import socket
import sqlite3
from threading import Thread

from typing import Tuple

from Common import *


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect("database.db")
        if self.conn is None:
            print("Can not create database connection!!!")
            exit(1)
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS user (name text PRIMARY KEY, pass_word text NOT NULL);")

    def insert_user(self, name: str, passwd: str) -> bool:
        try:
            self.conn.execute(f"INSERT INTO user (name,pass_word) VALUES ({name},{passwd})")
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(e)
            return False

    def select_user(self, name: str) -> Tuple:
        cursor = self.conn.execute(f"SELECT name, pass_word from user WHERE name = {name}")
        row = cursor.fetchone()
        if row is None:
            return None, None
        return row['name'], row['pass_word']


class Server:
    def __init__(self, port: int = 8000, max_client: int = 10):
        self.db: DataBase = DataBase()
        self.port = port
        self.max_client = max_client
        self.clients = dict()
        self.socket: Optional[socket.socket] = None
        self.thread_accept: Optional[multiprocessing.Process] = None
        self.running: bool = False
        self.start()

    def start(self):
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("0.0.0.0", self.port))
        self.socket.listen(self.max_client)
        self.running = True
        self.thread_accept = multiprocessing.Process(target=self.accept_loop)
        self.thread_accept.daemon = True
        self.thread_accept.start()

    def stop(self):
        self.running = False
        if self.thread_accept is not None:
            self.thread_accept.terminate()

    def accept_loop(self):
        while self.running:
            client_socket, client_addr = self.socket.accept()
            print(f"New client connected: {client_addr}")
            thread_receive = Thread(target=self.read_from_client, args=(client_socket,))
            thread_receive.daemon = True
            thread_receive.start()

    @staticmethod
    def send_data(received_socket: socket.socket, data: bytes):
        received_socket.send(data)

    def send_ack(self, received_socket: socket.socket, msg_type: MsgType, value: bool = True):
        data = chr(msg_type.value).encode()
        if msg_type == MsgType.GetList:
            data + chr(len(self.clients)).encode()
            for client in self.clients:
                data += make_packet(client)
        else:
            if value:
                data += chr(1).encode()
            else:
                data += chr(0).encode()
        data = chr(MsgType.Ack.value).encode() + data
        received_socket.send(data)

    def read_from_client(self, sock: socket.socket):
        while True:
            try:
                data = sock.recv(Define.MAX_TCP_PKT_LEN)
                msg_type = data[0]
                curr_pos = 1
                if msg_type == MsgType.SignUp:
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    name = data[curr_pos:curr_pos + size].decode()
                    curr_pos += size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    passwd = data[curr_pos:curr_pos + size].decode()
                    if self.db.insert_user(name, passwd):
                        self.clients.update({name: sock})
                        self.send_ack(sock, MsgType.SignUp, True)
                    else:
                        self.send_ack(sock, MsgType.SignUp, False)
                elif msg_type == MsgType.LogIn:
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    name = data[curr_pos:curr_pos + size].decode()
                    curr_pos += size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    passwd = data[curr_pos:curr_pos + size].decode()
                    _name, _passwd = self.db.select_user(name)
                    if _passwd is None or _passwd != passwd:
                        self.send_ack(sock, MsgType.LogIn, False)
                    else:
                        self.clients.update({name: sock})
                        self.send_ack(sock, MsgType.LogIn, True)
                elif msg_type == MsgType.LogOut:
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    name = data[curr_pos:curr_pos + size].decode()
                    curr_pos += size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    passwd = data[curr_pos:curr_pos + size].decode()
                    _name, _passwd = self.db.select_user(name)
                    if _passwd is None or _passwd != passwd or _name not in self.clients:
                        self.send_ack(sock, MsgType.LogOut, False)
                    else:
                        self.clients.pop(name)
                        self.send_ack(sock, MsgType.LogIn, True)
                elif msg_type == MsgType.Message or msg_type == MsgType.File:
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos = curr_pos + 2 + size
                    size = int.from_bytes(data[curr_pos:curr_pos + 2], byteorder='big')
                    curr_pos += 2
                    receiver = data[curr_pos:curr_pos + size].decode()
                    if receiver in self.clients:
                        receiver_sock = self.clients[receiver]
                        self.send_data(receiver_sock, data)
                        self.send_ack(sock, MsgType.Message, True)
                    else:
                        self.send_ack(sock, MsgType.Message, False)
                elif msg_type == MsgType.GetList:
                    self.send_ack(sock, MsgType.Message)
            except Exception as e:
                print(e)


def main():
    server = Server()
    while True:
        try:
            pass
        except KeyboardInterrupt:
            server.stop()
            print("Ctrl-C or alike was pressed!!!")


if __name__ == "__main__":
    main()
