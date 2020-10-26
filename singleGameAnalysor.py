#!/usr/bin/python
# -*- coding:utf8 -*-
from klasses.Game import Game


gm = '201712100NOP'
game = Game(gm, 'regular')
_, _, _, record = game.game_scanner(gm)
for i in record:
    print(i)
# game.game_analyser(gm, record)
# game.pace(gm, record)
game.find_time_series(gm, record)
