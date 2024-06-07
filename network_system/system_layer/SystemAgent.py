import errno
import json
import os
import socket
import re
import struct
import subprocess
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from typing import Optional, List
from network_system.messageTypes import Header, Message, BobMsg, FoodMsg
from network_system.networkCommandsTypes import NetworkCommandsTypes

class SystemAgent:
    instance = None

    def __init__(self):
        self.message_read = None
        self.message_write = None
        self.connection = None
        self.sock = None
        self.player_id = 0
        self.ip = None

        self.is_online = False

    def init_listen(self):
        # from backend.Grid import Grid

        script_dir = os.path.dirname(os.path.realpath(__file__))
        client_path = os.path.join(script_dir, '../client_c')

        if not os.path.exists(client_path):
            print("Error C client not found, please run `make` before play online")
            return

        socket_address = "/tmp/socket"
        if os.path.exists(socket_address):
            os.remove(socket_address)

        # Create a Unix domain socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Bind the socket
        self.sock.bind(socket_address)

        # Listen for incoming connections
        self.sock.listen(1)

        # Wait for a connection
        print(f"Waiting for a connection on {socket_address}")

        # Run subprocess here to wait connection before lauch it
        # self.ip = input("Enter IP to join room (leave empty to host): ")
        if self.ip:
            print("Join room at IP : ", self.ip)
            c_file = [client_path,self.ip]
        else:
            print("Now you're hosting the game, waiting for connection...")
            c_file = [client_path]

        
        self.pid = subprocess.Popen(c_file)

        connection, client_address = self.sock.accept()
        self.connection = connection

        message = self.read_message(block=True)
        if not message:
            print("error receive C connection")
            return

        if message["header"]["command"] != 400:
            print("bad receive packet")
            return

        self.player_id = message["header"]["player_id"]
        print(f"Found C connection, player id : {self.player_id}")


    def send_message(self, command, id_object, data, id_player=1, encode=True):
        # time.sleep(0.0001)
        if not self.connection:
            print("Error send C connection")
            return

        if encode:
            data = data.encode()

        if data:
            object_size = len(data)

            format_send_types = f"=H H L L {object_size}s"
            sending_message = struct.pack(format_send_types,
                                          self.player_id, command,
                                          object_size,
                                          id_object,
                                          data)

        else:
            format_send_types = f"=H H L L"
            sending_message = struct.pack(format_send_types,
                                          self.player_id, command,
                                          0,
                                          id_object)

        return self.connection.sendall(sending_message)

    def read_message(self,block: bool = False) -> Optional[Message]:
        if self.connection is None:
            return None
        

        header_size = 12
        if not block:
            self.connection.setblocking(0)

        try:
            binary_received_header = self.connection.recv(header_size)
            if binary_received_header == b'':
                return None
        except socket.error as e:
            if e.errno != errno.EAGAIN:
                raise e
            self.connection.setblocking(1)
            return None

        self.connection.setblocking(1)

        header = self.unpack_header(binary_received_header)

        if header["object_size"]:
            binary_received_data = self.connection.recv(header["object_size"], socket.MSG_WAITALL)
            data = self.unpack_data(binary_received_data, header["object_size"])
        else:
            data = None


        self.message_read: Message = {
            "header": header,
            "data": data
        }

        # print(f"in read_message {self.message_read}")
        return self.message_read


    def unpack_data(self, binary_received_data, data_len):
        format = f"={data_len}s"
        #print(format, binary_received_data)
        data = struct.unpack(format, binary_received_data)
        return data
    def unpack_header(self, binary_received_header) -> Header:
        header = struct.unpack("=H H L L", binary_received_header)
        temp_dict = {
            "player_id": header[0],
            "command": header[1],
            "object_size": header[2],
            "id_object": header[3]
        }

        return temp_dict

    def close_socket(self):
        self.connection.close()
        self.sock.close()

    def get_coordinates(self):
        numbers = []
        pattern = r'\d+'
        for word in self.message_read['data'].split():
            matches = re.findall(pattern, word)
            # if word.isdigit():
            if matches:
                numbers.append(int(float(word)))
        return numbers

    @staticmethod
    def get_instance():
        if SystemAgent.instance is None:
            SystemAgent.instance = SystemAgent()
        return SystemAgent.instance

    #..............................................................................#

    def get_is_online(self):
        return self.is_online

    def set_is_online(self, status: bool):
        self.is_online = status

    #..............................................................................#
    def run_subprocess(self) :
        self.init_listen()

        # return output.decode("utf-8")

    #methode pour stoper le process

    def stop_subprocess(self):
        # from backend.Grid import Grid
        self.pid.terminate()
        self.set_is_online(False)
        self.player_id = 0
        # Grid.set_all_player_id(0)
        self.connection = None
