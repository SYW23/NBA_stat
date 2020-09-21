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
            for ss, _ in player.yieldSeasons():
                ss = player.on_board_games(ss)
                res += player.ave_and_sum(ss, type=2)
            ss = player.on_board_games(player.data)
            res += player.ave_and_sum(ss, type=2)
            res = pd.DataFrame(res, columns=regular_items_en.keys() if RoP == 'regular' else playoff_items_en.keys())
            # for col in res.columns:
            #     res[col] = res[col].astype('category')
            writeToPickle('../data/players/%s/%sGames/%sSaCAaS.pickle' % (p, RoP, RoP), res)
