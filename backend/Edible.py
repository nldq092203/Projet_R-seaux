from backend.Settings import Settings
from backend.Effect import *

class Edible:
    def __init__(self, x, y, value=0):
        self.x = x
        self.y = y
        self.value = value
        
    def set_player_id(self,player_id: int):
        self.player_id = player_id

    def get_player_id(self) -> int:
        return self.player_id

class Food(Edible):
    def __init__(self, x, y, energy=Settings.spawnedFoodEnergy):
        super().__init__(x, y, energy)

class EffectFood(Food):
    def __init__(self, x, y, energy=Settings.spawnedFoodEnergy, effect=None):
        super().__init__(x, y, energy)
        self.effect = effect

class PoisonnedFood(Food):
    pass

class Sausage(Edible):
    def __init__(self, x, y, ammos=Settings.spawnSausagesAmmos):
        super().__init__(x, y, ammos)
