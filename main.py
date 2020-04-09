import pygame as pg
import random
import sys
from os import path
from settings import *
from sprites import *
from tilemap import *

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
        self.loadData()
    
    def loadData(self):
        gameFolder = path.dirname(__file__)
        imgFolder = path.join(gameFolder, 'img')
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
                   self.tilesMap[row][col] = 'S' 

        #determines the where the player spawns
        spawningPosition = random.choice([(1,1), (GRIDHEIGHT-2,1),
                           (1,GRIDWIDTH-2), (GRIDHEIGHT-2,GRIDWIDTH-2)])
        row, col = spawningPosition
        self.tilesMap[row][col] = 'P'

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
                elif self.tilesMap[row][col] == "E":
                    ExplodableBlock(self, col, row)
                elif self.tilesMap[row][col] == 'P':
                    self.player = Player(self, col, row)
        for row in range(len(self.itemsMap)):
            for col in range(len(self.itemsMap[0])):
                if self.itemsMap[row][col] == 'B':
                    BombPowerup(self, col, row)
                elif self.itemsMap[row][col] == 'S':
                    SpeedPowerup(self, col, row)
                elif self.itemsMap[row][col] == 'R':
                    FlamePowerup(self, col, row)

    def new(self):
        # start a new game
        self.allSprites = pg.sprite.Group()
        self.players = pg.sprite.Group()
        self.solidBlocks = pg.sprite.Group()
        self.bombs = pg.sprite.Group()
        self.tempBombs = pg.sprite.Group()
        self.explosion = pg.sprite.Group()
        self.explodableBlocks = pg.sprite.Group()
        self.powerups = pg.sprite.Group()
        self.mapGenerator()
        self.translateMap()
                   
    def run(self):
        # Game Loop 
        self.playing = True
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
                if (event.key == pg.K_SPACE and self.player.canDropBomb and
                    self.player.bombQuota > 0):
                    self.player.placeBomb()
                if event.key == pg.K_r:
                    self.new()

    def drawGrid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))

    def draw(self):
        # Game Loop - draw
        self.screen.blit(self.bgImg, (0,0))
        self.drawGrid()
        self.tempBombs.draw(self.screen)
        self.bombs.draw(self.screen)
        self.powerups.draw(self.screen)
        self.solidBlocks.draw(self.screen)
        self.explodableBlocks.draw(self.screen)
        self.players.draw(self.screen)
        self.explosion.draw(self.screen)        
        pg.display.flip()

    def showStartScreen(self):
        # game splash/start screen
        pass

    def showGoScreen(self):
        #game over/continue
        pass

g = Game()
g.showStartScreen()
while g.running:
    g.new()
    g.run()
    g.showGoScreen()

g.quit()

