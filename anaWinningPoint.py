#!/usr/bin/python
# -*- coding:utf8 -*-
import sys
sys.path.append('../')
import os
from tqdm import tqdm
import numpy as np
import pandas as pd
import math
from util import gameMarkToSeason, gameMarkToDir, LoadPickle, writeToPickle, read_nba_pbp
from klasses.Game import Game
from klasses.miscellaneous import MPTime
from windows.result_windows import ShowSingleGame
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr

pp = []
tp = 0
wp = LoadPickle('D:/sunyiwu/stat/data/winning_point%d.pickle' % tp)
sss = wp[1]
keys = list(sss)

for key in keys:
    sss[key][0] /= sss[key][-1]
    sss[key][2] /= sss[key][-1]

items = ['pts off tovs', 'pts% off tovs', '2nd chance pts', '2nd chance pts%',
         'pts in the paint', 'pts% in the paint', 'biggest lead', 'biggest lead pts%',
         'longest run', 'longest run pts%', 'eFG%', 'TOV%', 'ORB%', 'FT/FGA',
         '2PT %', '2PT FGA%', '2PT PTS%', '2PT ASTed%',
         '3PT %', '3PT FGA%', '3PT PTS%', '3PT ASTed%',
         'FT %', 'FTA/FGA', 'FT PTS%']
chain = {}
for ix, it in enumerate(items):
    tmp = []
    for key in keys:
        if ix == 11:
            tmp.append(1 - sss[key][0][ix])
        else:
            tmp.append(sss[key][0][ix])
    # print(it, tmp)
    chain[it] = tmp

sub = 0
fig = plt.figure('Image', figsize=(20, 10))
for k in chain:
    # print(k, chain[k])
    c, p = pearsonr([x for x in range(1, len(keys) + 1)], chain[k])
    print(k, '\t', c, p)
    # if p < 0.05 and k != 'pts in the paint':
    sub += 1
    ax = fig.add_subplot(5, 5, sub)
    ax.plot(chain[k], c='r', label=k)
    # ax.set_xticks(np.arange(len(keys)))
    ax.set_xticklabels(['', '00-01', '05-06', '10-11', '15-16', '20-21'])
    # plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
    #          rotation_mode="anchor")
    # ax.set_title(k)
    ax.set_title(k + ' (p=%.5f)' % p)
    # ax.grid(axis="x")
plt.tight_layout()
plt.show()



# =============================================================================
# items = ['FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB',
#          'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
# chain = {}
# for ix, it in enumerate(items):
#     tmp = []
#     for key in keys:
#         if ix == 15:
#             tmp.append(1 - sss[key][2][ix])
#         else:
#             tmp.append(sss[key][2][ix])
#     # print(it, tmp)
#     chain[it] = tmp
# 
# sub = 0
# fig = plt.figure('Image', figsize=(20, 10))
# for k in chain:
#     # print(k, chain[k])
#     c, p = pearsonr([x for x in range(1, len(keys) + 1)], chain[k])
#     print(k, '\t', c, p)
#     # if p < 0.05 and k != 'pts in the paint':
#     sub += 1
#     ax = fig.add_subplot(4, 5, sub)
#     ax.plot(chain[k], c='r', label=k)
#     # ax.set_xticks(np.arange(len(keys)))
#     ax.set_xticklabels(['', '00-01', '05-06', '10-11', '15-16', '20-21'])
#     # plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
#     #          rotation_mode="anchor")
#     # ax.set_title(k)
#     ax.set_title(k + ' (p=%.3f)' % p)
#     # ax.grid(axis="x")
# plt.tight_layout()
# plt.show()
# =============================================================================

