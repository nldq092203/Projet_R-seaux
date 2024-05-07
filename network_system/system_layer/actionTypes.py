from typing import TypedDict, Optional

class Header(TypedDict):
    player_id: int
    command_code: int

class AddBobAction(TypedDict):
    header: Header
    x: int
    y: int
    
class RemoveBobAction(TypedDict):
    header: Header
    bob_id: int

class AddFoodAction(TypedDict):
    header: Header
    x: int
    y: int

class ClearFoodAction(TypedDict):
    header: Header

