import os
import sys
from operator import itemgetter
sys.path.append('../')
from stats_nba.Game_nba import Game_nba
from util import LoadText, writeToPickle


predir = 'D:/sunyiwu/stat/data_nba/origin/'
for season in range(2016, 2020):
    ss = '%d_%d' % (season, season + 1)
    gms = os.listdir(predir + ss)
    for gm in gms[0:1]:
        print(gm)
        game = Game_nba(gm, ss)
        
        res = game.nba_actions
        # print(game.rtID)
        # print(game.rtTri)
        # for k in game.stats['awayTeam']:
        #     print(k, game.stats['awayTeam'][k])
        #    print()