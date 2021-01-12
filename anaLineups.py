#!/usr/bin/python
# -*- coding:utf8 -*-
import os
from tqdm import tqdm
import numpy as np
from klasses.Game import Game
from klasses.miscellaneous import MPTime
from util import writeToPickle, gameMarkToDir, LoadPickle, plus_minus
regularOrPlayoffs = ['regular', 'playoffs']


def inline(r):
    line = r['R'][RoH]
    return sorted(line, reverse=True)


lines_all = [{}, {}]
for season in range(2020, 2021):
    ss = '%d_%d' % (season, season + 1)
    for i in range(2):
        lines_all[i][ss] = {}
        lines = {}    # {'tm1': {'line1': ['sum_time', '+/-'], 'line2': ['sum_time', '+/-'] ...}, 'tm2': ...}
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gmf in tqdm(gms):
            gm = gmf[:-7]
            game = Game(gm, regularOrPlayoffs[i])
            record = LoadPickle(gameMarkToDir(gm, regularOrPlayoffs[i], tp=3))
            rot = game.rotation(record)
            et = '%d:00.0' % (48 + 5 * (game.quarters - 4))
            for tm in list(game.bxscr[0]):    # 分别回溯两支球队
                if tm not in lines:
                    lines[tm] = {}
                RoH = list(game.bxscr[0]).index(tm)
                for ix, r in enumerate(rot):
                    line = inline(r)
                    if ' '.join(line) not in lines[tm]:
                        lines[tm][' '.join(line)] = [MPTime('0:00.0'), 0]
                    if ix == 0:
                        tt = '0:00.0'
                        s = [0, 0]
                    else:
                        assert r['T'] != tt or (ix > 0 and r['Q'] != rot[ix - 1]['Q'])
                        if set(r['R'][RoH]) != set(rot[ix - 1]['R'][RoH]):
                            # print(gm, r)
                            try:
                                lines[tm][' '.join(inline(rot[ix - 1]))][0] += (MPTime(r['T']) - MPTime(tt))
                                lines[tm][' '.join(inline(rot[ix - 1]))][1] += plus_minus(r, s, RoH)
                            except:
                                print(gm, r)
                                raise KeyError
                            tt = r['T']
                            s = r['S']
                lines[tm][' '.join(inline(rot[-1]))][0] += (MPTime(et) - MPTime(tt))
                lines[tm][' '.join(inline(rot[-1]))][1] += plus_minus(record[-1], s, RoH)
        # print(len(lines))
        for tm in lines:
            lines_sorted = {}
            for k in sorted(lines[tm], key=lines[tm].__getitem__, reverse=True):  # 字典按值排序
                lines_sorted[k] = lines[tm][k]
            lines_all[i][ss][tm] = lines_sorted
        # for k in lines_sorted:
        #     print(k, lines_sorted[k])

# writeToPickle('./data/Lineups/anaSeason5Lineups.pickle', lines_all)
# print(len(lines_all[0]['2019_2020']['MIL']))

st = MPTime('0:00.0')
for line in lines_all[0]['2020_2021']['LAL']:
    st += lines_all[0]['2020_2021']['LAL'][line][0]
    print(line, lines_all[0]['2020_2021']['LAL'][line])
print(st)
