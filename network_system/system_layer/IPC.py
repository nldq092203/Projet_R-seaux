import sysv_ipc
import os

KEY = 199999
PY_TO_C = 1
C_TO_PY = 2

class IPC:
    def __init__(self) -> None:
        self.messageQueue = sysv_ipc.MessageQueue(KEY, sysv_ipc.IPC_CREAT)
        self.message = None
        self.sending_type = PY_TO_C
        self.receiving_type = C_TO_PY

    def encode_msg(self, msg: str):
        return msg.encode('utf-8')
    
    def decode_msg(self):
        return self.msg.decode('utf-8')
    
    def sendToC(self, message: str):
        self.messageQueue.send(self.encode_msg(message), 
                               block = False,
                               type=self.sending_type)
        
    def receiveFromC(self):
        self.message, type_msg = self.messageQueue.receive(type=self.receiving_type)
        return self.decode_msg()