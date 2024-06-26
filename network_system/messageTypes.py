
from typing import TypedDict

class Header(TypedDict):
    player_id: int
    command: int
    object_size: int
    id_object: int

class Message(TypedDict):
    header: Header
    data: any


class BobMsg(TypedDict):
    action_type: int
    last_position: list[int, int]
    position: list[int, int]
    mass: int
    velocity: int
    energy: float
    id: int

class FoodMsg(TypedDict):
    action_type: int
    position: list[int, int]
    energy: int