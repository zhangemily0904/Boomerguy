import pygame as pg
import random
import sys
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
        self.fontName = pg.font.match_font('Arial')
    
    def loadData(self):
        gameFolder = path.dirname(__file__)
        imgFolder = path.join(gameFolder, 'img')
        self.flashscreen = pg.image.load(path.join(imgFolder, 'flashscreen.png')).convert_alpha()
        self.flashscreen = pg.transform.scale(self.flashscreen, (WIDTH, HEIGHT))
        self.bgImg = pg.image.load(path.join(imgFolder, 'background.png')).convert_alpha()
        self.bgImg = pg.transform.scale(self.bgImg, (WIDTH, HEIGHT))
        self.solidBlImg = pg.image.load(path.join(imgFolder, 'SolidBlock.png')).convert_alpha()
        self.explodableBlImg = pg.image.load(path.join(imgFolder, 'ExplodableBlock.png')).convert_alpha()
        self.explFrames = [pg.image.load(path.join(imgFolder, 'flame0.png')).convert_alpha(),
                           pg.image.load(path.join(imgFolder, 'flame1.png')).convert_alpha(),
                           pg.image.load(path.join(imgFolder, 'flame2.png')).convert_alpha(),
                           pg.image.load(path.join(imgFolder, 'flame3.png')).convert_alpha(),
                           pg.image.load(path.join(imgFolder, 'flame4.png')).convert_alpha()]
        self.bombPowerupImg = pg.image.load(path.join(imgFolder, 'BombPowerup.png')).convert_alpha()
        self.speedPowerupImg = pg.image.load(path.join(imgFolder, 'SpeedPowerup.png')).convert_alpha()
        self.flamePowerupImg = pg.image.load(path.join(imgFolder, 'FlamePowerup.png')).convert_alpha()
        # load spritesheet image
        self.bombSpritesheet = Spritesheet(path.join(imgFolder, BOMBSPRITESHEET))
        self.playerSpritesheet = Spritesheet(path.join(imgFolder, PLAYERSPRITESHEET))

    def mapGenerator(self):
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

        if self.singlePl: #single player
            print('single')
            pos = [(1,1), (GRIDHEIGHT-2,1), (1,GRIDWIDTH-2), (GRIDHEIGHT-2,GRIDWIDTH-2)]
            probIndex = random.randrange(4) 
            row = pos[probIndex][0]
            col = pos[probIndex][1]
            print(f'player {col, row}')
            self.player = Player(self, col, row, pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_SPACE, (3, 13, 15, 22))   

            pos.pop(probIndex)
            probIndex = random.randrange(3)
            row = pos[probIndex][0]
            col = pos[probIndex][1]
            print(f'ai {col, row}')
            self.AIPlayer = AIPlayer(self, col, row)

        elif self.multiPl: #multi player
            print('multi')
            print(self.playersList)
            for player in self.playersList:
                Player(self, player[0], player[1], player[2], player[3], player[4], player[5], player[6], player[7], player[8], player[9])
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
        self.mapGenerator()
        self.translateMap()
           
    def run(self):
        # Game Loop 
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
                if event.key == pg.K_LCTRL:
                    self.playing = False
                    self.showGameControl()
                    
    def drawGrid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))
 
    def draw(self):
        # Game Loop - draw
        self.screen.blit(self.bgImg, (0,0))
        self.drawGrid()
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
        titles = [(">Single Player<", "Multiplayer", "Help"), ("Single Player", ">Multiplayer<", "Help"), ("Single Player", "Multiplayer", ">Help<")]
        colors = [(YELLOW, WHITE, WHITE), (WHITE, YELLOW, WHITE), (WHITE, WHITE, YELLOW)]
        index = 0
        while True:
            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Boomerguy", 128, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*2/10)
            self.drawText(titles[index][0], 68, colors[index][0], WIDTH/2, HEIGHT/2)
            self.drawText(titles[index][1], 68, colors[index][1], WIDTH/2, HEIGHT/2 + HEIGHT/10)
            self.drawText(titles[index][2], 68, colors[index][2], WIDTH/2, HEIGHT/2 + HEIGHT*2/10)
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
                            else:
                                self.help = True
                                self.singlePl = False
                                self.multiPl = False
                        else:
                            if event.key == pg.K_DOWN:
                                index = (index + 1) % 3
                                gettingInput = False
                            elif event.key == pg.K_UP:
                                index = (index - 1) % 3
                                gettingInput = False
                            startGame = False
            if startGame:
                break
        if self.singlePl:
            self.showSinglePlScreen()
        elif self.multiPl:
            self.showMultiPlScreen()
        elif self.help:
            self.showHelpScreen()
            self.showStartScreen()
            
    def showHelpScreen(self):
        self.screen.blit(self.flashscreen, (0,0))
        self.drawText("Help Screen", 96, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
        self.drawText("Objective", 60, YELLOW, WIDTH/2, HEIGHT/2 - 120)
        self.drawText("Kill the opponent(s) by strategically placing bombs", 36, WHITE, WIDTH/2, HEIGHT/2 - 50)
        self.drawText("Collect powerups to increase chance of winning", 36, WHITE, WIDTH/2, HEIGHT/2)
        self.screen.blit(self.bombPowerupImg, (WIDTH/4, HEIGHT/2 + 50))
        self.drawText("Increase bomb count", 36, WHITE, WIDTH/2, HEIGHT/2 + 50)
        self.screen.blit(self.flamePowerupImg, (WIDTH/4, HEIGHT/2 + 100))
        self.drawText("Increase explosion range", 36, WHITE, WIDTH/2, HEIGHT/2 + 100)
        self.screen.blit(self.speedPowerupImg, (WIDTH/4, HEIGHT/2 + 150))
        self.drawText("Increase speed", 36, WHITE, WIDTH/2, HEIGHT/2 + 150)
        self.drawText("Press Tab to go back to home page...", 36, WHITE, WIDTH/2, HEIGHT - 100)
        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self.help = False
                    gettingInput = False

    def showSinglePlScreen(self):
        self.screen.blit(self.flashscreen, (0,0))
        self.drawText("Single Player Mode", 96, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
        self.drawText("Game Control", 60, YELLOW, WIDTH/2, HEIGHT/2 - 120)
        self.drawText("LEFT ARROW - Move Left", 36, WHITE, WIDTH/2, HEIGHT/2 - 50)
        self.drawText("RIGHT ARROW - Move Right", 36, WHITE, WIDTH/2, HEIGHT/2)
        self.drawText("UP ARROW - Move Up", 36, WHITE, WIDTH/2, HEIGHT/2 + 50)
        self.drawText("DOWN ARROW - Move Down", 36, WHITE, WIDTH/2, HEIGHT/2 + 100)
        self.drawText("SPACE - Place Bomb", 36, WHITE, WIDTH/2, HEIGHT/2 + 150)
        self.drawText("Press Enter to begin, Tab to go back to home page...", 36, WHITE, WIDTH/2, HEIGHT - 100)
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
        keys = []
        pos = [(1,1), (GRIDHEIGHT-2,1), (1,GRIDWIDTH-2), (GRIDHEIGHT-2,GRIDWIDTH-2)]
        sprite = [(3, 13, 15, 22), (161, 13, 15, 22), (3, 108, 15, 22), (161, 108, 15, 22)]
        colors = [WHITE, BLACK, RED, GREEN]
        index = 0
        while index < 4: #max four players
            self.screen.blit(self.flashscreen, (0,0))
            self.drawText("Multiplayer Mode", 96, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText(f"Setting keys for Player {self.playerNum}...", 60, YELLOW, WIDTH/2, HEIGHT/2 - 120)
            pg.display.flip()
            self.drawText("Press the key you want for moving up", 36, WHITE, WIDTH/2, HEIGHT/2 - 50)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            upKey = key
            keys.append(upKey)

            self.drawText("Press the key you want for moving down", 36, WHITE, WIDTH/2, HEIGHT/2)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            downKey = key
            keys.append(downKey)

            self.drawText("Press the key you want for moving left", 36, WHITE, WIDTH/2, HEIGHT/2 + 50)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            leftKey = key
            keys.append(leftKey)
            
            self.drawText("Press the key you want for moving right", 36, WHITE, WIDTH/2, HEIGHT/2 + 100)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            rightKey = key
            keys.append(rightKey)

            self.drawText("Press the key you want for placing bombs", 36, WHITE, WIDTH/2, HEIGHT/2 + 150)
            pg.display.flip()
            key = self.waitForKey()
            while key in keys:
                key = self.waitForKey()
            bombKey = key
            keys.append(bombKey)
           
            self.playersList.append((pos[index][1], pos[index][0], upKey, downKey, leftKey, rightKey, bombKey, sprite[index], self.playerNum, colors[index]))
            index += 1
            if index >= 4:
                break
            self.drawText("Create another player?", 36, WHITE, WIDTH/2, HEIGHT - 150)
            self.drawText("Press Enter to create, Tab to go back to home page, anything else to stop...", 32, WHITE, WIDTH/2, HEIGHT - 100)
            pg.display.flip()
    
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
            
    def showGameControl(self):
        self.screen.blit(self.flashscreen, (0,0))
        if self.singlePl:
            self.drawText("Single Player Mode", 96, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText("Game Control", 60, YELLOW, WIDTH/2, HEIGHT/2 - 120)
            self.drawText("LEFT ARROW - Move Left", 36, WHITE, WIDTH/2, HEIGHT/2 - 50)
            self.drawText("RIGHT ARROW - Move Right", 36, WHITE, WIDTH/2, HEIGHT/2)
            self.drawText("UP ARROW - Move Up", 36, WHITE, WIDTH/2, HEIGHT/2 + 50)
            self.drawText("DOWN ARROW - Move Down", 36, WHITE, WIDTH/2, HEIGHT/2 + 100)
            self.drawText("SPACE - Place Bomb", 36, WHITE, WIDTH/2, HEIGHT/2 + 150)
            self.drawText("Press any key to continue...", 36, WHITE, WIDTH/2, HEIGHT - 100)            
        else:
            self.drawText("Multiplayer Mode", 96, WHITE, WIDTH/2, 150)
            self.drawText("Game Control", 60, YELLOW, WIDTH/2, HEIGHT/2 - 180)
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
                    height = HEIGHT/2 - 110
                else:
                    height = HEIGHT/2 + 100
                self.drawText(f"Player {playerNum}", 48, color, width, height)
                self.drawText(f"{leftKey} - Move Left", 36, WHITE, width, height + 35)
                self.drawText(f"{rightKey} - Move Right", 36, WHITE, width, height + 70)
                self.drawText(f"{upKey} - Move Up", 36, WHITE, width, height + 105)
                self.drawText(f"{downKey} - Move Down", 36, WHITE, width, height + 140)
                self.drawText(f"{bombKey} - Place Bomb", 36, WHITE, width, height + 175)
            self.drawText("Press any key to continue...", 36, WHITE, WIDTH/2, HEIGHT - 100)
        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    self.playing = True
                    gettingInput = False

    def showGoScreen(self):
        print('over')
        #game over/continue
        self.screen.blit(self.flashscreen, (0,0))
        if self.singlePl:
            if self.player.win:
                self.drawText("You Win!", 96, WHITE, WIDTH/2, HEIGHT/2)
                self.drawText("Press Enter to play again...", 36, WHITE, WIDTH/2, HEIGHT - 100)
            else:
                self.drawText("Game Over", 96, WHITE, WIDTH/2, HEIGHT/2)
                self.drawText("Press Enter to try again...", 36, WHITE, WIDTH/2, HEIGHT - 100)
        else:
            self.drawText("Game Over", 96, WHITE, WIDTH/2, HEIGHT/2 - HEIGHT*3/10)
            self.drawText("Rank", 60, YELLOW, WIDTH/2, HEIGHT/2 - 120)
            self.ranking = self.ranking[::-1]
            print(self.ranking)
            temp = []
            
            for i in range(len(self.ranking)):
                temp.append(self.ranking[i][0])
                print(i)
                self.drawText(f"Player {self.ranking[i][0]}", 48, self.ranking[i][1], WIDTH/2, HEIGHT/2 + i * 50)
            
            for i in range(1, self.playerNum+1):
                if i not in temp:
                    if i == 1:
                        color = WHITE
                    elif i == 2:
                        color = BLACK
                    elif i == 3:
                        color = RED
                    else:
                        color = GREEN
                    self.drawText(f"Player {i}", 48, color, WIDTH/2, HEIGHT/2 - 50)
            self.drawText("Press Enter to play again...", 36, WHITE, WIDTH/2, HEIGHT - 100)
            
        pg.display.flip()
        gettingInput = True
        while gettingInput:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    self.singlePl = False
                    self.playing = True
                    gettingInput = False
                
    def waitForKey(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    key = event.key
                    return key
                    
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

