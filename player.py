import pygame as pg
import decimal
from bomb import *
from settings import *

vec = pg.math.Vector2

#helper function for rounding
#this code is taken from: https://www.cs.cmu.edu/~112/notes/notes-variables-and-functions.html
def roundHalfUp(d):
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

#This code is inspired from: http://programarcadegames.com/python_examples/en/sprite_sheets/
class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()
    
    def getImage(self, x, y, width, height):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pg.transform.scale(image, (TILESIZE, TILESIZE))
        return image

class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y, upKey, downKey, leftKey, rightKey, bombKey, spriteCoords, playerNum = 1, color = WHITE):
        self.groups = game.allSprites, game.players
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.spriteL = spriteCoords[0]
        self.spriteT = spriteCoords[1]
        self.spriteW = spriteCoords[2]
        self.spriteH = spriteCoords[3]
        self.loadImages()
        self.image = self.frontFrames[0]
        self.image.set_colorkey(PLAYERBG)
        self.rect = self.image.get_rect()
        self.upKey = upKey
        self.downKey = downKey
        self.leftKey = leftKey
        self.rightKey = rightKey
        self.bombKey = bombKey
        self.standing = True
        self.backward = False
        self.forward = True
        self.left = False
        self.right = False
        self.walkCount = 0
        self.lastUpdate = 0 #for setting animation speed
        self.x = x
        self.y = y
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.bombsLeft = 1
        self.speed = 125
        self.range = 1
        self.frameRate = 100
        self.onBomb = False
        self.win = False
        self.playerNum = playerNum
        self.color = color
        
    def loadImages(self):
        frontFrames = [self.game.playerSpritesheet.getImage(self.spriteL+17, self.spriteT, self.spriteW, self.spriteH),
                       self.game.playerSpritesheet.getImage(self.spriteL+33, self.spriteT, self.spriteW, self.spriteH),
                       self.game.playerSpritesheet.getImage(self.spriteL, self.spriteT, self.spriteW, self.spriteH)] 
        self.frontFrames = []                  
        for frame in frontFrames:
            frame.set_colorkey(PLAYERBG)
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.frontFrames.append(frame)

        backFrames = [self.game.playerSpritesheet.getImage(self.spriteL+65, self.spriteT, self.spriteW, self.spriteH),
                      self.game.playerSpritesheet.getImage(self.spriteL+80, self.spriteT, self.spriteW, self.spriteH),
                      self.game.playerSpritesheet.getImage(self.spriteL+49, self.spriteT, self.spriteW, self.spriteH)]
        self.backFrames = []
        for frame in backFrames:
            frame.set_colorkey(PLAYERBG)
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.backFrames.append(frame)
            
        rightFrames = [self.game.playerSpritesheet.getImage(self.spriteL+64, self.spriteT+24, self.spriteW+1, self.spriteH),
                       self.game.playerSpritesheet.getImage(self.spriteL+81, self.spriteT+24, self.spriteW, self.spriteH),
                       self.game.playerSpritesheet.getImage(self.spriteL+49, self.spriteT+24, self.spriteW, self.spriteH),]
        self.leftFrames = []
        self.rightFrames = []
        for frame in rightFrames:
            frame.set_colorkey(PLAYERBG)
            #flips horizontally
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.rightFrames.append(frame)
            self.leftFrames.append(pg.transform.flip(frame, True, False))
                            
    def getKeys(self):
        self.vel = vec(0,0)
        keys = pg.key.get_pressed()
        if keys[self.upKey]:
            self.vel.y = -self.speed
            self.standing = False
            self.forward = False
            self.backward = True
            self.right = False
            self.left = False
        elif keys[self.downKey]:
            self.vel.y = self.speed
            self.standing = False
            self.forward = True
            self.backward = False
            self.right = False
            self.left = False
        elif keys[self.rightKey]:
            self.vel.x = self.speed
            self.standing = False
            self.forward = False
            self.backward = False
            self.right = True
            self.left = False
        elif keys[self.leftKey]:
            self.vel.x = -self.speed
            self.standing = False
            self.forward = False
            self.backward = False
            self.right = False
            self.left = True
        else:
            self.standing = True
            self.walkCount = 0
        
        if keys[self.bombKey] and self.bombsLeft > 0 and self.game.tilesMap[int(self.y)][int(self.x)] == '-':
            self.placeBomb()

    #prevents the player from walking into obstacles
    #This code is inspired from: https://www.youtube.com/watch?v=ajR4BZBKTr4
    def collideWithObstacles(self, direction, obstacles):
        if direction == 'x':
            hits = pg.sprite.spritecollide(self, obstacles, False)
            #the sprite that the player collides with
            if len(hits)>0:
                sprite = hits[0]
                if self.vel.x > 0:
                    self.pos.x = sprite.rect.left - self.rect.width
                if self.vel.x < 0:
                    self.pos.x = sprite.rect.right
                self.x = self.pos.x//TILESIZE
                self.vel.x = 0
                self.rect.x = self.pos.x
        if direction == 'y':
            hits = pg.sprite.spritecollide(self, obstacles, False)
            #the sprite that the player collides with
            if len(hits)>0:
                sprite = hits[0]
                if self.vel.y > 0:
                    self.pos.y = hits[0].rect.top - self.rect.height
                if self.vel.y < 0:
                    self.pos.y = hits[0].rect.bottom
                self.y = self.pos.y//TILESIZE
                self.vel.y = 0
                self.rect.y = self.pos.y
    
    def placeBomb(self):
        self.newBomb = Bomb(self.game, roundHalfUp(self.pos.x/TILESIZE), 
                        roundHalfUp(self.pos.y/TILESIZE), self.range, False, self)
        self.game.tilesMap[int(self.y)][int(self.x)] = 'B'
        self.bombsLeft -= 1
        self.game.tempBombs.add(self.newBomb)
        self.onBomb = True

    def droppingBomb(self):
        #allows player to walk out of the tile before checking for collison with the bomb
        #prevents player from dropping more than one bomb at the same spot
        if ((self.rect.right < self.newBomb.rect.left or 
             self.rect.left > self.newBomb.rect.right) or
            (self.rect.top > self.newBomb.rect.bottom or
             self.rect.bottom < self.newBomb.rect.top)):
            self.game.bombs.add(self.newBomb)
            self.onBomb = False
            
    
    #kills the player if collides with flames
    def isKilled(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()
            if self.game.singlePl:
                self.win = False
                self.game.playing = False
            else:
                self.game.ranking.append((self.playerNum, self.color))
                if len(self.game.players) <= 1:
                    self.game.playing = False
            
    def update(self):
        self.animate()
        self.getKeys()
        self.pos += self.vel * self.game.dt
        if self.onBomb:
            self.droppingBomb()
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        self.x = int(self.rect.center[0]//TILESIZE)
        self.y = int(self.rect.center[1]//TILESIZE)
        self.collideWithObstacles('x', self.game.solidBlocks)
        self.collideWithObstacles('y', self.game.solidBlocks)
        self.collideWithObstacles('x', self.game.bombs)
        self.collideWithObstacles('y', self.game.bombs)
        self.collideWithObstacles('x', self.game.bombsAI)
        self.collideWithObstacles('y', self.game.bombsAI)
        self.collideWithObstacles('x', self.game.explodableBlocks)
        self.collideWithObstacles('y', self.game.explodableBlocks)
        self.isKilled()

    def animate(self):
        if self.standing:
            if self.forward:
                self.image = self.frontFrames[0]
            elif self.backward:
                self.image = self.backFrames[0]
            elif self.right:
                self.image = self.rightFrames[0]
            else:
                self.image = self.leftFrames[0]
        else:
            timeNow = pg.time.get_ticks()
            if timeNow - self.lastUpdate > self.frameRate:
                self.lastUpdate = timeNow
                if self.forward:
                    self.walkCount = (self.walkCount + 1) % len(self.frontFrames)
                    self.image = self.frontFrames[self.walkCount]
                elif self.backward:
                    self.walkCount = (self.walkCount + 1) % len(self.backFrames)
                    self.image = self.backFrames[self.walkCount]
                elif self.right:
                    self.walkCount = (self.walkCount + 1) % len(self.rightFrames)
                    self.image = self.rightFrames[self.walkCount]
                else:
                    self.walkCount = (self.walkCount + 1) % len(self.leftFrames)
                    self.image = self.leftFrames[self.walkCount]   