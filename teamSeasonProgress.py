#!/usr/bin/python
# -*- coding:utf8 -*-

import os
from util import LoadPickle
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from windows.result_windows import ShowTables


def wl(dt):    # 判断胜负，返回队名列表，0胜1负
    ks = list(dt.keys())
    return [ks[0], ks[1]] if dt[ks[0]][0] > dt[ks[1]][0] else [ks[1], ks[0]]


def rec_op(a, b, ot):
    if a not in ot:
        ot[a] = []
    if b not in ot[a]:
        ot[a].append(b)
    return ot


def teamsWL(ss, ROP):
    seasonbsdir = './data/seasons_boxscores/%s/%s/' % (ss, ROP)
    gms = [x[:-17] for x in os.listdir(seasonbsdir)]
    pc = {}    # key: value    '队名': [n, n, ..., n] 列表长度为赛季比赛场次，从0开始累加，胜场+1，负场+0
    if ROP == 'playoffs':
        ot = {}    # 记录季后赛对手球队
    for gm in gms:
        bs = LoadPickle(seasonbsdir + gm + '_boxscores.pickle')
        gr = wl(bs[0])
        for i, t in enumerate(gr):
            if t not in pc:
                pc[t] = []
            # pc[t].append(pc[t][-1] + -1 if i else pc[t][-1] + 1) if pc[t] else pc[t].append(-1 if i else 1)
            pc[t].append(pc[t][-1] if i else pc[t][-1] + 1) if pc[t] else pc[t].append(0 if i else 1)    # 胜队+1，负队+0
        if ROP == 'playoffs':
            ot = rec_op(gr[0], gr[1], ot)
            ot = rec_op(gr[1], gr[0], ot)
    if ROP == 'playoffs':
        return pc, ot
    else:
        return pc


def find_no1_wl(wl):
    maxp = 0
    maxt = ''
    for i in wl:
        tmp = wl[i][0] / (wl[i][0] + wl[i][1])
        if tmp > maxp:
            maxp = tmp
            maxt = i
    return maxp, maxt



chps = LoadPickle('./data/champions.pickle')
op_wl = {}
help_defeat_wl = {}
diff2topwl = {}
for season in tqdm(range(1949, 2020)):
    ss = '%d_%d' % (season, season + 1)
    cc = chps[ss]
    # print(ss)
    pc = teamsWL(ss, 'regular')

    wls_reg = {}
    for tm in pc.keys():
        wls_reg[tm] = np.array([pc[tm][-1], len(pc[tm]) - pc[tm][-1]])
    no1p, no1t = find_no1_wl(wls_reg)
    ccp = wls_reg[cc][0] / (wls_reg[cc][0] + wls_reg[cc][1])
    diff2topwl[ss] = [cc, ccp, no1t, no1p, ccp - no1p]
    
    # for tm in teams:
        # plt.plot(range(len(pc[tm])), pc[tm])
    # plt.show()

    pc_p, ot = teamsWL(ss, 'playoffs')
    wls_plf = {}
    for tm in pc_p.keys():
        wls_plf[tm] = np.array([pc_p[tm][-1], len(pc_p[tm]) - pc_p[tm][-1]])

    # 冠军球队对手的胜率
    tmp = np.array([0, 0])
    for t in ot[cc]:
        tmp += wls_reg[t]
        # print(t)
    if ss == '2019_2020':
        tmp[0] -= 1
    op_wl[ss + ' ' + cc] = tmp[0] / (tmp[0] + tmp[1])
    
    # 冠军球队对手（总亚军）直接击败对手的胜率
    tmp = np.array([0, 0])
    for t in ot[cc]:
        for dt in ot[t]:
            if dt != cc:
                tmp += wls_reg[dt]
    help_defeat_wl[ss + ' ' + cc] = tmp[0] / (tmp[0] + tmp[1])

#%%
new_century = '1999'    # 是否排除新世纪以前的赛季
win = ShowTables([[x[0].split(' ')[0], x[0].split(' ')[1],
                   float('%.3f' % x[1])] for x in op_wl.items() if x[0].split(' ')[0] > new_century],
                   ['年份', '冠军球队', '对手胜率'])
win.loop('总冠军季后赛对手球队胜率排名')

win = ShowTables([[x[0].split(' ')[0], x[0].split(' ')[1],
                   float('%.3f' % x[1])] for x in help_defeat_wl.items() if x[0].split(' ')[0] > new_century],
                   ['年份', '冠军球队', '对手直接击败球队胜率'])
win.loop('总冠军季后赛对手直接击败球队胜率排名')

win = ShowTables([[x[0], x[1][0], float('%.3f' % x[1][1]), x[1][2],
                   float('%.3f' % x[1][3]), float('%.3f' % x[1][4])] for x in diff2topwl.items() if x[0] > new_century],
                   ['年份', '冠军球队', '冠军球队胜率胜率', '常规赛第一球队', '常规赛第一球队胜率', '胜率差'])
win.loop('总冠军季后赛对手直接击败球队胜率排名')


























