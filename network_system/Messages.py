from typing import TypedDict, Optional

class Header(TypedDict):
    player_id: int
    command: int
    object_size: int
    id_object: int

class Message(TypedDict):
    header: Header
    data: any

