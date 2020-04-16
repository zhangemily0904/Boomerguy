import pygame as pg
from settings import *
from sprites import *
import copy

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
            self.path.append(vec(current.x, current.y)*TILESIZE)
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