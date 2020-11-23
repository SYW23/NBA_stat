#!/usr/bin/python
# -*- coding:utf8 -*-

from klasses.Game import Game
from klasses.Player import Player
from util import LoadPickle, playerMarkToDir
import pandas as pd
import numpy as np
np.set_printoptions(suppress=True)
pd.options.display.expand_frame_repr = False
pd.options.display.width = 50
RoF = ['regular', 'playoff']

gm = '201710250LAL.pickle'
game = Game(gm[:-7], 'regular')
_, _, _, record = game.game_scanner()
# 判断胜者
scores = [game.bxscr[0][x][0] for x in game.bxscr[0]]
print(scores)
print(int(scores[0] < scores[1]))

for i in record:
    print(i)
rot = game.rotation(record)
for i in rot:
    print(i)
# for i in record:
#     print(i)
# game.find_time_series(record)
# bx = game.boxscores(record)[:, 6, :]
# print(bx)
# print(game.teamplyrs())
# ttl = [game.bxscr[1][0][-1], game.bxscr[1][1][-1]]
# print(ttl)

# i = 0
# pm = 'jamesle01'
# pmdir = playerMarkToDir(pm, RoF[i], tp=1)
# plyr_ss = LoadPickle('./data/playerSeasonAverage.pickle')
# lg_ss = LoadPickle('./data/leagueSeasonAverage.pickle')
# cr_as = LoadPickle(pmdir)
# print(cr_as['Season'].values)
# print('2019_2020' in cr_as['Season'].values)
# print(cr_as[cr_as['Season'] == '2019_2020'][:1])
# print(cr_as[cr_as['Season'] == '2019_2020'][:1]['G'].values[0][:-3])
# print(cr_as[cr_as['Season'] == '2019_2020'][:1]['MP'].values[0])
# pmdir = playerMarkToDir(pm, RoF[i])
# plyr = Player('jamesle01', 'regular')
# # print(plyr.data)
# ssgms = plyr.getSeason('2019_2020')
# print(ssgms)
# print(ssgms[2:3]['MP'].values[0])
#
# enforce = LoadPickle('./data/Enforce/playerBlockEnforce.pickle')
# print(enforce['jamesle01'][1][-1]['2019_2020'])
#
# print('=' * 50)
# print(plyr_ss['jamesle01']['2019_2020'][1][0][-1][2][6] / plyr_ss['jamesle01']['2019_2020'][1][0][0])
# print(lg_ss['2019_2020'][1][-1][2][6] / lg_ss['2019_2020'][1][0] / 2)
# print(lg_ss['2019_2020'][0][0], lg_ss['2019_2020'][0][1])
# print(lg_ss['2019_2020'][1][0], lg_ss['2019_2020'][1][1])
# print('=' * 50)
# lg_season = LoadPickle('./data/Enforce/seasonBlockEnforceRecord.pickle')
# print(lg_season[-2]['2019_2020'][0][2])
# print(lg_season[1]['2019_2020'][0][2])
