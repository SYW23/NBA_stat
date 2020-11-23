#!/usr/bin/python
# -*- coding:utf8 -*-
# 统计一整节在场但无任何数据统计入账的球员
import os
from tqdm import tqdm
from klasses.Game import Game
from util import writeToPickle, gameMarkToDir, LoadPickle, plus_minus

regularOrPlayoffs = ['regular', 'playoffs']
plyrs = {}    # {'pm': [[gm], [节次], [+/-], [胜负], [是否比赛最后一节]]}
for season in range(2000, 2020):
    ss = '%d_%d' % (season, season + 1)
    # print(ss)
    for i in range(1):
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gmf in tqdm(gms):
            gm = gmf[:-7]
            game = Game(gm, regularOrPlayoffs[i])
            _, _, _, record = game.game_scanner()
            rot = game.rotation(record)
            qtrs = rot[-1]['Q'] + 1
            # 判断胜者
            scores = [game.bxscr[0][x][0] for x in game.bxscr[0]]
            winner = int(scores[0] < scores[1])
            for tm in range(2):    # 分别回溯两支球队
                # if tm not in plyrs:
                #     plyrs[pm] = {}
                q = 0
                tick = 0
                SoQ = 0
                for qtr in range(qtrs):
                    # 定位至本届首发
                    st_pms = rot[tick]['R'][tm]
                    ivs_pm = set(st_pms)
                    SoQ = tick
                    while tick < len(rot) and rot[tick]['Q'] == qtr:
                        ivs_pm = ivs_pm.intersection(set(rot[tick]['R'][tm]))
                        tick += 1
                    # print(SoQ, tick)
                    # print(rot[SoQ])
                    # print(rot[tick] if tick < len(rot) else record[-1])
                    # print(ivs_pm)

                    if ivs_pm:
                        for pm in ivs_pm:
                            flag = 1
                            for r in game.gameflow[qtr]:
                                ind = 1 if r[1] else 5
                                if (len(r) > 2 and pm in r[ind]) or (len(r) == 2 and 'Jump' in r[ind] and pm in r[ind]):
                                    flag = 0
                                    # print(qtr, pm, r)
                                    break
                            if flag:
                                if pm not in plyrs:
                                    plyrs[pm] = [[], [], [], [], []]    # 0gm, 1节次, 2+/-, 3胜负, 4是否比赛最后一节
                                diff = plus_minus(rot[tick] if tick < len(rot) else record[-1], rot[SoQ]['S'], tm)
                                plyrs[pm][0].append(gm)
                                plyrs[pm][1].append(qtr)
                                plyrs[pm][2].append(diff)
                                plyrs[pm][3].append(int(winner == tm))
                                plyrs[pm][4].append(int(qtr == game.quarters - 1))
                                # print('ivs', pm, gm, qtr)

for pm in plyrs:
    print(pm, plyrs[pm])
writeToPickle('./data/anaInvisiblePlayers.pickle', plyrs)
