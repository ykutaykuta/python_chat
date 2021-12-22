from enum import Enum


class MsgType(Enum):
    SignUp = 0
    LogIn = 1
    LogOut = 2
    Message = 3
    File = 4
    Ack = 5


a = chr(20)
b = a.encode()
print(a, type(a))
print(b, type(b))
