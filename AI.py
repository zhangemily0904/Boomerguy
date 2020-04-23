import pygame as pg
from settings import *
from bomb import *
import copy

#This code is inspired from: http://programarcadegames.com/python_examples/en/sprite_sheets/
class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()
    
    def getImage(self, x, y, width, height):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pg.transform.scale(image, (TILESIZE, TILESIZE))
        return image

vec = pg.math.Vector2

class Tile(object):
    def __init__(self, x, y, reachable, explodable):
        self.x = x
        self.y = y
        self.reachable = reachable
        self.explodable = explodable
        self.g = 0 #distance from start to current
        self.h = 0 #distance from current to end
        self.f = 0 #g + h
        self.parent = None
    
    def __repr__(self):
        return f'Tile{self.x, self.y}'

class Astar(object):
    def __init__(self, game, start, end, allSolid):
        self.openedList = []
        self.closedList = set()
        self.tiles = []
        self.allSolid = allSolid
        for row in range(len(game.tilesMap)):
            temp = []
            for col in range(len(game.tilesMap[0])):
                if self.allSolid:
                    if game.tilesMap[row][col] == 'S' or game.tilesMap[row][col] == 'E': 
                        reachable = False
                        explodable = False
                    else: 
                        reachable = True
                        explodable = False
                else:
                    if game.tilesMap[row][col] == 'S': reachable = False 
                    else: reachable = True
                    if game.tilesMap[row][col] == 'E': explodable = True
                    else: explodable = False
                temp.append(Tile(col, row, reachable, explodable))
            self.tiles.append(temp)
        self.start = self.getTile(int(start[0]), int(start[1]))
        self.end = self.getTile(int(end[0]), int(end[1]))
    
    def getTile(self, x, y):
        return self.tiles[y][x]

    def getChildren(self, current):
        children = []
        for pos in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            newX = current.x + pos[0]
            newY = current.y + pos[1]
            if (newX < GRIDWIDTH and newX >= 0 and
               newY < GRIDHEIGHT and newY >= 0):
                child = self.getTile(newX, newY)
                children.append(child)
        return children

    def updateChild(self, child, current):
        if child.explodable:
            child.g = current.g + 2
        else:
            child.g = current.g + 1
        child.h = abs(self.end.x - child.x) + abs(self.end.y - child.y)
        child.f = child.g + child.h
        child.parent = current
    
    def getPath(self, current):
        self.path = []
        while current != None:
            self.path.append(vec(current.x, current.y) * TILESIZE)
            current = current.parent
        self.path = self.path[::-1]
        self.path.pop(0)

    def findPath(self): #main
        self.openedList.append(self.start)
        while len(self.openedList) > 0:
            current = self.openedList[0]
            currentIndex = 0
            for index, item in enumerate(self.openedList):
                if item.f < current.f:
                    current = item
                    currentIndex = index
            self.openedList.pop(currentIndex) 
            self.closedList.add(current)

            if current == self.end:
                self.getPath(current)
                return self.path

            children = self.getChildren(current)
            for child in children:
                if child.reachable and child not in self.closedList: 
                    if child in self.openedList:
                        if current.g + 1 < child.g:  
                            self.updateChild(child, current)
                    else:
                        self.updateChild(child, current)
                        self.openedList.append(child)

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
        self.lastUpdate2 = 0 #for setting path generation speed
        self.loadImages()
        self.image = self.frontFrames[0]
        self.image.set_colorkey(PLAYERBG)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        print(f'pos: {x,y}')
        print(f'rect: {self.rect.x, self.rect.y}')
        self.bombsLeft = 1
        self.speed = 10
        self.range = 1
        self.frameRate = 100
        self.path = Astar(self.game, (self.x, self.y), (self.game.player.x, self.game.player.y), False).findPath()
        self.distance = ((self.x-self.game.player.x)**2 + (self.y-self.game.player.y)**2)**0.5
        print('original' + f'{self.x, self.y}' + f'{self.path}')
        self.target = self.path[0]
        self.radius = 50
        self.hiding = False
        self.onBomb = False
        
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
        target = (int((self.target[1])//TILESIZE), int((self.target[0])//TILESIZE))
        distY = self.y - self.game.player.y 
        distX = self.x - self.game.player.x
        self.x, self.y = int(self.x), int(self.y)
        if (((distY == 0 and abs(distX) ==1) or (distX == 0 and abs(distY) ==1) or (self.game.tilesMap[target[0]][target[1]] == 'E')) 
            and (self.bombsLeft>0 and self.game.tilesMap[self.y][self.x] == '-'
            and self.game.tilesMap[self.y-1][self.x] != 'B' and self.game.tilesMap[self.y+1][self.x] != 'B'
            and self.game.tilesMap[self.y][self.x-1] != 'B' and self.game.tilesMap[self.y][self.x+1] != 'B')):
            self.newBomb = Bomb(self.game, self.x, self.y, self.range, True, None)
            self.game.tilesMap[self.y][self.x] = 'B'
            self.runAway(self.newBomb)
            print('running away')
            self.bombsLeft -= 1
            self.onBomb = True
            self.game.tempBombsAI.add(self.newBomb)
        
    def droppingBomb(self):
        if ((self.rect.right < self.newBomb.rect.left or 
             self.rect.left > self.newBomb.rect.right) or
            (self.rect.top > self.newBomb.rect.bottom or
             self.rect.bottom < self.newBomb.rect.top)):
            self.onBomb = False
            self.game.bombsAI.add(self.newBomb)


    def runAway(self, bomb):
        if (bomb.y - self.y == 0 and bomb.x - self.x == 0):
            wrongDir = None
        elif (bomb.y - self.y == 0):
            if bomb.x < self.x:
                wrongDir= 'left' 
            elif bomb.x > self.x:
                wrongDir = 'right'
        elif (bomb.x - self.x == 0):
            if bomb.y < self.y:
                wrongDir = 'up'
            elif bomb.y > self.y:
                wrongDir = 'down'

        for direction in ['left', 'right', 'up', 'down']:
            if wrongDir != None and direction == wrongDir:
                continue
            emptySpaces = 0
            for i in range(1, GRIDWIDTH):
                if direction == 'right': #right
                    x = self.x + i
                    y = self.y
                    neighbors = [(self.x+i, self.y+1), (self.x+i, self.y-1)]
                elif direction == 'left': #left
                    x = self.x - i
                    y = self.y 
                    neighbors = [(self.x-i, self.y+1), (self.x-i, self.y-1)]
                elif direction == 'down': #down
                    x = self.x
                    y = self.y + i
                    neighbors = [(self.x+1, self.y+i), (self.x-1, self.y+i)]
                else: #up
                    x = self.x
                    y = self.y - i
                    neighbors = [(self.x+1, self.y-i), (self.x-1, self.y-i)]
                
                #look at the diagonals for empty spaces 
                for neighbor in neighbors:
                    if self.game.tilesMap[neighbor[1]][neighbor[0]] == '-':
                        target = (neighbor[0], neighbor[1])
                        path = Astar(self.game, (self.x, self.y), target, True).findPath()
                        if path != None:
                            self.path = path
                            print(f'hiding: {self.path}')
                            self.hiding = True
                            return 

                # look at the four directions for empty spaces 
                if (x < GRIDWIDTH and x > 0 and 
                    y < GRIDHEIGHT and y > 0 and
                    self.game.tilesMap[y][x] == '-'):
                    emptySpaces += 1
                    if emptySpaces > self.range:
                        path = Astar(self.game, (self.x, self.y), (x,y), False).findPath()
                        if path != None:
                            self.path = path
                            print(f'hiding: {self.path}')
                            self.hiding = True
                            return
                else: break
                         
    def moveToTarget(self):
        if not self.standing:
            self.target = self.path[0]
            print(f'current: {self.pos}')
            print(f'target: {self.target}')
            self.vel = (self.target - self.pos)
            dist = self.vel.length()
            
            if dist != 0:
                self.vel.normalize_ip()
                self.checkDir()
                if dist < self.radius:
                    self.vel *= (dist/self.radius * self.speed)
                else:
                    self.vel *=  self.speed

            print(f'velocity: {self.vel}')
            if dist <= 2: 
                if len(self.path) > 1:
                    self.pos = self.target
                    self.path.pop(0)
                    self.target = self.path[0]
                    self.vel = (self.target - self.pos)
                    self.vel.normalize_ip()
                else:
                    self.vel = vec(0,0)
                    self.standing = True
                    self.walkCount = -1

    def generateNewPath(self):
        path = Astar(self.game, (self.x, self.y), (self.game.player.x, self.game.player.y), False).findPath()
        if path != None:
            self.path = path
            self.targetIndex = 0

    def isKilled(self):
        hits = pg.sprite.spritecollide(self, self.game.explosion, False)
        if len(hits) > 0:
            self.kill()
            self.game.player.win = True
            self.game.playing = False

    def update(self):
        self.distance = ((self.x-self.game.player.x)**2 + (self.y-self.game.player.y)**2)**0.5
        self.checkDir()
        self.animate()
        self.moveToTarget()
        self.placeBomb()
        if self.onBomb:
            self.droppingBomb()

        for bomb in self.game.bombs:
            if ((self.x - bomb.x == 0 and abs(self.y-bomb.y) <= self.game.player.range) or 
                (self.y - bomb.y == 0 and abs(self.x-bomb.x) <= self.game.player.range)):
                if not self.hiding:
                    bomb.run = True
                    bomb.AI = True
                    self.runAway(bomb)

        timeNow = pg.time.get_ticks()
        if timeNow - self.lastUpdate2 > 2000:
            self.lastUpdate2 = timeNow
            if not self.hiding:
                self.generateNewPath()
                print(f'generating new path {self.path}')

        if self.game.tilesMap[self.y][self.x] == 'B':
            for dir in [(0,1), (0,-1), (1,0), (-1,0)]:
                if (self.game.tilesMap[self.y-1][self.x] != 'B' or self.game.tilesMap[self.y+1][self.x] != 'B'
                    or self.game.tilesMap[self.y][self.x-1] != 'B' or self.game.tilesMap[self.y][self.x+1] != 'B'):
                    self.standing = True
                    break

        self.pos += self.vel
        self.rect.x = self.pos.x + (TILESIZE-PLAYERSIZE)/2
        self.rect.y = self.pos.y + (TILESIZE-PLAYERSIZE)/2
        self.x = int(self.rect.center[0]//TILESIZE)
        self.y = int(self.rect.center[1]//TILESIZE)
        self.isKilled()
        self.collideWithObstacles('x', self.game.solidBlocks)
        self.collideWithObstacles('y', self.game.solidBlocks)
        self.collideWithObstacles('x', self.game.bombsAI)
        self.collideWithObstacles('y', self.game.bombsAI)
        self.collideWithObstacles('x', self.game.tempBombs)
        self.collideWithObstacles('y', self.game.tempBombs)
        self.collideWithObstacles('x', self.game.bombs)
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


