#!/usr/bin/python
# -*- coding:utf8 -*-

from klasses.Game import Game
from util import LoadPickle, playerMarkToDir
import pandas as pd
import numpy as np
np.set_printoptions(suppress=True)
pd.options.display.expand_frame_repr = False
pd.options.display.width = 50
RoF = ['regular', 'playoff']

# gm = '199701230VAN.pickle'
# game = Game(gm[:-7], 'regular')
# _, _, _, record = game.game_scanner(gm[:-7])
# for i in record:
#     print(i)
# game.find_time_series(gm, record)
# bx = game.boxscores(record)[:, 6, :]
# print(bx)

i = 0
pm = 'jamesle01'
pmdir = playerMarkToDir(pm, RoF[i], tp=1)
plyr_ss = LoadPickle('./data/playerSeasonAverage.pickle')
lg_ss = LoadPickle('./data/leagueSeasonAverage.pickle')
cr = LoadPickle(pmdir)
print(cr['Season'].values)
print('2019_2020' in cr['Season'].values)
print(cr[cr['Season'] == '2019_2020'][:1])
print(cr[cr['Season'] == '2019_2020'][:1]['G'].values[0][:-3])
print(cr[cr['Season'] == '2019_2020'][:1]['MP'].values[0])

enforce = LoadPickle('./data/Enforce/playerBlockEnforce.pickle')
print(enforce['jamesle01'][1][-1]['2019_2020'])

print('=' * 50)
print(plyr_ss['jamesle01']['2019_2020'][1][0][3][2][6] / plyr_ss['jamesle01']['2019_2020'][1][0][0])
print(lg_ss['2019_2020'][1][-1][2][6] / lg_ss['2019_2020'][1][0] / 2)
print('=' * 50)
lg_season = LoadPickle('./data/Enforce/seasonBlockEnforceRecord.pickle')
print(lg_season[-2]['2019_2020'][0][2])
print(lg_season[1]['2019_2020'][0][2])
