#!/usr/bin/python
# -*- coding:utf8 -*-

from klasses.Game import Game
from klasses.miscellaneous import MPTime
from windows.tools import GameDetailEditor
from util import writeToPickle, gameMarkToDir, LoadPickle
from tqdm import tqdm
import os
import time
import numpy as np
np.set_printoptions(suppress=True)

regularOrPlayoffs = ['regular', 'playoffs']
# 分赛季统计变量
count_games_all = {}    # 总比赛数
count_item_all = {}    # 总次数
count_score_all = {}    # 球队在球权转换前创造的总得分
average_score_all = {}    # 球队在球权转换前创造的平均得分
# key: value
# ——>
# 'player name': [[0总次数, 1阻止/帮助总得分, 2总被次数, 3被阻止/帮助总得分,
#                  {赛季: [0总次数, 1阻止/帮助总得分, 2总被次数, 3被阻止/帮助总得分]]
plyrs = {}
tar_sn = ['BLK', 'AST']
KoS = ['MS', 'MK']
tar_text = ['Block', 'Assist']
tar_item = 1    # 0盖帽1助攻


def new_player(pm, ss):
    if pm not in plyrs:  # 新建球员统计
        plyrs[pm] = [[0, 0, 0, 0, {}], [0, 0, 0, 0, {}]]
    if ss not in plyrs[pm][i][-1]:  # 新建球员赛季统计
        plyrs[pm][i][-1][ss] = [0, 0, 0, 0]


for season in range(1996, 2020):
    count_games = [0, 0]  # 0reg1plf
    count_item = np.zeros((2, 3, 9))  # 0reg1plf    0客场球队1主场球队2总    0总1第一节2第二节3第三节4第四节5f加时6s加时7t加时8f加时
    count_score = np.zeros((2, 3, 9))
    ss = '%d_%d' % (season, season + 1)
    # print(ss)
    for i in range(2):    # 分别统计常规赛、季后赛
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in tqdm(gms):
            count_games[i] += 1
            game = Game(gm[:-7], regularOrPlayoffs[i])
            gameplyrs = game.teamplyrs()
            record = LoadPickle(gameMarkToDir(gm[:-7], regularOrPlayoffs[i], tp=3))
            zoom = 0
            bp = -1
            pm = ''
            for rec in record:
                if tar_sn[tar_item] in rec:
                    pm = tar_sn[tar_item]
                    pmd = rec[KoS[tar_item]][0]
                    s = rec[KoS[tar_item]][1]

                    count_item[i][0 if rec['BP'] else 1][0] += 1
                    count_item[i][0 if rec['BP'] else 1][rec['Q'] + 1] += 1
                    count_item[i][2][0] += 1
                    count_item[i][2][rec['Q'] + 1] += 1
                    count_score[i][0 if rec['BP'] else 1][0] += s
                    count_score[i][0 if rec['BP'] else 1][rec['Q'] + 1] += s
                    count_score[i][2][0] += s
                    count_score[i][2][rec['Q'] + 1] += s

                    if pm:
                        new_player(pm, ss)
                        plyrs[pm][i][0] += 1
                        plyrs[pm][i][1] += s
                        plyrs[pm][i][-1][ss][0] += 1
                        plyrs[pm][i][-1][ss][1] += s
                    if pmd:
                        new_player(pmd, ss)
                        plyrs[pmd][i][2] += 1
                        plyrs[pmd][i][3] += s
                        plyrs[pmd][i][-1][ss][2] += 1
                        plyrs[pmd][i][-1][ss][3] += s
    count_games_all[ss] = count_games
    count_item_all[ss] = count_item
    count_score_all[ss] = count_score
    average_score_all[ss] = count_score_all[ss] / count_item_all[ss]
    print(count_games_all[ss])
    print(count_item_all[ss][:, 2, 0])
    print(count_score_all[ss][:, 2, 0])
    print(average_score_all[ss][:, 2, 0])

writeToPickle('./data/Enforce/player%sEnforce.pickle' % tar_text[tar_item], plyrs)
writeToPickle('./data/Enforce/season%sEnforceRecord.pickle' % tar_text[tar_item], [count_games_all, count_item_all, count_score_all, average_score_all])
