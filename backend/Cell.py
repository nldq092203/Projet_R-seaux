from backend.Settings import Settings
from backend.Edible import *
from backend.Bob import *
from backend.Effect import *
from random import *
from network_system.networkCommandsTypes import NetworkCommandsTypes
from network_system.system_layer.SystemAgent import SystemAgent

class Cell:
    def __init__(self, x, y):
        self.bobs = []
        self.edibleObject = None

    # Compare two cells
    def __eq__(self, other):
        if self is other or other is None:
            return False
        if not isinstance(other, Cell):
            return False
        return self.x == other.x and self.y == other.y

    # Hash the cell
    def __hash__(self):
        prime = 31
        result = 1
        result = prime * result + self.coordY
        result = prime * result + self.coordX
        return result

    # Convert the cell to a string
    # def __str__(self):
    #     return f"({self.getX()},{self.getY()})"
    

    # Cell data retrieval methods


    # Check if the cell is empty
    def isEmpty(self):
        return len(self.bobs) == 0 and self.edibleObject is None


    # Cell data manipulation methods


    # Add a Bob object to the cell
    def addBob(self, bob):
        """
        Add a Bob object to the list of bobs.

        Args:
            bob (Bob): The Bob object to be added.
        """
        self.bobs.append(bob)

    # Remove a Bob object from the cell of bobs by its ID
    def removeBob(self, bobID=None, player_id=None):
        if not player_id:
            if bobID is None:
                self.bobs = []
            self.bobs = list(filter(lambda x: x.id != bobID, self.bobs))
        else:
            self.bobs = list(filter(lambda x: x.id != bobID or x.player_id != player_id, self.bobs))
    
    # Add an Edible object to the cell
    def addEdible(self, edibleObject):
        """
        Add an edible object to the cell.

        Args:
            edibleObject (Edible): The edible object to be added.
        """
        # If the cell is empty, add the edible object to the cell
        if self.edibleObject is None:
            self.edibleObject = edibleObject
        # Else, add the value of the edible object to the value of the edible object in the cell
        else:
            self.edibleObject.value += edibleObject.value


    # Cell events methods
        

    # Feed all bobs in the cell
        
    def eat(self, b, edibleObject, list_food_message, list_bob_message):
        """
        This method makes a Bob eat an edible object.

        Args:
            b (Bob): The Bob object that eats the edible object.
            edibleObject (Edible): The edible object that is eaten.
        """
        sys = SystemAgent.get_instance()
        # If the edible object is a food
        if isinstance(edibleObject, Food):
            bobEnergy = b.energy
            if isinstance(edibleObject, EffectFood):
                b.effects.append(edibleObject.effect)
            # The Bob object consumes the food energy
            b.energy = min(b.energyMax, bobEnergy + edibleObject.value)
            edibleObject.value -= b.energy - bobEnergy
            # if edibleObject.value <= 1e-5:
            #     self.edibleObject = None
            self.edibleObject = None
            if not b.other_player_bob:
                sys.send_to_list_food_message(
                    action_type=NetworkCommandsTypes.DELETE_FOOD,
                    list_food_message=list_food_message,
                    position=[b.currentX, b.currentY],
                    energy=0,
                    )
                sys.send_to_list_bob_message(
                    list_bob_message=list_bob_message,
                    action_type=NetworkCommandsTypes.EAT_FOOD,
                    last_position=[b.lastX, b.lastY],
                    position=[b.currentX, b.currentY],
                    mass=b.mass,
                    velocity=b.totalVelocity,
                    energy=b.energy,
                    id=b.id,
                )
            # Set the action of the Bob object to "eat"
            b.action = "eat"

        # If the edible object is a sausage
        elif isinstance(edibleObject, Sausage):                         
            # The Bob object consumes the sausage
            b.ammos = min(b.maxAmmos, b.ammos + edibleObject.value)
            self.edibleObject = None
            # Set the action of the Bob object to "eat"
            b.action = "eat"

    # Make all bobs in the cell eat food or a prey if they are able to
    def feedCellBobs(self, list_food_message, list_bob_message):
        """
        This method feeds the Bob objects in the cell. 
        It first gets the food energy available in the cell and the list of Bob objects. 
        Each Bob object then consumes the energy of another Bob object if the mass ratio is less than a certain threshold. 
        If a Bob object's energy reaches zero, it is removed from the cell. 
        After consuming the energy of another Bob object, the Bob object stops eating. 
        If there is food energy available and the Bob object's energy is less than a maximum energy threshold, 
        the Bob object consumes the food energy.
        """
        # Shuffle the list of Bob objects in the cell
        shuffle(self.bobs)
        my_bobs = list(filter(lambda x: not x.other_player_bob, self.bobs))
        # Make each bob that has not performed any action yet eat
        for bob in my_bobs:
            sys = SystemAgent.get_instance()
            if bob.action == "idle":
                
                # Get the list all other Bobs in the cell
                otherBobs = [otherBob for otherBob in self.bobs if otherBob != bob]

                # If the mass mechanism is enabled, make the Bob eats its prey if there is one in the cell
                if Settings.enableMass:
                    for otherBob in otherBobs:
                        massRatio = otherBob.mass / bob.mass
                        otherBobEnergy = otherBob.energy

                        # If the mass ratio is less than the threshold
                        if massRatio < Settings.massRatioThreshold:
                            # print("Bob has been eaten in send")
                            # The Bob consumes the energy of the other Bob object
                            bob.energy = min(bob.energyMax, otherBobEnergy * .5 * (1 - massRatio))
                            # The other Bob's energy is reduced
                            sys.send_to_list_bob_message(
                                    list_bob_message,
                                    action_type=NetworkCommandsTypes.EAT_BOB,
                                    last_position=[bob.lastX, bob.lastY],
                                    position=[bob.currentX, bob.currentY],
                                    mass=0,
                                    velocity=0,
                                    energy=bob.energy,
                                    id=bob.id, 
                                )
                            sys.send_to_list_bob_message(
                                list_bob_message,
                                action_type=NetworkCommandsTypes.BOB_EATEN,
                                last_position=[otherBob.lastX, otherBob.lastY],
                                position=[otherBob.currentX, otherBob.currentY],
                                mass=0,
                                velocity=0,
                                energy=otherBob.player_id,
                                id=otherBob.id, 
                                )
                            otherBob.action = "eaten"
                            otherBob.energy=0                                

                            # Set the actions of the two Bob objects
                            
                            bob.action = "eat"

                            # print("cannibalism")

                            # The Bob can only eat once per tick so we break the loop
                            break  
                
                # If the Bob has not eaten yet, make it eat the edible object if there is one in the cell
                if self.edibleObject is not None:
                    self.eat(bob, self.edibleObject, list_food_message=list_food_message, list_bob_message=list_bob_message)

    # Split a bob into two bobs, (reproduction by parthenogenesis)
    def split(self, b, list_bob_message):
        """
        This method makes a Bob split into two Bobs.

        Args:
            b (Bob): The Bob object to be split.
        """
        sys = SystemAgent.get_instance()
        # Create a new bob
        bornBob = b.createMonoparentalChild()
        sys.send_to_list_bob_message(
            list_bob_message,
            last_position=[0, 0],
            position=[bornBob.currentX, bornBob.currentY],
            mass=bornBob.mass,
            velocity=bornBob.totalVelocity,
            id=bornBob.id,
            energy=bornBob.energy,
            action_type=NetworkCommandsTypes.BORN_BOB,
        )
        

        # Add the new bob to the cell
        self.addBob(bornBob)

        # Set the action of the parent to "parthenogenesis"
        b.action = "parthenogenesis"

        # Remove SuperMutation effects
        b.effects = [effect for effect in b.effects if not isinstance(effect, SuperMutation)]
        b.mutationFactor = 1

        # Reduce the energy of the parent
        b.incrementEnergy(-Settings.motherEnergy)
        sys.send_to_list_bob_message(
            list_bob_message,
            last_position=[b.lastX, b.lastY],
            position=[b.currentX, b.currentY],
            mass=0,
            velocity=0,
            id=b.id,
            energy=b.energy,
            action_type= NetworkCommandsTypes.PARTHENOGENESIS_BOB,
        )

    # Make two bobs reproduce (sexual reproduction)
    def mate(self, b1, b2, list_bob_message):
        """
        This method makes two Bob mate and creates a new Bob.

        Args:
            b1 (Bob): The first Bob.
            b2 (Bob): The second Bob.
        """
        sys = SystemAgent.get_instance()
        # Create a new bob
        bornBob = Bob.createBiParentalChild(b1, b2)
        sys.send_to_list_bob_message(
            list_bob_message,
            last_position=[0, 0],
            position=[bornBob.currentX, bornBob.currentY],
            mass=bornBob.mass,
            velocity=bornBob.totalVelocity,
            id=bornBob.id,
            energy=bornBob.energy,
            action_type=NetworkCommandsTypes.BORN_BOB,
        )
        # Add the new bob to the cell
        self.addBob(bornBob)
        
        # Set the action of the two parents to "mate"
        b1.action = "love"
        b2.action = "love"
        
        # Remove SuperMutation effects
        b1.effects = [effect for effect in b1.effects if not isinstance(effect, SuperMutation)]
        b2.effects = [effect for effect in b2.effects if not isinstance(effect, SuperMutation)]
        b1.mutationFactor = 1
        b2.mutationFactor = 1

        # Reduce the energy of the bobs
        b1.incrementEnergy(-Settings.matingEnergyConsumption)
        b2.incrementEnergy(-Settings.matingEnergyConsumption)
        
        sys.send_to_list_bob_message(
            list_bob_message,
            last_position=[b1.lastX, b1.lastY],
            position=[b1.currentX, b1.currentY],
            mass=b1.mass,
            velocity=b1.totalVelocity,
            id=b1.id,
            energy=b1.energy,
            action_type=NetworkCommandsTypes.SEXUAL_BOB,
        )
        sys.send_to_list_bob_message(
            list_bob_message,
            last_position=[b2.lastX, b2.lastY],
            position=[b2.currentX, b2.currentY],
            mass=b2.mass,
            velocity=b2.totalVelocity,
            id=b2.id,
            energy=b2.energy,
            action_type=NetworkCommandsTypes.SEXUAL_BOB,
        )

        
    # Make all bobs in the cell reproduce (parthenogenesis or sexual reproduction)
    def reproduceCellBobs(self, list_bob_message):
        """
        This method makes the Bobs in the cell reproduce.
        """
        # If both parthenogenesis and sexual reproduction are disabled, exit the method
        if not(Settings.enableParthenogenesis or Settings.enableSexualReproduction):
            return
        
        my_bobs_list = list(filter(lambda x: not x.other_player_bob, self.bobs))
        
        for bob in my_bobs_list:
            # If the Bob has not performed any action yet
            if bob.action == "idle":
                # Make the Bob reproduce by parthenogenesis if it has enough energy
                if Settings.enableParthenogenesis and bob.energy >= bob.energyMax:
                    self.split(bob, list_bob_message)
                elif Settings.enableSexualReproduction and bob.energy >= Settings.matingEnergyRequirement:
                    # Get the list of Bob objects in the cell
                    otherBobs = [otherBob for otherBob in my_bobs_list if otherBob != bob]
                    # If there is another Bob object in the cell
                    if otherBobs:
                        # Select a random Bob object from the list of Bob objects in the cell
                        otherBob = choice(otherBobs)
                        # If the other Bob object has enough energy to reproduce by parthenogenesis
                        if otherBob.energy >= Settings.matingEnergyRequirement:
                            # The two Bobs mate
                            self.mate(bob, otherBob, list_bob_message)

    # Delete all dead bobs in the cell
    def cleanCellDeadBobs(self, sys, list_bob_message):
        """
        This method decays the Bob objects in the cell. 
        It first gets the list of Bob objects. 
        Each Bob object then loses a certain amount of energy. 
        If a Bob object's energy reaches zero, it is removed from the cell.
        """

        for bob in self.bobs:
            # If a Bob object's energy reaches zero, it is removed from the cell
            if bob.action == "decay":
                if sys:
                    sys.send_to_list_bob_message(
                    list_bob_message=list_bob_message,
                    action_type=NetworkCommandsTypes.DELETE_BOB,
                    last_position=[bob.currentX, bob.currentY],
                    position=[bob.currentX, bob.currentY],
                    mass=0,
                    velocity=0,
                    energy=0,
                    id=bob.id
                    )
                self.removeBob(bob.id)
    
    
    #Apply only for online mode         
    def get_bob_by_id(self, bob_id, player_id = None) -> Bob:
        for b in self.bobs:
            if b.id == bob_id and b.player_id == player_id:
                return b
        return None
