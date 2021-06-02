#!/usr/bin/python
# -*- coding:utf8 -*-

from klasses.Game import Game
from klasses.Player import Player
from util import LoadPickle, playerMarkToDir, writeToPickle, gameMarkToSeason
from stats_nba.Game_nba import Game_nba
import pandas as pd
import numpy as np
np.set_printoptions(suppress=True)
pd.options.display.expand_frame_repr = False
pd.options.display.width = 50
RoF = 0

gm = '202012220BRK'
game = Game(gm, 'playoff' if RoF else 'regular')
record = game.game_scanner()
# for i in record:
#     print(i)
record = game.game_analyser(record)
record = game.game_analyser(record, T=1)
ss = gameMarkToSeason(gm)
rof = 'playoff' if RoF else 'regular'
season_dir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/%s/' % (ss, rof)
writeToPickle(season_dir + gm + '_scanned.pickle', record)
for i in record:
    print(i)
# print()

game.find_time_series(record)
game.start_of_quarter(record)

# 判断胜者
scores = [game.bxscr[0][x][0] for x in game.bxscr[0]]
print(list(game.bxscr[0]))
print(scores)
print('主队胜' if scores[0] < scores[1] else '客队胜')

rot = game.rotation(record)
for i in rot:
    print(i)
# print()
bxs, rot = game.replayer(record, rot)
# for i in rot:
#     print(i)

# for i in range(2):
#     for k in bxs.tdbxs[i][0]:
#         if k != 'team':
#             print(k, '\t', list(bxs.tdbxs[i][0][k][0]))
#         else:
#             print(k, '\t\t', list(bxs.tdbxs[i][0][k]))
#     print()

print()
# for i in game.nba_lastMins:
#     print(i)

print(bxs.tdbxs[0][0])
print(bxs.tdbxs[1][0])

# for i in record:
#     print(i)


# gn = Game_nba(game.nba_file, game.ss)
#
# if gn.nba_actions:
#     gn.game_scanner()
#     for i in gn.record:
#         print(i)

# bxs = game.boxscores(record)
# for i in bxs:
#     print(i)
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
