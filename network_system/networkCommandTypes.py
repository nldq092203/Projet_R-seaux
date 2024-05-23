from enum import IntEnum

# IntEnum: 400 - 499 range

class NetworkCommandTypes(IntEnum):
    CONNECT = 400
    DISCONNECT = 401
    GAME_SAVE = 402
    ASK_SAVE = 403

    ADD_BOB = 410
    ADD_FOOD = 411
    DELETE_FOOD = 412