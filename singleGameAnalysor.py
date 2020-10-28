#!/usr/bin/python
# -*- coding:utf8 -*-
from klasses.Game import Game
from klasses.miscellaneous import MPTime


gm = '201305060SAS'
game = Game(gm, 'playoffs')
# print(game.teamplyrs())
_, _, _, record = game.game_scanner(gm)
for i in record:
    # if 'MK' in i or 'MS' in i:
        print(i)
# game.game_analyser(gm, record)
# game.pace(gm, record)
game.find_time_series(gm, record)

# a = MPTime('47:36.1')
# b = MPTime('47:36.0')
# print(a >= b)    # True
