from IPC import IPC
from actionTypes import (
    AddBobAction,
    RemoveBobAction,
    AddFoodAction,
    ClearFoodAction
)
from NetworkCommandTypes import NetworkCommandTypes
import json

class GameIO:
    def __init__(self) -> None:
        self.ipc = IPC()
    
    def msg_to_action(self, message: str):
        return json.loads(message)
    
    def action_to_msg(self, action):
        return json.dumps(action)
    
    def send_action(self, action):
        msg = self.action_to_msg(action)
        self.ipc.sendToC(msg)

    def receive_action(self):
        msg = self.ipc.receiveFromC()
        return self.msg_to_action(msg)
    
    def send_add_bob(self, player_id: int, x: int, y: int):
        action: AddBobAction = {
            'header': {
                'player_id': player_id,
                'command_code': NetworkCommandTypes.ADD_BOB
            },
            'x': x,
            'y': y
        }
        self.send_action(action)

    def send_remove_bob(self, player_id: int, bob_id: int):
        action: RemoveBobAction = {
            'header': {
                'player_id': player_id,
                'command_code': NetworkCommandTypes.REMOVE_BOB
            },
            'bob_id': bob_id
        }
        self.send_action(action)

    def send_add_food(self, player_id: int, x: int, y: int):
        action: AddFoodAction = {
            'header': {
                'player_id': player_id,
                'command_code': NetworkCommandTypes.ADD_FOOD
            },
            'x': x,
            'y': y
        }
        self.send_action(action)

    def send_clear_food(self, player_id: int):
        action: ClearFoodAction = {
            'header': {
                'player_id': player_id,
                'command_code': NetworkCommandTypes.CLEAR_FOOD
            }
        }
        self.send_action(action)

