import pygame as pg
from settings import *
import decimal 

vec = pg.math.Vector2

#helper function for rounding
def roundHalfUp(d):
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()
    
    def getImage(self, x, y, width, height):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pg.transform.scale(image, (TILESIZE, TILESIZE))
        return image

class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.players
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.standing = True
        self.backward = False
        self.forward = True
        self.left = False
        self.right = False
        self.walkCount = 0
        self.lastUpdate = 0 #for setting animation speed
        self.canDropBomb = True
        self.loadImages()
        self.image = self.frontFrames[0]
        self.image.set_colorkey(PLAYERBG)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.bombQuota = 1
        self.speed = 125
        self.range = 1
        self.frameRate = 100
        
    def loadImages(self):
        frontFrames = [self.game.playerSpritesheet.getImage(20, 13, 15, 22),
                       self.game.playerSpritesheet.getImage(36, 13, 15, 22),
                       self.game.playerSpritesheet.getImage(3, 13, 15, 22)] 
        self.frontFrames = []                  
        for frame in frontFrames:
            frame.set_colorkey(PLAYERBG)
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.frontFrames.append(frame)

        backFrames = [self.game.playerSpritesheet.getImage(68, 13, 15, 22),
                      self.game.playerSpritesheet.getImage(83, 13, 15, 22),
                      self.game.playerSpritesheet.getImage(52, 13, 15, 22)]
        self.backFrames = []
        for frame in backFrames:
            frame.set_colorkey(PLAYERBG)
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.backFrames.append(frame)
            
        rightFrames = [self.game.playerSpritesheet.getImage(67, 37, 16, 22),
                       self.game.playerSpritesheet.getImage(84, 37, 15, 22),
                       self.game.playerSpritesheet.getImage(52, 37, 15, 22),]
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
        if keys[pg.K_UP]:
            self.vel.y = -self.speed
            self.standing = False
            self.forward = False
            self.backward = True
            self.right = False
            self.left = False

        elif keys[pg.K_DOWN]:
            self.vel.y = self.speed
            self.standing = False
            self.forward = True
            self.backward = False
            self.right = False
            self.left = False
    
        elif keys[pg.K_RIGHT]:
            self.vel.x = self.speed
            self.standing = False
            self.forward = False
            self.backward = False
            self.right = True
            self.left = False
        
        elif keys[pg.K_LEFT]:
            self.vel.x = -self.speed
            self.standing = False
            self.forward = False
            self.backward = False
            self.right = False
            self.left = True

        else:
            self.standing = True
            self.walkCount = 0

    #prevents the player from walking into obstacles 
    def collideWithObstacles(self, dir, obstacles):
        if dir == 'x':
            hits = pg.sprite.spritecollide(self, obstacles, False)
            if hits:
                if self.vel.x > 0:
                    self.pos.x = hits[0].rect.left - self.rect.width
                if self.vel.x < 0:
                    self.pos.x = hits[0].rect.right
                self.vel.x = 0
                self.rect.x = self.pos.x
        if dir == 'y':
            hits = pg.sprite.spritecollide(self, obstacles, False)
            if hits:
                if self.vel.y > 0:
                    self.pos.y = hits[0].rect.top - self.rect.height
                if self.vel.y < 0:
                    self.pos.y = hits[0].rect.bottom
                self.vel.y = 0
                self.rect.y = self.pos.y
    
    def placeBomb(self):
        self.newBomb = Bomb(self.game, roundHalfUp(self.pos.x/TILESIZE), 
                        roundHalfUp(self.pos.y/TILESIZE))
        self.bombQuota -= 1

    
    def droppingBomb(self):
        #allows player to walk out of the tile before checking for collison with the bomb
        #prevents player from dropping more than one bomb at the same spot
        if ((self.rect.right < self.newBomb.rect.left or 
             self.rect.left > self.newBomb.rect.right) or
            (self.rect.top > self.newBomb.rect.bottom or
             self.rect.bottom < self.newBomb.rect.top)):
            self.game.tempBombs.remove(self.newBomb)
            self.game.bombs.add(self.newBomb)
            self.canDropBomb = True
        else:
            self.canDropBomb = False
    
    #kills the player if collides with flames
    def isKilled(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()
        
    def update(self):
        self.animate()
        self.getKeys()
        self.pos += self.vel * self.game.dt
        if len(self.game.tempBombs) >= 1:
            self.droppingBomb()
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        self.collideWithObstacles('x', self.game.solidBlocks)
        self.collideWithObstacles('y', self.game.solidBlocks)
        self.collideWithObstacles('x', self.game.bombs)
        self.collideWithObstacles('y', self.game.bombs)
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

class SolidBlock(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.solidBlocks
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.solidBlImg
        self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y 
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE    

class ExplodableBlock(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.explodableBlocks
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.explodableBlImg
        self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y 
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE   
    
    #explodes the block if collide with flames
    def explode(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()
    
    def update(self):
        self.explode()

class Bomb(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.tempBombs
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
        self.range = game.player.range
    
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
        self.removeBombs()
     
    #removes the Bomb after a period of time
    def removeBombs(self):
        if self.time > 50:
            self.explodeBomb()
            self.kill()
            self.game.player.bombQuota += 1 
    
    #creates explosions based on the player's flame range
    #flames cannot break through solid blocks
    def explodeBomb(self):
        Explosion(self.game, self.x, self.y) #center
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x, self.y - i) #up
            if flame.collideWithObstacles():
                flame.kill()
                break
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x, self.y + i) #down
            if flame.collideWithObstacles():
                flame.kill()
                break
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x + i, self.y) #right
            if flame.collideWithObstacles():
                flame.kill()
                break
        for i in range(1, self.range+1):
            flame = Explosion(self.game, self.x - i, self.y) #left
            if flame.collideWithObstacles():
                flame.kill()
                break
             
class Explosion(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.explosion
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.explFrames[0]
        self.currentFrame = 0
        self.lastUpdate = 0
        self.frameRate = 100
        self.rect = self.image.get_rect()
        self.rect.center = (x*TILESIZE + TILESIZE/2, y*TILESIZE + TILESIZE/2)
    
    #checks if the flame collides with any obstacles
    def collideWithObstacles(self):     
        hits = pg.sprite.spritecollide(self, self.game.solidBlocks, False)
        if len(hits) > 0:
            return True

    def update(self):
        self.collideWithObstacles()
        timeNow = pg.time.get_ticks()
        if timeNow - self.lastUpdate > self.frameRate:
            self.lastUpdate = timeNow
            self.currentFrame += 1
            if self.currentFrame == len(self.game.explFrames):
                self.kill()
            else:
                self.image = self.game.explFrames[self.currentFrame]

class Powerups(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.powerups
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.center = (x*TILESIZE + TILESIZE/2, y*TILESIZE + TILESIZE/2)

        
class BombPowerup(Powerups):
    def __init__(self, game, x, y):
        self.game = game
        self.image = self.game.bombPowerupImg
        self.image = pg.transform.scale(self.image, (POWERUPSIZE, POWERUPSIZE))
        super().__init__(game, x, y)
    
    def update(self):
        hits = pg.sprite.spritecollide(self, self.game.players, False)
        if len(hits) > 0 and self.game.player.bombQuota < 10:
            self.game.player.bombQuota += 1
            self.kill()

class SpeedPowerup(Powerups):
    def __init__(self, game, x, y):
        self.game = game
        self.image = self.game.speedPowerupImg
        self.image = pg.transform.scale(self.image, (POWERUPSIZE, POWERUPSIZE))
        super().__init__(game, x, y)
    
    def update(self):
        hits = pg.sprite.spritecollide(self, self.game.players, False)
        if len(hits) > 0 and self.game.player.speed < 400:
            self.game.player.speed += 25
            self.kill()
    
class FlamePowerup(Powerups):
    def __init__(self, game, x, y):
        self.game = game
        self.image = self.game.flamePowerupImg
        self.image = pg.transform.scale(self.image, (POWERUPSIZE, POWERUPSIZE))
        super().__init__(game, x, y)

    def update(self):
        hits = pg.sprite.spritecollide(self, self.game.players, False)
        if len(hits) > 0 and self.game.player.range < 4:
            self.game.player.range += 1
            self.kill()
    
        
    
        
        
        
        