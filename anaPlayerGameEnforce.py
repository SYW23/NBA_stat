#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from util import LoadPickle, playerMarkToDir
from klasses.miscellaneous import MPTime
import pandas as pd

RoF = ['regular', 'playoff']
pm2pn = LoadPickle('./data/playermark2playername.pickle')
games_td = [300, 20]
tartext = ['Steal', 'Turnover', 'Block']
enforce = {}
season_lg = {}
for tar_item in range(3):    # 0抢断1失误2盖帽
    enforce[tartext[tar_item]] = LoadPickle('./data/Enforce/player%sEnforce.pickle' % tartext[tar_item])
    season_lg[tartext[tar_item]] = LoadPickle('./data/Enforce/season%sEnforceRecord.pickle' % tartext[tar_item])

print(len(enforce['Steal']))
print(len(enforce['Turnover']))
print(len(enforce['Block']))
pms = list(enforce['Turnover'].keys())

for i in range(2):
    tmp = {}
    for pm in pms:
        pmdir = playerMarkToDir(pm, RoF[i], tp=1)
        if pmdir:
            cr = LoadPickle(pmdir)
            cr_a = cr.iloc[cr.index[-2]]
            num_games = cr_a['G']
            num_games = int(num_games[:num_games.index('场')])
            if num_games > games_td[i]:
                mp = MPTime(cr_a['MP'])
                pts = float(cr_a['PTS'])
                drb = float(cr_a['DRB'])
                orb = float(cr_a['ORB'])
                ast = float(cr_a['AST'])
                stl = float(cr_a['STL'])
                blk = float(cr_a['BLK'])
                tov = float(cr_a['TOV'])
                pf = float(cr_a['PF'])

                if pm in enforce['Steal']:
                    stl_plus = enforce['Steal'][pm][i][2] / enforce['Steal'][pm][i][0] if enforce['Steal'][pm][i][0] else 0    # 球队得分/次抢断
                else:
                    stl_plus = 0
                if pm in enforce['Block']:
                    blk_plus = enforce['Block'][pm][i][1] / enforce['Block'][pm][i][0] if enforce['Block'][pm][i][0] else 0    # 球员阻止得分/次盖帽
                else:
                    blk_plus = 0
                tov_minus = enforce['Turnover'][pm][i][2] / enforce['Turnover'][pm][i][0] if enforce['Turnover'][pm][i][0] else 0  # 球队失分/次失误

                score = pts + drb + orb + ast * 2 + stl * stl_plus + blk * blk_plus - tov * tov_minus - pf * 2
                score = score / mp.mf() * 25
                tmp[pm] = score
    res = {}
    for k in sorted(tmp, key=tmp.__getitem__, reverse=True):
        res[pm2pn[k]] = tmp[k]
    top10 = list(res.keys())[:10]
    for r in range(10):
        print(RoF[i], r, top10[r], res[top10[r]])
    print()
