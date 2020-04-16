import pygame as pg
from settings import *
from AI import *
import decimal 
import queue

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
        self.x = x
        self.y = y
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.bombQuota = 1
        self.speed = 125
        self.range = 1
        self.frameRate = 100
        self.generateMap = True
        
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
                            
    def move(self):
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
                        roundHalfUp(self.pos.y/TILESIZE), self.range, False)
        self.bombQuota -= 1
        self.game.tempBombsPlayer.add(self.newBomb)

    def droppingBomb(self):
        #allows player to walk out of the tile before checking for collison with the bomb
        #prevents player from dropping more than one bomb at the same spot
        if ((self.rect.right < self.newBomb.rect.left or 
             self.rect.left > self.newBomb.rect.right) or
            (self.rect.top > self.newBomb.rect.bottom or
             self.rect.bottom < self.newBomb.rect.top)):
            self.game.bombs.add(self.newBomb)
            self.game.tempBombsPlayer.remove(self.newBomb)
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
        self.move()
        self.pos += self.vel * self.game.dt
        if len(self.game.tempBombsPlayer) > 0:
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

class AIPlayer(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.allSprites, game.AI
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
        self.x = x
        self.y = y
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.bombQuota = 1
        self.speed = 125
        self.range = 1
        self.frameRate = 100
        self.path = Astar(self.game, (self.x, self.y), (self.game.player.x, self.game.player.y), False).findPath()
        self.distance = ((self.x-self.game.player.x)**2 + (self.y-self.game.player.y)**2)**0.5
        print('original' + f'{self.x, self.y}' + f'{self.path}')
        self.path2 = None
        self.target = self.path[0]
        self.radius = 50
        self.hiding = False
        
    def loadImages(self):
        frontFrames = [self.game.playerSpritesheet.getImage(178, 13, 15, 22),
                       self.game.playerSpritesheet.getImage(194, 13, 15, 22),
                       self.game.playerSpritesheet.getImage(161, 13, 15, 22)] 
        self.frontFrames = []                  
        for frame in frontFrames:
            frame.set_colorkey(PLAYERBG)
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.frontFrames.append(frame)

        backFrames = [self.game.playerSpritesheet.getImage(226, 13, 15, 22),
                      self.game.playerSpritesheet.getImage(242, 13, 15, 22),
                      self.game.playerSpritesheet.getImage(210, 13, 15, 22)]
        self.backFrames = []
        for frame in backFrames:
            frame.set_colorkey(PLAYERBG)
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.backFrames.append(frame)
            
        rightFrames = [self.game.playerSpritesheet.getImage(225, 37, 16, 22),
                       self.game.playerSpritesheet.getImage(242, 37, 15, 22),
                       self.game.playerSpritesheet.getImage(210, 37, 15, 22),]
        self.leftFrames = []
        self.rightFrames = []
        for frame in rightFrames:
            frame.set_colorkey(PLAYERBG)
            #flips horizontally
            frame = pg.transform.scale(frame, (PLAYERSIZE, PLAYERSIZE))
            self.rightFrames.append(frame)
            self.leftFrames.append(pg.transform.flip(frame, True, False))

    def checkDir(self):
        if abs(self.target.y-self.pos.y)>1:
            if self.target.y < self.pos.y:
                self.standing = False
                self.forward = False
                self.backward = True
                self.right = False
                self.left = False
            else:
                self.standing = False
                self.forward = True
                self.backward = False
                self.right = False
                self.left = False
        elif abs(self.target.x-self.pos.x)>1:
            if self.target.x > self.pos.x:
                self.standing = False
                self.forward = False
                self.backward = False
                self.right = True
                self.left = False
            else:
                self.standing = False
                self.forward = False
                self.backward = False
                self.right = False
                self.left = True

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
        hits = pg.sprite.spritecollide(self, self.game.explodableBlocks, False)
        print(hits)
        print(f'candropbomb: {self.canDropBomb}')
        print(f'bombsLeft: {self.bombQuota}')
        if (((self.y - self.game.player.y == 0 and abs(self.x - self.game.player.x) <=2) or
           (self.x - self.game.player.x == 0 and abs(self.y - self.game.player.y) <=2) or
           (self.game.tilesMap[int(self.target.y//TILESIZE)][int(self.target.x//TILESIZE)] == 'E') or
           (len(hits)>0)) and self.canDropBomb and self.bombQuota > 0):
            print('placing bomb')
            path = self.hide()
            if path != None:
                self.newBomb = Bomb(self.game, self.x, self.y, self.range, True)
                self.bombQuota -= 1
                self.game.tempBombsAI.add(self.newBomb)
                self.path = path
           
    def droppingBomb(self):
        if ((self.rect.right < self.newBomb.rect.left or 
             self.rect.left > self.newBomb.rect.right) or
            (self.rect.top > self.newBomb.rect.bottom or
             self.rect.bottom < self.newBomb.rect.top)):
            self.game.tempBombsAI.remove(self.newBomb)
            self.game.bombsAI.add(self.newBomb)
            self.canDropBomb = True
        else:
            self.canDropBomb = False

    # def runAway(self, bomb):
    #     print(bomb.y, self.y)
    #     print(bomb.x, self.x)
    #     if (bomb.y - self.y == 0):
    #         print('left or right')
    #         if bomb.x < self.x:
    #             wrongDir= 'left' 
    #         elif bomb.x > self.x:
    #             wrongDir = 'right'
    #     elif (bomb.x - self.x == 0):
    #         print('up or down')
    #         if bomb.y < self.y:
    #             wrongDir = 'up'
    #         elif bomb.x > self.x:
    #             wrongDir = 'down'

    #     for direction in ['left', 'right', 'up', 'down']:
    #         if direction == wrongDir:
    #             continue
    #             print(direction)
    #         for i in range(1, GRIDWIDTH):
    #             print(i)
    #             if direction == 'right': #right
    #                 x = self.x + i
    #                 y = self.y
    #                 neighbors = [(self.x+i, self.y+1), (self.x+i, self.y-1)]
    #             elif direction == 'left': #left
    #                 x = self.x - i
    #                 y = self.y 
    #                 neighbors = [(self.x-i, self.y+1), (self.x-i, self.y-1)]
    #             elif direction == 'down': #down
    #                 x = self.x
    #                 y = self.y + i
    #                 neighbors = [(self.x+1, self.y+i), (self.x-1, self.y-i)]
    #             else: #up
    #                 x = self.x
    #                 y = self.y - i
    #                 neighbors = [(self.x+1, self.y-i), (self.x-1, self.y-i)]
                
    #             for neighbor in neighbors:
    #                 print(neighbor)
    #                 if self.game.tilesMap[neighbor[1]][neighbor[0]] == '-':
    #                     target = (neighbor[0],neighbor[1])
    #                     self.hiding = True
    #                     self.path = Astar(self.game, (self.x, self.y), target, False).findPath()
    #                     return
                
    #             print(self.game.tilesMap[y][x])
    #             print(f'location: {x,y}')
    #             if (x < GRIDWIDTH and x > 0 and 
    #                 y < GRIDHEIGHT and y > 0 and
    #                 self.game.tilesMap[y][x] == '-'):
    #                 emptySpaces += 1
    #                 print(f'dir: {direction}')
    #                 print(f'emptySpaces: {emptySpaces}')
    #                 if emptySpaces > self.range:
    #                     self.hiding = True
    #                     print('hiding2' + f'{self.x, self.y, self.pos}' + f'{self.path}')
    #                     self.path = Astar(self.game, (self.x, self.y), (x,y), False).findPath()
    #                     return
    #             else:
    #                 break

    def hide(self):
        for pos in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:   
            x = int(self.x + pos[0])
            y = int(self.y + pos[1])
            if (x < GRIDWIDTH and x >= 0 and y < GRIDHEIGHT and y >= 0 and 
                self.game.tilesMap[y][x] == '-'):
                path = Astar(self.game, (self.x, self.y), (x,y), True).findPath()
                if path != None:
                    self.path2 = self.path
                    self.hiding = True
                    return path              
        
        for dir in range(4):
            emptySpaces = 0
            for i in range(1, GRIDWIDTH):
                if dir == 0: #right
                    x = self.x + i
                    y = self.y 
                elif dir == 1: #left
                    x = self.x - i
                    y = self.y 
                elif dir == 2: #down
                    x = self.x
                    y = self.y + i
                else: #up
                    x = self.x
                    y = self.y - i
                
                if (x < GRIDWIDTH and x > 0 and 
                    y < GRIDHEIGHT and y > 0 and
                    self.game.tilesMap[y][x] == '-'):
                    emptySpaces += 1
                else: break

                if emptySpaces > self.range:
                    self.path2 = self.path
                    self.hiding = True
                    print('hiding2' + f'{self.x, self.y, self.pos}' + f'{self.path}')
                    return Astar(self.game, (self.x, self.y), (x,y), False).findPath()
                         
    def moveToTarget(self):
        if not self.standing:
            self.target = self.path[0]
            self.vel = (self.target - self.pos)
            dist = self.vel.length()

            if dist != 0:
                self.vel = self.vel.normalize()
                self.checkDir()
                if dist < self.radius:
                    self.vel *= dist/self.radius * self.speed
                else:
                    self.vel *= self.speed
            if dist < 2: 
                print(f'distance: {dist}') 
                if len(self.path) > 1:
                    if not self.hiding and self.distance >= 5:
                        path = self.generateNewPath()
                        if path != None:
                            self.path = path
                    # elif not self.hiding and self.distance <5:
                    #     path = self.runAway()
                    #     if path != None:
                    #         self.path = path
                    else: #continue on original path
                        self.path.pop(0)
                    self.target=self.path[0] 
                    print(f'target: {self.target}')
                    self.vel = (self.target - self.pos)
                    print(f'vel: {self.vel}')
                    dist = self.vel.length()
                    print(f'currentpos: {self.pos}')
                else:
                    self.vel = vec(0,0)
                    self.standing = True
                    self.walkCount = 0

    def generateNewPath(self):
        self.path = Astar(self.game, (self.x, self.y), (self.game.player.x, self.game.player.y), False).findPath()
    

    def isKilled(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()

    def restorePath(self):
        print('restoring path')
        #target x,y where u want to move to
        x = int(self.path2[0].x//TILESIZE)
        y = int(self.path2[0].y//TILESIZE)

        #gets shortest path to target location
        path = Astar(self.game, (self.x, self.y), (x,y), False).findPath()
        print(path)
        if path != None:
            self.path = path + self.path2[1:]
            self.target = self.path[0]
            print('toenemy' + f'{self.x, self.y, self.pos}' + f'{self.path}') 
    
    def isKilled(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()

    def update(self):
        self.distance = ((self.x-self.game.player.x)**2 + (self.y-self.game.player.y)**2)**0.5
        self.checkDir()
        self.animate()
        self.moveToTarget()
        # for bomb in self.game.bombs:
        #     dist = ((self.x-bomb.x)**2 + (self.y-bomb.y)**2)**0.5
        #     print(self.hiding)
        #     if dist <= 3 and not self.hiding:
        #         print('run')
        #         self.runAway(bomb)
        self.pos += self.vel * self.game.dt
        self.rect.x = self.pos.x + (TILESIZE-PLAYERSIZE)/2
        self.rect.y = self.pos.y + (TILESIZE-PLAYERSIZE)/2
        self.x = int(self.rect.center[0]//TILESIZE)
        self.y = int(self.rect.center[1]//TILESIZE)
        self.placeBomb()
        
        if len(self.game.tempBombsAI) > 0:
            self.droppingBomb()
        elif len(self.game.tempBombsAI) < self.bombQuota:
            self.canDropBomb = True
        
        self.isKilled()
        self.collideWithObstacles('x', self.game.solidBlocks)
        self.collideWithObstacles('y', self.game.solidBlocks)
        self.collideWithObstacles('x', self.game.bombsAI)
        self.collideWithObstacles('y', self.game.bombsAI)
        self.collideWithObstacles('x', self.game.bombs)
        self.collideWithObstacles('y', self.game.bombs)
        self.collideWithObstacles('x', self.game.explodableBlocks)
        self.collideWithObstacles('y', self.game.explodableBlocks)

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
    def update(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()
            self.game.tilesMap[self.y][self.x] = '-'

class Bomb(pg.sprite.Sprite):
    def __init__(self, game, x, y, range, AI):
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
            self.game.AIPlayer.bombQuota += 1
        else:
            self.kill()
            self.game.player.bombQuota += 1

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
                    self.game.AIPlayer.hiding = False
                    self.game.AIPlayer.restorePath()
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
        hits = pg.sprite.spritecollide(self, self.game.AI, False)
        if len(hits) > 0 and self.game.AIPlayer.bombQuota < 10:
            self.game.AIPlayer.bombQuota += 1
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
        hits = pg.sprite.spritecollide(self, self.game.AI, False)
        if len(hits) > 0 and self.game.AIPlayer.speed < 400:
            self.game.AIPlayer.speed += 25
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
        hits = pg.sprite.spritecollide(self, self.game.AI, False)
        if len(hits) > 0 and self.game.AIPlayer.range < 4:
            self.game.AIPlayer.range += 1
            self.kill()
    
