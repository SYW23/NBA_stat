#!/usr/bin/python
# -*- coding:utf8 -*-
from klasses.Player import Player
from util import LoadPickle, writeToPickle
from klasses.stats_items import *
from tqdm import tqdm
import pandas as pd

# 计算球员赛季和生涯场均及总和并保存
pm2pn = LoadPickle('../data/playermark2playername.pickle')
for p in tqdm(list(pm2pn.keys())):
    # print(p)
    for RoP in ['regular', 'playoff']:
        player = Player(p, RoP)
        if player.exists and not isinstance(player.data, list):
            res = []
            for sss, ss in player.yieldSeasons():
                sss = player.on_board_games(sss)
                res += player.ave_and_sum(sss, type=2)
                res[-2] = [ss] + res[-2]
                res[-1] = [ss] + res[-1]
            sss = player.on_board_games(player.data)
            res += player.ave_and_sum(sss, type=2)
            res[-2] = ['career'] + res[-2]
            res[-1] = ['career'] + res[-1]
            res = pd.DataFrame(res, columns=['Season'] + list(regular_items_en.keys() if RoP == 'regular' else playoff_items_en.keys()))
            # for col in res.columns:
            #     res[col] = res[col].astype('category')
            writeToPickle('../data/players/%s/%sGames/%sSaCAaS.pickle' % (p, RoP, RoP), res)
