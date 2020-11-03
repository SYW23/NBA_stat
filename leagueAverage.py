#!/usr/bin/python
# -*- coding:utf8 -*-
import os
from tqdm import tqdm
import numpy as np
from klasses.Game import Game
from util import writeToPickle, gameMarkToDir, LoadPickle

regularOrPlayoffs = ['regular', 'playoffs']
seasons = {}
plyrs = {}
for season in range(1996, 2020):
    ss = '%d_%d' % (season, season + 1)
    # print(ss)
    seasons[ss] = [[0, np.zeros((3, 7, 19))], [0, np.zeros((3, 7, 19))]]
    for i in range(2):
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gmf in tqdm(gms):
            gm = gmf[:-7]
            game = Game(gm, regularOrPlayoffs[i])
            _, _, _, record = game.game_scanner(gm)
            tmplyrs = game.teamplyrs()
            bx = game.boxscores(record)[:, 6, :]
            # 联盟赛季总和
            seasons[ss][i][0] += 1
            seasons[ss][i][1][0, 6, :] += bx[0]
            seasons[ss][i][1][1, 6, :] += bx[1]
            seasons[ss][i][1][2, 6, :] += (bx[0] + bx[1])
            # 球员赛季总和
            for rh in range(2):
                for pm in tmplyrs[rh]:
                    if pm not in plyrs:
                        plyrs[pm] = {}
                    if ss not in plyrs[pm]:
                        # 0本队1对手  0reg1plf  0全部比赛数1客场数2主场数3stats  0客场1主场2全部  0第一节1第二节2上半场3第三节4第四节5下半场6全场
                        # 0FG1FGA2FG%3 3P 4 3PA 5 3P% 6FT7FTA8FT%9ORB10DRB11TRB12AST13STL14BLK15TOV16PF17PTS18PACE
                        plyrs[pm][ss] = [[[0, 0, 0, np.zeros((3, 7, 19))], [0, 0, 0, np.zeros((3, 7, 19))]], [[0, 0, 0, np.zeros((3, 7, 19))], [0, 0, 0, np.zeros((3, 7, 19))]]]
                    # 记录本队
                    plyrs[pm][ss][0][i][0] += 1
                    plyrs[pm][ss][0][i][rh + 1] += 1
                    plyrs[pm][ss][0][i][-1][rh, 6, :] += bx[rh]
                    plyrs[pm][ss][0][i][-1][2, 6, :] += bx[rh]
                    # 记录对手
                    op = 0 if rh else 1
                    plyrs[pm][ss][1][i][0] += 1
                    plyrs[pm][ss][1][i][op + 1] += 1
                    plyrs[pm][ss][1][i][-1][op, 6, :] += bx[op]
                    plyrs[pm][ss][1][i][-1][2, 6, :] += bx[op]

    print(seasons[ss][0][0], list(seasons[ss][0][1][2, 6, :] / seasons[ss][0][0] / 2))
    print(seasons[ss][1][0], list(seasons[ss][1][1][2, 6, :] / seasons[ss][1][0] / 2))
    # if 'jamesle01' in plyrs:
    #     print(plyrs['jamesle01'][ss][0][0], list(plyrs['jamesle01'][ss][0][-1][2, 6, :] / plyrs['jamesle01'][ss][0][0]))
    #     print(plyrs['jamesle01'][ss][1][0], list(plyrs['jamesle01'][ss][1][-1][2, 6, :] / plyrs['jamesle01'][ss][1][0]))

writeToPickle('./data/leagueSeasonAverage.pickle', seasons)
writeToPickle('./data/playerSeasonAverage.pickle', plyrs)
