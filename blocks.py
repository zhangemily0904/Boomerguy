import pygame as pg
from settings import *

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