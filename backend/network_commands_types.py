from enum import IntEnum

# IntEnum: 400 - 499 range

class NetworkCommandsTypes(IntEnum):
    CONNECT = 400
    DISCONNECT = 401
    GAME_SAVE = 402
    ASK_SAVE = 403

    SPAWN_FOOD = 410
    DELETE_FOOD = 411
    # RISK_UPDATE = 412

    SPAWN_BOB = 420
    UPDATE_BOB = 421
    DELETE_BOB = 422

    DELEGATE = 499