from enum import Enum
from typing import Optional

MAX_TCP_PKT_LEN = 65535
MAX_NAME_LEN = 25
MAX_PASS_LEN = 25
MAX_SEG_LEN = 10240
SEG_START = 0x80
SEG_END = 0x40


class MsgType(Enum):
    SignUp = 0
    LogIn = 1
    LogOut = 2
    Message = 3
    File = 4
    GetList = 5
    Ack = 6


class AckResult(Enum):
    Success = 0
    Failed = 1


def make_packet(data: bytes) -> Optional[bytes]:
    size = len(data)
    if size > MAX_SEG_LEN:
        print(f"Size limit {MAX_SEG_LEN} bytes")
        return None
    return size.to_bytes(size, byteorder='big') + data


def verify_cb(conn, cert, errnum, depth, ok):
    print(f'Got certificate: {cert.get_subject()}')
    return ok
