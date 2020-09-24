#!/usr/bin/python
# -*- coding:utf8 -*-

import os
from util import LoadPickle
import matplotlib.pyplot as plt

regularOrPlayoffs = ['regular', 'playoff']
ROP = regularOrPlayoffs[0]


def wl(dt):
    ks = list(dt.keys())
    return [ks[0], ks[1]] if dt[ks[0]][0] > dt[ks[1]][0] else [ks[1], ks[0]]


for season in range(2019, 2020):
    ss = '%d_%d' % (season, season + 1)
    seasondir = './data/seasons/%s/%s/' % (ss, ROP if ROP == 'regular' else ROP + 's')
    seasonbsdir = './data/seasons_boxscores/%s/%s/' % (ss, ROP if ROP == 'regular' else ROP + 's')
    gms = os.listdir(seasondir)

    gms = [x[:-7] for x in gms]
    teams = set([x[9:] for x in gms])
    print(teams)
    pc = {}
    for tm in teams:
        pc[tm] = []
    for gm in gms:
        bs = LoadPickle(seasonbsdir + gm + '_boxscores.pickle')
        gr = wl(bs[0])
        for i, t in enumerate(gr):
            # pc[t].append(pc[t][-1] + -1 if i else pc[t][-1] + 1) if pc[t] else pc[t].append(-1 if i else 1)
            pc[t].append(pc[t][-1] if i else pc[t][-1] + 1) if pc[t] else pc[t].append(0 if i else 1)

    for tm in teams:
        plt.plot(range(len(pc[tm])), pc[tm])
    plt.show()

