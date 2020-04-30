import pygame as pg
import random
import sys
import string
from os import path
from settings import *
from player import *
from AI import *
from bomb import *
from powerups import *
from blocks import *

class Game(object):
    def __init__(self):
        # initialize game window, etc.
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        pg.key.set_repeat(500, 100)
        self.running = True
        self.playing = True
        self.loadData()
        self.fontName = pg.font.match_font('stentigattf')
    
    #sprites from https://gamedevelopment.tutsplus.com/articles/enjoy-these-totally-free-bomberman-inspired-sprites--gamedev-8541
    #             https://www.deviantart.com/supastarfox/art/Bomberboy-NES-Bomberman-Sprites-828515704
    #             https://opengameart.org/content/bomb-party-expansion 
    def loadData(self):
        gameFolder = path.dirname(__file__)
        imgFolder = path.join(gameFolder, 'img')
        self.flashscreen = pg.image.load(path.join(imgFolder, 'flashscreen.png')).convert_alpha()
        self.flashscreen = pg.transform.scale(self.flashscreen, (WIDTH, HEIGHT))
        self.bgImg = pg.image.load(path.join(imgFolder, 'background.png')).convert_alpha()
        self.bgImg = pg.transform.scale(self.bgImg, (WIDTH, HEIGHT))
        self.solidBlImg = pg.image.load(path.join(imgFolder, 'SolidBlock.png')).convert_alpha()
        self.explodableBlImg = pg.image.load(path.join(imgFolder, 'ExplodableBlock.png')).convert_alpha()
        explFrames = [pg.image.load(path.join(imgFolder, 'flame0.png')).convert_alpha(),
                    pg.image.load(path.join(imgFolder, 'flame1.png')).convert_alpha(),
                    pg.image.load(path.join(imgFolder, 'flame2.png')).convert_alpha(),
                    pg.image.load(path.join(imgFolder, 'flame3.png')).convert_alpha(),
                    pg.image.load(path.join(imgFolder, 'flame4.png')).convert_alpha()]
        self.explFrames = []
        for frame in explFrames:
            frame = pg.transform.scale(frame, (45, 40))
            self.explFrames.append(frame)
        self.bombPowerupImg = pg.image.load(path.join(imgFolder, 'BombPowerup.png')).convert_alpha()
        self.speedPowerupImg = pg.image.load(path.join(imgFolder, 'SpeedPowerup.png')).convert_alpha()
        self.flamePowerupImg = pg.image.load(path.join(imgFolder, 'FlamePowerup.png')).convert_alpha()
        playerImgs = [pg.image.load(path.join(imgFolder, 'player1.png')).convert_alpha(),
                      pg.image.load(path.join(imgFolder, 'player2.png')).convert_alpha(),
                      pg.image.load(path.join(imgFolder, 'player3.png')).convert_alpha(),
                      pg.image.load(path.join(imgFolder, 'player4.png')).convert_alpha()]
        self.playerImgs = []
        for img in playerImgs:
            img = pg.transform.scale(img, (50, TILESIZE))
            self.playerImgs.append(img)
        self.grassImg = pg.image.load(path.join(imgFolder, 'grassTile.png')).convert_alpha()
        self.grassImg = pg.transform.scale(self.grassImg, (TILESIZE, TILESIZE))
        # load spritesheet image

        self.bombSpritesheet = Spritesheet(path.join(imgFolder, BOMBSPRITESHEET))
        
        self.playerSpritesheet = Spritesheet(path.join(imgFolder, PLAYERSPRITESHEET))
        

    def randomMapGenerator(self):
        self.tilesMap = [["-" for col in range(GRIDWIDTH)] for row in range(GRIDHEIGHT)]
        self.itemsMap = [["-" for col in range(GRIDWIDTH)] for row in range(GRIDHEIGHT)]

        #randomly fills in the board with explodable blocks
        for row in range(len(self.tilesMap)):
            for col in range(len(self.tilesMap[0])):
                probIndex = random.randrange(100)
                #a 80% chance for the grid to be an explodable block
                if probIndex < 80:
                    self.tilesMap[row][col] = 'E' #EXPLODABLE BLOCK

        #fills in the solid blocks at the set spots
        for row in range(2, len(self.tilesMap)-1, 2):
            for col in range(2, len(self.tilesMap[0])-1, 2):
                self.tilesMap[row][col] = 'S' #SOLID BLOCK
        
        for row in range(len(self.tilesMap)):
            for col in range(len(self.tilesMap[0])):
                #clears out the four corners
                if ((row + col == 3) or 
                   ((GRIDHEIGHT-1 - row) + col == 3) or 
                   (row + (GRIDWIDTH-1 - col) == 3) or
                   ((GRIDHEIGHT-1 - row)+(GRIDWIDTH-1 - col) == 3) or 
                   (row == col == 1) or
                   ((GRIDHEIGHT-1 - row) == col == 1) or
                   (row == (GRIDWIDTH-1 - col) == 1) or
                   ((GRIDHEIGHT-1 - row) == (GRIDWIDTH-1 - col) == 1)):
                   self.tilesMap[row][col] = '-' #EMPTY SPACE 
                #build the wall around the board
                if (row == 0 or row == GRIDHEIGHT-1 or 
                    col == 0 or col == GRIDWIDTH-1):
                   self.tilesMap[row][col] = 'S' #SOLID BLOCK
        
        #randomly spawns power-ups under explodable blocks
        for row in range(len(self.tilesMap)):
            for col in range(len(self.tilesMap[0])):
                #only spawns power-ups when the tile is an explodable block
                if self.tilesMap[row][col] == 'E':
                    probIndex = random.randrange(100)
                    #a 40% chance to find a powerup under an explodable block
                    if probIndex <= 40:
                        if probIndex <= 40//3:
                            self.itemsMap[row][col] = 'B' #EXTRA BOMB
                        elif probIndex > 40//3 and probIndex <= 100//3:
                            self.itemsMap[row][col] = 'S' #SPEED UP
                        else:
                            self.itemsMap[row][col] = 'R' #EXTRA FLAME RANGE

    def mapGenerator(self):
        self.tilesMap = [["-" for col in range(GRIDWIDTH)] for row in range(GRIDHEIGHT)]
        self.itemsMap = [["-" for col in range(GRIDWIDTH)] for row in range(GRIDHEIGHT)]
        
        #generate power-ups
        for row in range(len(self.tilesMap)):
            for col in range(len(self.tilesMap[0])):
                if len(self.explTiles) > 0:
                    for pos in self.explTiles:
                        if col == pos[0] and row == pos[1]:
                            self.tilesMap[row][col] = "E"
                if len(self.solidTiles) > 0:
                    for pos in self.solidTiles:
                        if col == pos[0] and row == pos[1]:
                            self.tilesMap[row][col] = "S"
                #build the wall around the board
                if (row == 0 or row == GRIDHEIGHT-1 or 
                    col == 0 or col == GRIDWIDTH-1):
                   self.tilesMap[row][col] = 'S' #SOLID BLOCK  

        #generate power-ups
        for row in range(len(self.tilesMap)):
            for col in range(len(self.tilesMap[0])):
                #only spawns power-ups when the tile is an explodable block
                if self.tilesMap[row][col] == 'E':
                    probIndex = random.randrange(100)
                    #a 40% chance to find a powerup under an explodable block
                    if probIndex <= 40:
                        if probIndex <= 40//3:
                            self.itemsMap[row][col] = 'B' #EXTRA BOMB
                        elif probIndex > 40//3 and probIndex <= 100//3:
                            self.itemsMap[row][col] = 'S' #SPEED UP
                        else:
                            self.itemsMap[row][col] = 'R' #EXTRA FLAME RANGE        

    #reads the map and creates blocks/player/items accordingly
    def translateMap(self):
        for row in range(len(self.tilesMap)):
            for col in range(len(self.tilesMap[0])):
                if self.tilesMap[row][col] == "S":
                    SolidBlock(self, col, row)
                if self.tilesMap[row][col] == "E":
                    ExplodableBlock(self, col, row)          
        for row in range(len(self.itemsMap)):
            for col in range(len(self.itemsMap[0])):
                if self.itemsMap[row][col] == 'B':
                    BombPowerup(self, col, row)
                if self.itemsMap[row][col] == 'S':
                    SpeedPowerup(self, col, row)
                if self.itemsMap[row][col] == 'R':
                    FlamePowerup(self, col, row)

        if self.randomMap:
            if self.singlePl: #single player
                pos = [(1,1), (GRIDHEIGHT-2,1), (1,GRIDWIDTH-2), (GRIDHEIGHT-2,GRIDWIDTH-2)]
                probIndex = random.randrange(4) 
                row = pos[probIndex][0]
                col = pos[probIndex][1]
                self.player = Player(self, col, row, pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_SPACE, (3, 13, 15, 22))   

                pos.pop(probIndex)
                probIndex = random.randrange(3)
                row = pos[probIndex][0]
                col = pos[probIndex][1]
                self.AIPlayer = AIPlayer(self, col, row)

            elif self.multiPl: #multi player
                for player in self.playersList:
                    Player(self, player[0], player[1], player[2], player[3], player[4], player[5], player[6], player[7], player[8], player[9])
                self.ranking = []

        else: #use self-made map
            if self.singlePl:
                col,row = self.playerTiles[1][0]
                self.player = Player(self, col, row, pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_SPACE, (3, 13, 15, 22))   
                
                pos = []
                for row in range(len(self.tilesMap)):
                    for col in range(len(self.tilesMap[0])):
                        if self.tilesMap[row][col] == '-':
                            pos.append((row,col))

                #randomly generate the AI at an empty spot
                probIndex = random.randrange(len(pos))
                row = pos[probIndex][0]
                col = pos[probIndex][1]
                self.AIPlayer = AIPlayer(self, col, row)
            
            elif self.multiPl:
                for key in self.playerTiles:
                    player = self.playersList[key-1]
                    col,row = self.playerTiles[key][0]
                    colorKey = self.playerTiles[key][1]
                    sprite = self.sprite[colorKey]
                    Player(self, col, row, player[2], player[3], player[4], player[5], player[6], sprite, player[8], player[9])
                self.ranking = []

    def new(self):
        # start a new game
        self.allSprites = pg.sprite.Group()
        self.players = pg.sprite.Group()
        self.AI = pg.sprite.Group()
        self.solidBlocks = pg.sprite.Group()
        self.bombs = pg.sprite.Group()
        self.bombsAI = pg.sprite.Group()
        self.tempBombs = pg.sprite.Group()
        self.tempBombsAI = pg.sprite.Group()
        self.explosion = pg.sprite.Group()
        self.explodableBlocks = pg.sprite.Group()
        self.powerups = pg.sprite.Group()
        if self.randomMap:
            self.randomMapGenerator()
        else:
            self.mapGenerator()
        self.translateMap()
           
    def run(self):
        # Game Loop 
        gameFolder = path.dirname(__file__)
        music = pg.mixer.music.load(path.join(gameFolder, 'main.mp3'))
        pg.mixer.music.play(-1)
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()
    
    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # Game Loop - Update
        self.allSprites.update()

    def events(self):
        # Game Loop - events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_r:
                    self.new()
                if event.key == pg.K_TAB:
                    self.playing = False
                    self.showGameControl()
 
    def draw(self):
        # Game Loop - draw
        self.screen.blit(self.bgImg, (0,0))
        self.powerups.draw(self.screen)
        self.solidBlocks.draw(self.screen)
        self.explodableBlocks.draw(self.screen)
        self.tempBombs.draw(self.screen)
        self.tempBombsAI.draw(self.screen)
        self.bombsAI.draw(self.screen)
        self.bombs.draw(self.screen)
        self.players.draw(self.screen)
        self.AI.draw(self.screen)
        self.explosion.draw(self.screen)        
        pg.display.flip()

    def showStartScreen(self):
        # game splash/start screen
        gameFolder = path.dirname(__file__)
        music = pg.mixer.music.load(path.join(gameFolder, 'menu.mp3'))
        pg.mixer.music.play(-1)
        titles = [(">Single Player<", "Multiplayer", "Scoreboard", "Help"), ("Single Player", ">Multiplayer<", "Scoreboard", "Help"), ("Single Player", "Multiplayer", ">Scoreboard<", "Help"), ("Single Player", "Multiplayer", "Scoreboard", ">Help<")]
        colors = [(YELLOW, WHITE, WHITE, WHITE), (WHITE, YELLOW, WHITE, WHITE), (WHITE, WHITE, YELLOW, WHITE), (WHITE, WHITE, WHITE, YELLOW)]
        index = 0
        while True:
            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Boomerguy", 100, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT/4)
            self.drawText(titles[index][0], SUBHEADING, colors[index][0], WIDTH/2, 360)
            self.drawText(titles[index][1], SUBHEADING, colors[index][1], WIDTH/2, 450)
            self.drawText(titles[index][2], SUBHEADING, colors[index][2], WIDTH/2, 540)
            self.drawText(titles[index][3], SUBHEADING, colors[index][3], WIDTH/2, 630)

            pg.display.flip()
            gettingInput = True
            while gettingInput:
                for event in pg.event.get():
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            gettingInput = False
                            startGame = True
                            if index == 0:
                                self.singlePl = True
                                self.multiPl = False
                            elif index == 1:
                                self.multiPl = True
                                self.singlePl = False
                            elif index == 2:
                                self.scoreboard = True
                                self.singlePl = False
                                self.multiPl = False
                            else:
                                self.help = True
                                self.scoreboard = False
                                self.singlePl = False
                                self.multiPl = False
                        else:
                            if event.key == pg.K_DOWN:
                                index = (index + 1) % 4
                                gettingInput = False
                            elif event.key == pg.K_UP:
                                index = (index - 1) % 4
                                gettingInput = False
                            startGame = False
            if startGame:
                break

        if self.singlePl:
            self.showSinglePlScreen()
            self.makeMapOrNo()
            if not self.randomMap:
                self.showMapScreen()
        elif self.multiPl:
            self.showMultiPlScreen()
            self.makeMapOrNo()
            if not self.randomMap:
                self.showMapScreen()
        elif self.scoreboard:
            self.showScoreboard()
            self.showStartScreen()
        elif self.help:
            self.showHelpScreen()
            self.showStartScreen()
            
    def showHelpScreen(self):
        self.screen.blit(self.flashscreen, (0,0))
        self.drawText("Help Screen", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
        self.drawText("Objective", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 120)
        self.drawText("Place bombs to break blocks and kill the opponent(s)", TEXT, WHITE, WIDTH/2, HEIGHT/2 - 50)
        self.drawText("Collect powerups to increase chance of winning", TEXT, WHITE, WIDTH/2, HEIGHT/2)
        self.screen.blit(self.bombPowerupImg, (WIDTH/4, HEIGHT/2 + 50))
        self.drawText("Increase bomb count", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 50)
        self.screen.blit(self.flamePowerupImg, (WIDTH/4, HEIGHT/2 + 100))
        self.drawText("Increase explosion range", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 100)
        self.screen.blit(self.speedPowerupImg, (WIDTH/4, HEIGHT/2 + 150))
        self.drawText("Increase speed", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 150)
        self.drawText("Hint : Press TAB during game to check game control", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 200)
        self.drawText("Press TAB to go back to home menu...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self.help = False
                    gettingInput = False

    def showSinglePlScreen(self):
        self.playerName = []
        self.screen.blit(self.flashscreen, (0,0))
        self.drawText("Single Player Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
        self.drawText("Please Enter Your Name", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 100)
        pg.draw.rect(self.screen, WHITE, (WIDTH/4, HEIGHT/2-20, WIDTH/2, HEIGHT/12), 2)
        pg.display.flip()
        while True:
            key = self.waitForKey()
            if (key == pg.K_RETURN or len(self.playerName)>15) and len(self.playerName) > 0: 
                self.playerName = ''.join(self.playerName)
                break
            elif key == pg.K_SPACE:
                self.playerName.append(' ')
            elif key == pg.K_BACKSPACE:
                if len(self.playerName) > 0:
                    self.playerName.pop()
            elif pg.key.name(key) in string.printable: 
                self.playerName.append(pg.key.name(key))
            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Single Player Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText("Please Enter Your Name", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 100)
            pg.draw.rect(self.screen, WHITE, (WIDTH/4, HEIGHT/2-20, WIDTH/2, HEIGHT/12), 2)
            self.drawText(''.join(self.playerName), SUBHEADING, WHITE, WIDTH/2, HEIGHT/2)
            pg.display.flip()
        
        self.screen.blit(self.flashscreen, (0,0))    
        self.drawText("Single Player Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
        self.drawText("Game Control", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 120)
        self.drawText("LEFT - Move Left", TEXT, WHITE, WIDTH/2, HEIGHT/2 - 50)
        self.drawText("RIGHT - Move Right", TEXT, WHITE, WIDTH/2, HEIGHT/2)
        self.drawText("UP - Move Up", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 50)
        self.drawText("DOWN - Move Down", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 100)
        self.drawText("SPACE - Place Bomb", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 150)
        self.drawText("Press ENTER to begin, TAB to go back to home menu...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
        pg.display.flip()

        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        gettingInput = False
                    elif event.key == pg.K_TAB:
                        self.singlePl = False
                        gettingInput = False
                        self.showStartScreen()
    
    def showMultiPlScreen(self):
        self.playerNum = 1
        self.playersList = []
        self.playerNames = {}
        keys = []
        pos = [(1,1), (GRIDHEIGHT-2,1), (1,GRIDWIDTH-2), (GRIDHEIGHT-2,GRIDWIDTH-2)]
        self.sprite = [(3, 13, 15, 22), (161, 13, 15, 22), (3, 108, 15, 22), (161, 108, 15, 22)]
        self.colors = [WHITE, BLACK, RED, GREEN]
        self.frames = [self.playerSpritesheet.getImage(20, 13, 15, 22),
                       self.playerSpritesheet.getImage(178, 13, 15, 22),
                       self.playerSpritesheet.getImage(20, 108, 15, 22),
                       self.playerSpritesheet.getImage(178, 108, 15, 22)]
        index = 0
        while index < 4: #max four players
            playerName = []
            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Multiplayer Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText("Please Enter Your Name", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 100)
            pg.draw.rect(self.screen, WHITE, (WIDTH/4, HEIGHT/2-20, WIDTH/2, HEIGHT/12), 2)
            pg.display.flip()

            while True:
                key = self.waitForKey()
                if (key == pg.K_RETURN or len(playerName)>15) and len(playerName) > 0: 
                    self.playerNames[self.playerNum] = ''.join(playerName)
                    break
                elif key == pg.K_SPACE:
                    playerName.append(' ')
                elif key == pg.K_BACKSPACE:
                    if len(playerName) > 0:
                        playerName.pop()
                elif pg.key.name(key) in string.printable: 
                    playerName.append(pg.key.name(key))
                self.screen.blit(self.flashscreen, (0,0))
                self.drawText("Multiplayer Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
                self.drawText("Please Enter Your Name", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 100)
                pg.draw.rect(self.screen, WHITE, (WIDTH/4, HEIGHT/2-20, WIDTH/2, HEIGHT/12), 2)
                self.drawText(''.join(playerName), SUBHEADING, WHITE, WIDTH/2, HEIGHT/2)
                pg.display.flip()

            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Multiplayer Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText(f"Setting Keys For {''.join(playerName)}", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 120)
            self.drawText("Press the key you want for moving up", TEXT, WHITE, WIDTH/2, HEIGHT/2 - 40)
            pg.display.flip()

            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            upKey = key
            keys.append(upKey)

            self.drawText("Press the key you want for moving down", TEXT, WHITE, WIDTH/2, HEIGHT/2+10)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            downKey = key
            keys.append(downKey)

            self.drawText("Press the key you want for moving left", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 60)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            leftKey = key
            keys.append(leftKey)
            
            self.drawText("Press the key you want for moving right", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 110)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            rightKey = key
            keys.append(rightKey)

            self.drawText("Press the key you want for placing bombs", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 160)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            bombKey = key
            keys.append(bombKey)
           
            self.playersList.append((pos[index][1], pos[index][0], upKey, downKey, leftKey, rightKey, bombKey, self.sprite[index], self.playerNum, self.colors[index]))
            index += 1
            
            if index < 4:
                self.drawText("Create another player?", TEXT, YELLOW, WIDTH/2, HEIGHT - 150)
                self.drawText("Press ENTER to create, TAB to go back to home menu, anything else to start...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
                pg.display.flip()
            else:
                self.drawText("Press ENTER to start, TAB to go back to home menu...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
                pg.display.flip()
                break
                
            cont = self.waitForKey()
            if cont == pg.K_TAB:
                self.multiPl = False
                self.playersList = []
                self.showStartScreen()
                break
            elif cont == pg.K_RETURN:
                self.playerNum += 1
            else:
                break
        if index == 4:
            gettingInput = True
            while gettingInput:
                for event in pg.event.get():
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            gettingInput = False
                        elif event.key == pg.K_TAB:
                            self.multiPl = False
                            self.playerNames = {}
                            gettingInput = False
                            self.showStartScreen()
    
    def showGameControl(self):
        self.screen.blit(self.flashscreen, (0,0))
        if self.singlePl:
            self.drawText("Single Player Mode", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText("Game Control", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 120)
            self.drawText("LEFT - Move Left", TEXT, WHITE, WIDTH/2, HEIGHT/2 - 50)
            self.drawText("RIGHT - Move Right", TEXT, WHITE, WIDTH/2, HEIGHT/2)
            self.drawText("UP - Move Up", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 50)
            self.drawText("DOWN - Move Down", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 100)
            self.drawText("SPACE - Place Bomb", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 150)
            self.drawText("Press any key to continue...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)            
        else:
            self.drawText("Multiplayer Mode", HEADING, WHITE, WIDTH/2, 90)
            self.drawText("Game Control", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 230)
            for player in self.playersList:
                playerNum = player[8]
                upKey = player[2]
                downKey = player[3]
                leftKey = player[4]
                rightKey = player[5]
                bombKey = player[6]
                color = player[9]
                if playerNum % 2 == 1:
                    width = WIDTH/3
                else:
                    width = WIDTH*2/3
                if playerNum <= 2:
                    height = HEIGHT/2 - 170
                else:
                    height = HEIGHT/2 + 80
                self.drawText(self.playerNames[playerNum], 36, color, width, height)
                self.drawText(f"{pg.key.name(leftKey).upper()} - Move Left", TEXT, WHITE, width, height + 50)
                self.drawText(f"{pg.key.name(rightKey).upper()} - Move Right", TEXT, WHITE, width, height + 85)
                self.drawText(f"{pg.key.name(upKey).upper()} - Move Up", TEXT, WHITE, width, height + 120)
                self.drawText(f"{pg.key.name(downKey).upper()} - Move Down", TEXT, WHITE, width, height + 155)
                self.drawText(f"{pg.key.name(bombKey).upper()} - Place Bomb", TEXT, WHITE, width, height + 195)
            self.drawText("Press any key to continue...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    self.playing = True
                    gettingInput = False

    def showGoScreen(self):
        #game over/continue
        gameFolder = path.dirname(__file__)
        music = pg.mixer.music.load(path.join(gameFolder, 'end.mp3'))
        pg.mixer.music.play(-1)
        self.screen.blit(self.flashscreen, (0,0))
        if self.singlePl:
            if self.player.win:
                self.drawText("You Win!", HEADING, WHITE, WIDTH/2, HEIGHT/2)
                self.drawText("Press ENTER to play again...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
            else:
                self.drawText("Game Over", HEADING, WHITE, WIDTH/2, HEIGHT/2)
                self.drawText("Press ENTER to try again...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
        else:
            self.drawText("Game Over", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText("Rank", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 120)
            self.ranking = self.ranking[::-1]
            temp = []
            
            for i in range(len(self.ranking)):
                temp.append(self.ranking[i])
                playerNum = self.ranking[i]
                self.drawText(self.playerNames[playerNum], 48, self.colors[playerNum-1], WIDTH/2, (HEIGHT/2 + 20) + i * 70)
            
            for i in range(1, self.playerNum+1):
                if i not in temp:
                    self.drawText(self.playerNames[i], 48, self.colors[i-1], WIDTH/2, HEIGHT/2 - 50)
                    with open('multiScores.txt', 'a') as f:
                        f.write(f"{self.playerNames[i]}\n")
            self.drawText("Press ENTER to play again...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100)
        
        self.randomMap = True
        self.playersList = []
        self.playerTiles = {}
        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    self.singlePl = False
                    self.playing = True
                    gettingInput = False
    
    def showScoreboard(self):
        self.screen.blit(self.flashscreen, (0,0))
        mode = 'single'
        singleHighscores = self.findHighscores(mode)
        self.drawText("Single Player", SUBHEADING, YELLOW, WIDTH/4 + 10, HEIGHT/2 - HEIGHT*3/10)
        if singleHighscores != None:
            for i in range(len(singleHighscores)):
                player = singleHighscores[i][0].strip()
                score = singleHighscores[i][1]
                self.drawText(f'{player}: {score}', 36, WHITE, WIDTH/4, HEIGHT/3 + i*70)
        
        mode = 'multi'
        multiHighscores = self.findHighscores(mode)
        self.drawText("Multiplayer", SUBHEADING, YELLOW, WIDTH*3/4, HEIGHT/2 - HEIGHT*3/10)
        if multiHighscores != None:
            for i in range(len(multiHighscores)):
                player = multiHighscores[i][0].strip()
                score = multiHighscores[i][1]
                self.drawText(f'{player}: {score}', 36, WHITE, WIDTH*3/4, HEIGHT/3 + i*60)
     
        self.drawText("Press TAB to go back to home menu...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100) 
        pg.display.flip()
        
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self.help = False
                    gettingInput = False

    def findHighscores(self, mode):  
        scores = {}
        with open(f'{mode}Scores.txt', 'r') as s:
            for name in s:
                if name not in scores:
                    scores[name] = 1
                else:
                    scores[name] += 1

        highscores = []
        for i in range(5):
            if self.findHighestScore(scores)[0] != None:
                winner, highscore = self.findHighestScore(scores)
                highscores.append((winner, highscore))
                del scores[winner]
            else: break
        return highscores

    def findHighestScore(self, scores):
        highscore = 0
        winner = None
        for key in scores:
            if scores[key] > highscore:
                highscore = scores[key]
                winner = key
        return winner, highscore
    
    def makeMapOrNo(self):
        self.screen.blit(self.flashscreen, (0,0))
        self.drawText("Do You Want To Make Your Own Map?", 36, WHITE, WIDTH/4, HEIGHT/2 - HEIGHT*3/10)
        pg.display.flip()
        options = [(">YES<", "NO"), ("YES", ">NO<")]
        colors = [(YELLOW, WHITE), (WHITE, YELLOW)]
        index = 0
        while True:
            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Do You Want To Make Your Own Map?", 36, WHITE, WIDTH/2, HEIGHT/2 - 120)
            self.drawText(options[index][0], SUBHEADING, colors[index][0], WIDTH/2, 400)
            self.drawText(options[index][1], SUBHEADING, colors[index][1], WIDTH/2, 490)
            pg.display.flip()
            
            gettingInput = True
            while gettingInput:
                for event in pg.event.get():
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            gettingInput = False
                            startGame = True
                            if index == 0:
                                self.randomMap = False
                                self.makeMapInstructions()
                                break
                            elif index == 1:
                                self.randomMap = True
                                break
                        else:
                            if event.key == pg.K_DOWN:
                                index = (index + 1) % 2
                                gettingInput = False
                            elif event.key == pg.K_UP:
                                index = (index - 1) % 2
                                gettingInput = False
                            startGame = False
            if startGame: break

    def makeMapInstructions(self):
        self.screen.blit(self.flashscreen, (0,0))
        self.drawText("Make Your Own Map", HEADING, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
        self.drawText("Instructions", SUBHEADING, YELLOW, WIDTH/2, HEIGHT/2 - 120)
        self.drawText("1. Click on each cell to select cell(s)", TEXT, WHITE, WIDTH/2, HEIGHT/2 - 50)
        self.drawText("2. Click on an icon on the left to assign cell(s)", TEXT, WHITE, WIDTH/2, HEIGHT/2)
        self.drawText("3. Reassign cell(s) by reclicking on the cell(s)", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 50)
        self.drawText("4. Walls are automatically generated around the map", TEXT, WHITE, WIDTH/2, HEIGHT/2 + 100)
        self.drawText("Press ENTER to continue...", SUBTEXT, YELLOW, WIDTH/2, HEIGHT - 100) 

        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    gettingInput = False

    def showMapScreen(self):
        self.clickedTiles = []
        self.explTiles = []
        self.solidTiles = []
        self.playerTiles = {}
        self.screen.fill(LIGHTGREY)
        pg.draw.rect(self.screen, YELLOW, (2*64, 10, 3*64, 45))
        pg.draw.rect(self.screen, YELLOW, (6*64, 10, 3*64, 45))
        pg.draw.rect(self.screen, YELLOW, (10*64, 10, 3*64, 45))
        self.drawText("Home Menu", TEXT, BLACK, 3*64+32, 20)
        self.drawText("Create New", TEXT, BLACK, 7*64+32, 20)
        self.drawText("Start Game", TEXT, BLACK, 11*64+32, 20)
        bg = pg.transform.scale(self.bgImg, (832, 704))
        self.screen.blit(bg, (64,64))
        self.screen.blit(self.solidBlImg, (0, 64))
        self.screen.blit(self.explodableBlImg, (0, 64*2))
        if self.singlePl:
            self.screen.blit(self.playerImgs[0], (5, 64*3))
        elif self.multiPl:
            for i in range(len(self.playerImgs)):
                self.screen.blit(self.playerImgs[i], (5, 64*(3+i)))
        self.drawGrid()
        pg.display.flip()
        self.makeMap()
    
    def makeMap(self):
        if self.singlePl:
            maxPlayer = 1
        elif self.multiPl:
            maxPlayer = len(self.playersList)
        currentPlayer = 0
        solid = (0, 1)
        explodable = (0, 2)
        players = [(0,3),(0,4),(0,5),(0,6)]
        buttons = {"Home Menu": (2*64, 10, 5*64, 45),
                   "Create New": (6*64, 10, 9*64, 45),
                   "Start Game": (10*64, 10, 13*64, 45)}
        makingMap = True
        taken = []
        
        while makingMap:
            pos = self.getMousePressed()
            x = pos[0]//TILESIZE
            y = pos[1]//TILESIZE
            for key in buttons:
                (left, top, right, bottom) = buttons[key]
                if pos[0] > left and pos[0] < right and pos[1] > top and pos[1] < bottom:
                    if key == "Create New":
                        self.showMapScreen()
                        break
                    elif key == "Home Menu":
                        self.showStartScreen()
                        makingMap = False
                        break
                    elif key == "Start Game" and len(self.playerTiles)>0:
                        self.randomMap = False
                        makingMap = False
                        break
            
            #assign selected tiles to explodable blocks
            if (x,y) == explodable:
                for (clickedX, clickedY) in self.clickedTiles:
                    self.screen.blit(self.explodableBlImg, (clickedX*TILESIZE,clickedY*TILESIZE))
                    if (clickedX, clickedY) in self.solidTiles:
                        self.solidTiles.remove((clickedX, clickedY))
                    self.explTiles += copy.copy(self.clickedTiles)
                    self.clickedTiles = []
            
            #assign selected tiles to solid blocks
            elif (x,y) == solid:
                for (clickedX, clickedY)  in self.clickedTiles:
                    self.screen.blit(self.solidBlImg, (clickedX*TILESIZE,clickedY*TILESIZE))
                    if (clickedX, clickedY) in self.explTiles:
                        self.explTiles.remove((clickedX, clickedY))
                    self.solidTiles += copy.copy(self.clickedTiles)
                    self.clickedTiles = []
            
            #assign selected tile to player
            elif (x,y) in players and currentPlayer < maxPlayer and len(self.clickedTiles) == 1:
                clickedX, clickedY = self.clickedTiles[0]
                taken.append((clickedX, clickedY))
                for i in range(0, len(players)):
                    if (x,y) == players[i]:
                        self.screen.blit(self.grassImg, (clickedX*TILESIZE, clickedY*TILESIZE))
                        self.screen.blit(self.playerImgs[i], (clickedX*TILESIZE + 5,clickedY*TILESIZE))
                        self.playerTiles[currentPlayer+1] = [self.clickedTiles[0], i]
                        self.clickedTiles = []
                        currentPlayer += 1
                        break
            
            #select tiles
            elif ((x,y) not in self.clickedTiles and x>0 and x<14 and y>0 and y<12 and (x,y) not in taken):
                self.clickedTiles.append((x,y))
                centerx, centery = x*TILESIZE+TILESIZE//2, y*TILESIZE+TILESIZE//2
                pg.draw.rect(self.screen, YELLOW, (x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE))
                pg.draw.rect(self.screen, BLACK, (x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE), 3)

            pg.display.flip()
        
    def drawGrid(self):
        for x in range(64, WIDTH, TILESIZE):
            pg.draw.line(self.screen, DARKGREY, (x, 64), (x, HEIGHT-64))
        for y in range(64, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, DARKGREY, (64, y), (WIDTH-64, y))
            
    def getMousePressed(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONUP:
                    pos = pg.mouse.get_pos()
                    return pos

    def waitForKey(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    key = event.key
                    return key

    #This code is inpired from https://www.youtube.com/watch?v=rLrMPg-GCqo
    def drawText(self, text, size, color, x, y):
        font = pg.font.Font(self.fontName, size)
        textSurface = font.render(text, True, color)
        textRect = textSurface.get_rect()
        textRect.midtop = (x, y)
        self.screen.blit(textSurface, textRect)

g = Game()
while g.running:
    g.showStartScreen()
    g.new()
    g.run()
    g.showGoScreen()
g.quit()

