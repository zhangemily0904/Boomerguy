import pygame as pg
from settings import *

class Bomb(pg.sprite.Sprite):
    def __init__(self, game, x, y, range, AI, player):
        self.groups = game.allSprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.loadImages()
        self.image = self.bombFrames[0]
        self.image.set_colorkey(BLACK)
        self.currentFrame = 0
        self.lastUpdate = 0
        self.time = 0
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE
        self.frameRate = 300
        self.range = range
        self.AI = AI
        self.player = player
        self.run = False
    
    def loadImages(self):
        self.bombFrames = [self.game.bombSpritesheet.getImage(66, 288, 15, 16),
                           self.game.bombSpritesheet.getImage(83, 289, 12, 15),
                           self.game.bombSpritesheet.getImage(98, 288, 13, 16),
                           self.game.bombSpritesheet.getImage(115, 288, 12, 16),
                           self.game.bombSpritesheet.getImage(130, 288, 13, 16),
                           self.game.bombSpritesheet.getImage(147, 289, 12, 15)]
        for frame in self.bombFrames:
            frame.set_colorkey(BLACK)

    def update(self):
        timeNow = pg.time.get_ticks()
        if timeNow - self.lastUpdate > self.frameRate:
            self.lastUpdate = timeNow
            self.currentFrame = (self.currentFrame + 1) % (len(self.bombFrames))
            self.image = self.bombFrames[self.currentFrame]
        self.time += 1
        if self.time > 50:
            self.removeBombs()

    #removes the Bomb after a period of time
    def removeBombs(self):
        self.explodeBomb()
        if self.AI: 
            self.kill()
            self.game.AIPlayer.bombsLeft += 1
        if not self.AI or self.run:
            self.player.bombsLeft += 1
            self.kill()
        self.game.tilesMap[self.y][self.x] = '-'

    #creates explosions based on the player's flame range
    #flames cannot break through solid blocks
    def explodeBomb(self):
        Explosion(self.game, self.x, self.y, self.AI) #center
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x, self.y - i, self.AI) #up
            if flame.collideWithObstacles(self.game.solidBlocks):
                flame.kill()
                break
            elif flame.collideWithObstacles(self.game.explodableBlocks):
                break
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x, self.y + i, self.AI) #down
            if flame.collideWithObstacles(self.game.solidBlocks):
                flame.kill()
                break
            elif flame.collideWithObstacles(self.game.explodableBlocks):
                break
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x + i, self.y, self.AI) #right
            if flame.collideWithObstacles(self.game.solidBlocks):
                flame.kill()
                break
            elif flame.collideWithObstacles(self.game.explodableBlocks):
                break
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x - i, self.y, self.AI) #left
            if flame.collideWithObstacles(self.game.solidBlocks):
                flame.kill()
                break
            elif flame.collideWithObstacles(self.game.explodableBlocks):
                break

    
class Explosion(pg.sprite.Sprite):
    def __init__(self, game, x, y, AI):
        self.groups = game.allSprites, game.explosion
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.explFrames[0]
        self.currentFrame = 0
        self.lastUpdate = 0
        self.frameRate = 100
        self.rect = self.image.get_rect()
        self.rect.center = (x*TILESIZE + TILESIZE/2, y*TILESIZE + TILESIZE/2)
        self.AI = AI
    
    #checks if the flame collides with any obstacles
    def collideWithObstacles(self, obstacles):     
        hits = pg.sprite.spritecollide(self, obstacles, False)
        if len(hits) > 0:
            return True

    def update(self):
        timeNow = pg.time.get_ticks()
        if timeNow - self.lastUpdate > self.frameRate:
            self.lastUpdate = timeNow
            self.currentFrame += 1
            if self.currentFrame == len(self.game.explFrames):
                if self.AI:
                    print('here')
                    self.game.AIPlayer.hiding = False
                    self.game.AIPlayer.standing = False
                self.kill()
            else:
                self.image = self.game.explFrames[self.currentFrame]