#..............................................................................#
    def send_disconnect(self):
        pass

    def recieve_disconnect(self, datas):
        pass


    def recieve_connect(self, datas):
        pass

    def send_game_save(self, game):
        import pickle

        sys = SystemAgent.get_instance()
        serialize_data = pickle.dumps({ 'grid': game.grid,'tickCount': game.tickCount })
        sys.send_message(command=NetworkCommandsTypes.GAME_SAVE, id_object=1, data=serialize_data, encode=False)

    def receive_game_save(self, game):
        import pickle

        message = self.read_message(block=True)
        if message["header"]["command"] != NetworkCommandsTypes.GAME_SAVE:
            return
            
        gameSave = pickle.loads(message["data"][0])
        # print(f"type Grid: {type(gameSave['grid'])}")
        game.grid = gameSave["grid"]
        # print(f"Grid: {game.grid}")
        bobs = game.grid.getAllBobs()
        for b in bobs:
            b.other_player_bob = True
            b.player_id = int(message["header"]["player_id"])
            # print(f"id player: {b.player_id}")
        game.tickCount = gameSave["tickCount"]
        # Grid.save_load()


    def get_ip(self):
        return self.ip

    def set_ip(self,ip: str):
        self.ip = ip

    # def send_bob(self, command: int, last_position: list[int, int], position: list[int, int], mass: int, velocity: int, id: int, energy: float):

    #     msg: BobMsg = {
    #         "last_position": last_position,
    #         "position": position,
    #         "mass": mass,
    #         "velocity": velocity,
    #         "energy": energy,
    #         "id": id
    #     }
        
    #     # print(f"print send bob {msg}")

    #     self.send_message(command, id_object=12, data=json.dumps(msg))

    # def send_food(self, position: list[int, int], energy: int):
    #     msg: FoodMsg = {
    #         "action_type":  NetworkCommandsTypes.SPAWN_FOOD,
    #         "position": position,
    #         "energy": energy,
    #     }
    #     print(FoodMsg)
    #     self.send_message(command=NetworkCommandsTypes.FOOD_MESSAGE, id_object=10, data=json.dumps(msg))
    
    def send_food(self, list_food_message: List, command = NetworkCommandsTypes.FOOD_MESSAGE):
        # print(f"print send bob {msg}")

        self.send_message(command, id_object=12, data=json.dumps(list_food_message))

    
    def send_to_list_food_message(self, list_food_message: List, position: list[int, int], energy: float, action_type: int) -> List:
        msg: BobMsg = {
            "action_type": action_type,
            "position": position,
            "energy": energy,
        }
        list_food_message.append(msg)
        return list_food_message


    def send_to_list_bob_message(self, list_bob_message: List, last_position: list[int, int], position: list[int, int], mass: int, velocity: int, id: int, energy: float, action_type: int) -> List:
        msg: BobMsg = {
            "action_type": action_type,
            "last_position": last_position,
            "position": position,
            "mass": mass,
            "velocity": velocity,
            "energy": energy,
            "id": id
        }
        list_bob_message.append(msg)
        return list_bob_message
        
    def send_bob(self, list_bob_message: List, command = NetworkCommandsTypes.BOB_MESSAGE):
        # print(f"print send bob {msg}")

        self.send_message(command, id_object=13, data=json.dumps(list_bob_message))
    
    def send_bob_and_food(self, list_message: List):
        self.send_message(command=NetworkCommandsTypes.UPDATE_MAP, id_object=15, data=json.dumps(list_message))

    def get_player_id(self) -> int:
        return self.player_id
    #
    #
    # def send_walker_direction_update(self, new_direction, walker_id):
    #     pass
    #
    # def recieve_walker_direction_update(self, datas):
    #     pass
    #
    #
    #
    # def send_spawn_walker(self, pos, walker_type, walker_id):
    #     pass
    #
    # def recieve_spawn_walker(self, datas):
    #     pass
    #
    #
    #
    # def send_delete_walker(self, walker_id):
    #     pass
    #
    # def recieve_delete_walker(self, datas):
    #     pass


# def main():
#     system_agent = SystemAgent.get_instance()
#     system_agent.init_listen()
#     # time.sleep(1)
#     # system_agent.send_bob([1, 2], 3, 4)
#     system_agent.send_bob([5, 5], 1, 1)
#     system_agent.send_bob([10, 10], 2, 2)

#     system_agent.read_message()

# main()