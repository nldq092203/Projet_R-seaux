import json
import pygame
from pygame.locals import *
from random import randint

# import json
import pickle
from datetime import datetime
from os import path, makedirs

from backend.Grid import *
from backend.Settings import Settings
from backend.InputBox import *

from frontend.Map import Map
from frontend.Gui import *
from frontend.DisplayStatsChart import DisplayStatsChart

from network_system.system_layer.SystemAgent import SystemAgent
from network_system.networkCommandsTypes import NetworkCommandsTypes
from backend.Bob import Bob

import ast

class Game:
    instance = None;

    def __init__(self, grid, screenWidth=930, screenHeight=640, dayLimit = 0, noInterface=False):
        
        pygame.init()

        pygame.key.set_repeat(400, 30)
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEMOTION])

        # Time related variables
        self.frameClock = pygame.time.Clock()
        self.tickClock = pygame.time.Clock()
        self.tickCount = 0
        self.dayLimit = dayLimit
        
        # Pause related variables
        self.running = True
        self.render = True
        self.paused = not noInterface # Pause the game if there is an interface, else run it

        # Display related variables
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.renderHeight = False
        self.renderTextures = True
        self.displayStats = True
        self.noInterface = noInterface

        # Stats related variables
        self.followBestBob = False
        self.currentBestBob = None
        self.bobCountHistory = []
        self.bestBobGenerationHistory = []


        # Editor mode related variables
        self.editorMode = False
        self.editorModeType = "bob" # "bob" or "food"
        self.editorModeCoords = None

        # Multiplayer mode related to variables
        self.multiplayerMenu = False
        self.multiplayerMode = False
        self.onlineMode = False
        self.onlineModeType = "bob" # "bob" or "food"
        self.onlineModeCoords = None
        
        self.list_bob_message = []

        
        
        # Grid related variables
        if type(grid) == Grid:
            self.grid = grid
            
            # Map size related variables
            self.mapWidth = self.grid.size
            self.mapHeight = self.grid.size
        
            if not self.noInterface:
                self.map = Map(self, screenWidth, screenHeight)
                self.gui = Gui(self, self.map, screenWidth, screenHeight)
            
            self.gridDict = self.grid.gridDict

        elif type(grid) == str:
            self.loadSaveFile(grid)
        
        

    # main loop
    def run(self):
        """
        Main loop of the game
        If the game is not paused, it launches a tick event every 1/maxTps seconds
        If a day has passed, it launches new day events
        """
        # Initialiser le temps du dernier tick
        last_tick_time = pygame.time.get_ticks()
        alpha = 0
        icon = pygame.image.load("assets/game-icon.png")
        pygame.display.set_icon(icon)
        
        if not self.noInterface:
            icon = pygame.image.load("assets/game-icon.png")
            pygame.display.set_icon(icon)

        if self.grid.dayCount == 0:
            # Populate the grid with random bobs and Food
            self.grid.spawnBobs()
            self.grid.spawnFood()
        if Settings.enableSpitting:
            self.grid.spawnSausages()

        # Game loop
        while self.running:
            # handle events
            self.events()

            if not self.noInterface:            
                # display fps in title
                pygame.display.set_caption('Game of Life - FPS: ' + str(int(self.frameClock.get_fps())))

            # Refresh the frame clock
            self.frameClock.tick(Settings.maxFps)

            if not self.paused:
                sys = None
                if self.onlineMode:
                    sys = SystemAgent.get_instance()
                # Vérifier si suffisamment de temps s'est écoulé depuis le dernier tick
                current_time = pygame.time.get_ticks()
                if current_time - last_tick_time >= 1000 / Settings.maxTps:
                    # Mettre à jour le temps du dernier tick
                    last_tick_time = current_time

                    # Launch new day events
                    if self.tickCount % Settings.dayLength == 0 and (self.dayLimit == 0 or self.grid.dayCount < self.dayLimit):
                        self.grid.newDayEvents()
                    # Launch tick events
                    self.tickCount += 1
                    self.receive_messages()
                    self.grid.newTickEvents()
                    if sys:
                        sys.send_bob(list_bob_message=self.list_bob_message)
                        self.list_bob_message = []
                    

                    # Compute the best bob, update the stats
                    self.currentBestBob = self.grid.getBestBob()
                    if self.currentBestBob is not None:
                        self.bobCountHistory.append(len(self.grid.getAllBobs()))
                        self.bestBobGenerationHistory.append(self.currentBestBob.generation)
                    
                # Calculate alpha, the percentage of the tick that has passed
                alpha = (pygame.time.get_ticks() - last_tick_time) / (1000 / Settings.maxTps)

            if self.noInterface:
                bobCount = len(self.grid.getAllBobs())
                if bobCount == 0:
                    self.running = False
                    self.renderInTerminal()
                    # print("All bobs are dead")
                    continue
                self.renderInTerminal()
                continue

            if self.render:
                self.map.render(alpha)
                self.gui.render(self.map.screen, self.displayStats)


            pygame.display.update()
    
    def renderInTerminal(self):

        if self.tickCount == 0:
            # clear pygame init string, ect
            print('\033[2J', end='')

        gameString = self.grid.__str__()
        gameStringLinesCount = len(gameString.split('\n'))

        # clear terminal
        print(f'\033[{gameStringLinesCount + 3}A\033[2K', end='')

        # print game
        print(gameString, end='')

        # print stats
        print('\n')
        print(f'Tick: {self.tickCount} - Days: {self.grid.dayCount}')
        print(f'Bobs: {len(self.grid.getAllBobs())} - Food: {len(self.grid.getAllEdibleObjects())} ')


    # handle events
    def events(self):
        """
        Handle events
        Currently handles:
            - Quitting the game (by pressing the cross or escape)
            - Pausing the game (by pressing p)
            - Rendering the game (by pressing r)
            - Moving the map (by clicking and dragging)
            - Zooming the map (by scrolling)
        """

        for event in pygame.event.get():
            # Quitting the game (cross)
            if event.type == pygame.QUIT:
                self.running = False
            
            if not self.multiplayerMenu:
                if event.type == pygame.KEYDOWN:
                    # Pausing the game and displaying the pause menu (escape)
                    if event.key == pygame.K_ESCAPE:
                        if self.editorMode:
                            self.gui.displayPauseMenu = not self.gui.displayPauseMenu
                        else:
                            self.paused = not self.paused
                            self.gui.displayPauseMenu = self.paused
                    # Rendering the game (r)
                    if event.key == pygame.K_r:
                        self.render = not self.render
                    # Pausing the game (p)
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                        self.gui.displayPauseMenu = not self.paused
                    # Rendering the height (h)
                    if event.key == pygame.K_h:
                        self.renderHeight = not self.renderHeight
                        self.map.mustReRenderTerrain = True
                    # Rendering the textures (t)
                    if event.key == pygame.K_t:
                        self.renderTextures = not self.renderTextures
                        self.map.mustReRenderTerrain = True
                    # Displaying stats (s)
                    if event.key == pygame.K_s:
                        self.displayStats = not self.displayStats
                    
                    # serialize the game (o)
                    if event.key == pygame.K_o:
                        # self.createSaveFile()
                        DisplayStatsChart(self.tickCount, self.bobCountHistory, self.bestBobGenerationHistory)

            # when scrolling, zoom the map
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.map.zoom()
                elif event.button == 5:  # Scroll down
                    self.map.unzoom()
            
            # when clicking and dragging, move the map
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[0] == 1:
                    self.map.moveMap(event.rel)
            
            # if multiplayer menu is enabled
            if self.multiplayerMenu:
                if event.type == pygame.MOUSEBUTTONUP:
                    if self.gui.ipInputBox.isClicked:
                        self.gui.ipInputBox.active = True
                        self.gui.nameInputBox.active = False
                        self.gui.ipInputBox.isClicked = False 
                    elif self.gui.nameInputBox.isClicked:
                        self.gui.nameInputBox.active = True
                        self.gui.ipInputBox.active = False
                        self.gui.nameInputBox.isClicked = False
                        
                if event.type == pygame.KEYDOWN:
                    if self.gui.ipInputBox.active:
                        # self.gui.nameInputBox.active = False
                        self.gui.ipInputBox.handle_event(event, True)
                    elif self.gui.nameInputBox.active:
                        # self.gui.ipInputBox.active = False
                        self.gui.nameInputBox.handle_event(event, True)                
            
            
            # if online mode is enabled
            if self.onlineMode:
                sys = SystemAgent.get_instance()

                if self.gui.displayPauseMenu:
                    if self.map.highlightedTile is not None:
                        self.map.highlightedTile = None
                        self.map.mustReRenderTerrain = True
                    continue

                if event.type == pygame.MOUSEMOTION: # event.type == pygame.MOUSEBUTTONDOWN:
                    self.onlineModeCoords = self.map.getCoordsFromPosition(*event.pos)

                    if self.onlineModeCoords is None:
                        continue

                    if event.buttons[0] == 1:
                        if self.onlineModeType == "bob":
                            print("Spawn bob")
                            Bob.id_bob_origin += 1
                            bob = Bob(self.onlineModeCoords[0], self.onlineModeCoords[1], id_bob=Bob.id_bob_origin, player_id=int(SystemAgent.get_instance().player_id))
                            self.grid.addBob(bob)
                            self.list_bob_message = sys.send_to_list_bob_message(
                                         list_bob_message=self.list_bob_message,
                                         action_type=NetworkCommandsTypes.SPAWN_BOB,
                                         last_position= [0, 0],
                                         position=[self.onlineModeCoords[0], self.onlineModeCoords[1]],
                                         mass=Settings.spawnMass,
                                         velocity=Settings.spawnVelocity,
                                         energy=Settings.spawnEnergy,
                                         id=bob.id)
                            sys.send_bob(self.list_bob_message)
                            self.list_bob_message = []
                            
                            
                        elif self.onlineModeType == "food":
                            self.grid.addEdible(Food(self.onlineModeCoords[0], self.onlineModeCoords[1]))
                    
                    if event.buttons[2] == 1:
                        if self.onlineModeType == "bob":
                            self.grid.removeAllBobsAt(*self.onlineModeCoords)
                        elif self.onlineModeType == "food":
                            self.grid.removeFoodAt(*self.onlineModeCoords)

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if self.onlineModeCoords is None:
                        continue

                    if event.button == 1:
                        if self.onlineModeType == "bob":
                            print("Spawn bob")
                            Bob.id_bob_origin += 1
                            bob = Bob(self.onlineModeCoords[0], self.onlineModeCoords[1], id_bob=Bob.id_bob_origin, player_id=int(SystemAgent.get_instance().player_id))
                            self.grid.addBob(bob)
                            self.list_bob_message = sys.send_to_list_bob_message(action_type=NetworkCommandsTypes.SPAWN_BOB,
                                         last_position= [0, 0],
                                         position=[self.onlineModeCoords[0], self.onlineModeCoords[1]],
                                         mass=Settings.spawnMass,
                                         velocity=Settings.spawnVelocity,
                                         energy=Settings.spawnEnergy,
                                         id=bob.id)
                            sys.send_bob(self.list_bob_message)
                            self.list_bob_message = []

                        elif self.onlineModeType == "food":
                            self.grid.addEdible(Food(self.onlineModeCoords[0], self.onlineModeCoords[1]))

                        print(f'Adding {self.onlineModeType} at {self.onlineModeCoords}')
                    if event.button == 3:

                        if self.onlineModeType == "bob":
                            self.grid.removeAllBobsAt(*self.onlineModeCoords)
                        elif self.onlineModeType == "food":
                            self.grid.removeFoodAt(*self.onlineModeCoords)

                        print(f'Removing {self.onlineModeType} at {self.onlineModeCoords}')

            
            # if editing mode is enabled, check for clicks on the map and edit the grid accordingly
            if self.editorMode:

                if self.gui.displayPauseMenu:
                    if self.map.highlightedTile is not None:
                        self.map.highlightedTile = None
                        self.map.mustReRenderTerrain = True
                    continue

                if event.type == pygame.MOUSEMOTION: # event.type == pygame.MOUSEBUTTONDOWN:
                    self.editorModeCoords = self.map.getCoordsFromPosition(*event.pos)

                    if self.editorModeCoords is None:
                        continue

                    if event.buttons[0] == 1:
                        if self.editorModeType == "bob":
                            self.grid.addBob(Bob(self.editorModeCoords[0], self.editorModeCoords[1]))
                        elif self.onlineModeType == "food":
                            self.grid.addEdible(Food(self.onlineModeCoords[0], self.onlineModeCoords[1]))
                    
                    if event.buttons[2] == 1:
                        if self.editorModeType == "bob":
                            self.grid.removeAllBobsAt(*self.editorModeCoords)
                        elif self.editorModeType == "food":
                            self.grid.removeFoodAt(*self.editorModeCoords)

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if self.editorModeCoords is None:
                        continue

                    if event.button == 1:
                        if self.editorModeType == "bob":
                            self.grid.addBob(Bob(self.editorModeCoords[0], self.editorModeCoords[1]))
                        elif self.editorModeType == "food":
                            self.grid.addEdible(Food(self.editorModeCoords[0], self.editorModeCoords[1]))

                        print(f'Adding {self.editorModeType} at {self.editorModeCoords}')
                    if event.button == 3:

                        if self.editorModeType == "bob":
                            self.grid.removeAllBobsAt(*self.editorModeCoords)
                        elif self.editorModeType == "food":
                            self.grid.removeFoodAt(*self.editorModeCoords)

                        print(f'Removing {self.editorModeType} at {self.editorModeCoords}')
                    
            if event.type == pygame.VIDEORESIZE:
                # There's some code to add back window content here.
                self.screenWidth = event.w
                self.screenHeight = event.h

                self.map.resize(event.w, event.h)
                self.gui.resize(event.w, event.h)

    def createSaveFile(self, pathToSaveFolder='saves', saveName=None):
        """
        Serialize the game and save it in a json file at the given path.
        Can't be used when the game is running.
        """
        if not self.paused:
            raise Exception("Can't serialize a game that is not paused")
        
        if saveName is None:
            saveName = datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".save"
        
        if not path.exists(pathToSaveFolder):
            makedirs(pathToSaveFolder)

        with open(path.join(pathToSaveFolder, saveName), 'wb') as f:
            pickle.dump({ 'grid': self.grid, 'settings': Settings.getSettings(), 'tickCount': self.tickCount }, f, pickle.HIGHEST_PROTOCOL)

        print("Game saved as " + saveName)

        return saveName

    def loadSaveFile(self, pathToSaveFile):
        with open(pathToSaveFile, 'rb') as f:
            try:
                data = pickle.load(f)
            except:
                print("Error while loading save file")
                return False

        self.grid = data['grid']

        Settings.setSettings(data['settings'])
        
        self.tickCount = data['tickCount']

        # Map size related variables
        self.mapWidth = self.grid.size
        self.mapHeight = self.grid.size
    
        if not self.noInterface:
            self.map = Map(self, self.screenWidth, self.screenHeight)
            self.gui = Gui(self, self.map, self.screenWidth, self.screenHeight)
            
        self.gridDict = self.grid.gridDict

        self.paused = True
        self.gui.displayPauseMenu = True
        
        print("Game loaded from " + pathToSaveFile)

        return True

    @staticmethod
    def get_instance():
        if Game.instance is None:
            Game.instance = Game()
        return Game.instance
    
    def receive_messages(self):
        sys = SystemAgent.get_instance()
        print(f"my id : {sys.player_id}")
     
        messages = sys.read_message()
        header = None
        if messages:
            header = messages["header"]
        
        if not header:
            return
        
        if (header["command"] == NetworkCommandsTypes.ASK_SAVE):
            sys.send_game_save(game = self)
            
        for messageReceived in messages["data"]:
            print(f"data: {messages['data']}")
            if messageReceived:
                # data =  messageReceived["data"][0]
                data = messageReceived.decode()
                # data = json.loads(data)
                data = ast.literal_eval(data)
                match(header["command"]):
                    case NetworkCommandsTypes.BOB_MESSAGE:
                        match(data["action_type"]):
                            case NetworkCommandsTypes.SPAWN_BOB:
                                bob = Bob(x=data["position"][0], 
                                        y=data["position"][1], 
                                        mass=data["mass"], 
                                        totalVelocity=data["velocity"],
                                        energy=data["energy"],
                                        id_bob=int(data["id"]),
                                        player_id=int(header["player_id"]),
                                        )
                                bob.action = "idle"
                                bob.other_player_bob = True
                                # self.bob_dict[(int(header["player_id"]), int(data["id"]))] = bob
                                self.grid.addBob(bob)
                                
                            case NetworkCommandsTypes.DELETE_BOB:
                                self.grid.removeBob(bobID=data["id"], player_id=int(header["player_id"]))
                                
                                
                            case NetworkCommandsTypes.MOVE_BOB:
                                # bobs = self.grid.getAllBobs()
                                # other_player_bobs = list(filter(lambda x: x.other_player_bob == True, bobs))
                                # for bob in other_player_bobs:
                                #     if bob.id == int(data["id"]) and bob.player_id == int(header["player_id"]):
                                #         bob.action = "idle"
                                #         self.grid.moveBobTo(bob, int(data["position"][0]), int(data["position"][1]))
                                #         break
                                # bob = self.grid.bob_dict[(int(header["player_id"]), int(data["id"]))]
                                # self.grid.moveBobTo(bob, int(data["position"][0]), int(data["position"][1])   
                                
                                # cell = self.grid.getCellAt(x=int(data["last_position"][0]),y=int(data["last_position"][1]))
                                # bobs_at_position = self.grid.getBobsAt(x=int(data["last_position"][0]),y=int(data["last_position"][1]))
                                bob = None
                                # for b in bobs_at_position:
                                #     if b.player_id == int(header["player_id"]) and b.id == int(data["id"]):
                                #         bob = b
                                #         break
                                bobs = self.grid.getAllBobs()
                                print(hex(id(self.grid)))
                                print(f"All bobs: {bobs}")
                                for b in bobs:
                                    print(f"bob: {b.id} {b.player_id}")
                                    print(f"id player: {header['player_id']}")
                                    print(f"id bob: {data['id']}")
                                    if b.player_id == int(header["player_id"]) and b.id == int(data["id"]):
                                        bob = b
                                        break
                                # print(f"Cell:{cell}")
                                # bob = cell.get_bob_by_id(bob_id=data["id"], player_id = int(header["player_id"])
                                #     )
                                # self.grid.moveBobTo(bob, int(data["position"][0]), int(data["position"][1]))
                                if bob:
                                    self.grid.moveBobTo(bob, int(data["position"][0]), int(data["position"][1]))
                            case NetworkCommandsTypes.FOOD_MESSAGE:
                                match(data["action_type"]):
                                    case NetworkCommandsTypes.SPAWN_FOOD:
                                        self.grid.addEdible(Food(data["position"][0], data["position"][1]))
                                        
                                    case NetworkCommandsTypes.DELETE_FOOD:
                                        self.grid.removeFoodAt(data["position"][0], data["position"][1])

