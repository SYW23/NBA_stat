#!/usr/bin/python
# -*- coding:utf8 -*-
import os
from tqdm import tqdm
import numpy as np
from klasses.Game import Game
from klasses.miscellaneous import MPTime
from util import writeToPickle, gameMarkToDir, LoadPickle, plus_minus
from splitLineups import splitLineups
regularOrPlayoffs = ['regular', 'playoff']


def inline(r):
    line = r['R'][RoH]
    return sorted(line, reverse=True)


lines_all = LoadPickle('./data/Lineups/anaSeason5Lineups.pickle')
for season in range(2020, 2021):
    ss = '%d_%d' % (season, season + 1)
    for i in range(2):
        lines_all[i][ss] = {}
        lines = {}    # {'tm1': {'line1': ['sum_time', '+/-'], 'line2': ['sum_time', '+/-'] ...}, 'tm2': ...}
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in tqdm(gms):
            game = Game(gm, regularOrPlayoffs[i])
            record = LoadPickle(gameMarkToDir(gm, regularOrPlayoffs[i], tp=3))
            rot = game.rotation(record)
            bxs, rot = game.replayer(record, rot)
            et = '%d:00.0' % (48 + 5 * (game.quarters - 4))
            for tmix, tm in enumerate(list(game.bxscr[0])):    # 分别回溯两支球队
                if tm not in lines:
                    lines[tm] = {}
                RoH = list(game.bxscr[0]).index(tm)
                for ix, r in enumerate(rot):
                    line = inline(r)
                    if ' '.join(line) not in lines[tm]:
                        lines[tm][' '.join(line)] = [MPTime('0:00.0'), 0, [np.zeros((21, )), np.zeros((21, ))]]    # 0时间 1+/- 2详细数据   0本队数据1对手数据
                    if ix == 0:
                        tt = '0:00.0'
                        stats = np.zeros((21, ))
                        s = [0, 0]
                    else:
                        try:
                            assert r['T'] != tt or (ix > 0 and r['Q'] != rot[ix - 1]['Q'])
                        except:
                            print(gm, tt, r)
                            print(rot[ix - 1])
                        if set(r['R'][RoH]) != set(rot[ix - 1]['R'][RoH]):
                            # print(gm, r)
                            try:
                                lines[tm][' '.join(inline(rot[ix - 1]))][0] += (MPTime(r['T']) - MPTime(tt))
                                lines[tm][' '.join(inline(rot[ix - 1]))][1] += plus_minus(r, s, RoH)
                                lines[tm][' '.join(inline(rot[ix - 1]))][2][0] += (r['team'][tmix] - stats[tmix])
                                lines[tm][' '.join(inline(rot[ix - 1]))][2][1] += (r['team'][tmix - 1] - stats[tmix - 1])
                            except:
                                print(gm, r)
                                raise KeyError
                            tt = r['T']
                            s = r['S']
                            stats = r['team']
                lines[tm][' '.join(inline(rot[-1]))][0] += (MPTime(et) - MPTime(tt))
                lines[tm][' '.join(inline(rot[-1]))][1] += plus_minus(record[-1], s, RoH)
                lines[tm][' '.join(inline(rot[-1]))][2][0] += (bxs.tdbxs[tmix][0]['team'] - r['team'][tmix])
                lines[tm][' '.join(inline(rot[-1]))][2][1] += (bxs.tdbxs[tmix - 1][0]['team'] - r['team'][tmix - 1])
        # print(len(lines))
        for tm in lines:
            for L in lines[tm]:
                lines[tm][L][2] = [list(lines[tm][L][2][0]), list(lines[tm][L][2][1])]
                for pp in [2, 5, 8]:
                    for tt in range(2):
                        lines[tm][L][2][tt][pp] = float('%.3f' % (lines[tm][L][2][tt][pp - 2] / lines[tm][L][2][tt][pp - 1])) if lines[tm][L][2][tt][pp - 1] else float('nan')
        for tm in lines:
            lines_sorted = {}
            for k in sorted(lines[tm], key=lines[tm].__getitem__, reverse=True):  # 字典按值排序
                lines_sorted[k] = lines[tm][k]
            lines_all[i][ss][tm] = lines_sorted

# writeToPickle('./data/Lineups/anaSeason5Lineups.pickle', lines_all)
# ==============================推导1~4人lineup统计===================================
# splitLineups(lines_all)


st = MPTime('0:00.0')
for line in lines_all[0]['2020_2021']['LAL']:
    tmp = lines_all[0]['2020_2021']['LAL'][line]
    st += tmp[0]
    print(line, '\t', float('%.3f' % (tmp[1] * 100 / tmp[2][0][-3])) if tmp[2][0][-3] else float('nan'), tmp)
print(st)
