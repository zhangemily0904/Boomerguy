import pygame as pg
from settings import *

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
        if len(hits) > 0:
            hits[0].bombsLeft += 1
            self.kill()
        hits = pg.sprite.spritecollide(self, self.game.AI, False)
        if len(hits) > 0 and self.game.AIPlayer.bombsLeft < 10:
            self.game.AIPlayer.bombsLeft += 1
            self.kill()

class SpeedPowerup(Powerups):
    def __init__(self, game, x, y):
        self.game = game
        self.image = self.game.speedPowerupImg
        self.image = pg.transform.scale(self.image, (POWERUPSIZE, POWERUPSIZE))
        super().__init__(game, x, y)
    
    def update(self):
        hits = pg.sprite.spritecollide(self, self.game.players, False)
        if len(hits) > 0:
            hits[0].speed += 25
            self.kill()
        hits = pg.sprite.spritecollide(self, self.game.AI, False)
        if len(hits) > 0:
            self.game.AIPlayer.speed += 3
            self.kill()
    
class FlamePowerup(Powerups):
    def __init__(self, game, x, y):
        self.game = game
        self.image = self.game.flamePowerupImg
        self.image = pg.transform.scale(self.image, (POWERUPSIZE, POWERUPSIZE))
        super().__init__(game, x, y)

    def update(self):
        hits = pg.sprite.spritecollide(self, self.game.players, False)
        if len(hits) > 0:
            hits[0].range += 1
            self.kill()
        hits = pg.sprite.spritecollide(self, self.game.AI, False)
        if len(hits) > 0 and self.game.AIPlayer.range < 4:
            self.game.AIPlayer.range += 1
            self.kill()
    