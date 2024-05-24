
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
    position: list[int, int]
    mass: int
    velocity: int

class FoodMsg(TypedDict):
    position: list[int, int]
    energy: int