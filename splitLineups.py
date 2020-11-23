#!/usr/bin/python
# -*- coding:utf8 -*-

from util import LoadPickle, writeToPickle
import itertools
from klasses.miscellaneous import MPTime
from tqdm import tqdm

lines = LoadPickle('data/Lineups/anaSeason5Lineups.pickle')
# print(len(lines))
# print(len(lines[0]))
# print(len(lines[0]['2019_2020']))
lines_all = [[{}, {}], [{}, {}], [{}, {}], [{}, {}]]    # 0一人组合1二人组合2三人组合3四人组合 0常规赛1季后赛
for season in tqdm(range(2000, 2020)):
    ss = '%d_%d' % (season, season + 1)
    # print(ss)
    for i in range(2):
        lines1234 = [{}, {}, {}, {}]    # 单赛季按球队 0一人组合1二人组合2三人组合3四人组合
        for tm in lines[i][ss]:
            # 球队lineups初始化
            for ix in range(4):
                if tm not in lines1234[ix]:
                    lines1234[ix][tm] = {}
                lines_all[ix][i][ss] = {}
            line5_tm = lines[i][ss][tm]    # 单队5人lineups
            # print(tm, len(line5_tm))
            for L in line5_tm:
                pms = L.split(' ')    # 遍历每组5人组合
                # print(pms)
                pms1234 = [[], [], [], []]    # 0一人组合1二人组合2三人组合3四人组合
                for c in range(1, 5):    # 按照每组5人组合，使用（排列）组合方法穷尽所有1-4人的搭配
                    for iter in itertools.combinations(pms, c):
                        pms1234[c - 1].append(list(iter))
                for ix, combs_i in enumerate(pms1234):    # 遍历1-4人的所有搭配，累加时间和正负值
                    for combs in combs_i:
                        combstr = ' '.join(sorted(combs))
                        if combstr not in lines1234[ix][tm]:    # 每种组合初始化
                            lines1234[ix][tm][combstr] = [MPTime('0:00.0'), 0]
                        lines1234[ix][tm][combstr][0] += line5_tm[L][0]
                        lines1234[ix][tm][combstr][1] += line5_tm[L][1]
        for ix in range(4):
            for tm in lines1234[ix]:
                lines_sorted = {}
                for k in sorted(lines1234[ix][tm], key=lines1234[ix][tm].__getitem__, reverse=True):  # 字典按值排序
                    lines_sorted[k] = lines1234[ix][tm][k]
                lines_all[ix][i][ss][tm] = lines_sorted

for ix in range(4):
    writeToPickle('./data/Lineups/anaSeason%dLineups.pickle' % (ix + 1), lines_all[ix])
    # for combs in lines_all[ix][0]['2019_2020']['LAL']:
    #     print(combs, lines_all[ix][0]['2019_2020']['LAL'][combs])
