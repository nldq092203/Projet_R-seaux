from enum import IntEnum

# IntEnum: 400 - 499 range

class NetworkCommandsTypes(IntEnum):
    CONNECT = 400
    DISCONNECT = 401
    GAME_SAVE = 402
    ASK_SAVE = 403

    FOOD_MESSAGE = 410
    SPAWN_FOOD = 411
    DELETE_FOOD = 412
    # RISK_UPDATE = 412


    UPDATE_MAP = 430

    BOB_MESSAGE = 420
    SPAWN_BOB = 421
    UPDATE_BOB = 422
    DELETE_BOB = 423
    BORN_BOB = 424
    MOVE_BOB = 425
    EAT_FOOD = 426
    EAT_BOB = 427
    

    DELEGATE = 499