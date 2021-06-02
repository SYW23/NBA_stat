#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from klasses.Game import Game
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import numpy as np
import math
np.set_printoptions(suppress=True)

#%%
regularOrPlayoffs = ['regular', 'playoff']
plyrs = []
stats = []
for i in range(1):
    for season in range(2020, 2021):
        ss = '%d_%d' % (season, season + 1)
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        print(len(gms))
        for gm in tqdm(gms[:1]):
            # print(gm)
            game = Game(gm, regularOrPlayoffs[i])
            record, rot, bxs = game.preprocess(load=1)
            for RoH in range(2):
                for plyr in bxs.tdbxs[RoH][0]:
                    if plyr != 'team':
                        plyrs.append(plyr)
                        tmp = bxs.tdbxs[RoH][0][plyr][0]
                        stats.append(tmp[[0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20]])
# print(plyrs)
print(len(plyrs))
stats = np.array(stats)
print(stats.shape)
print(stats)
stats[:, 0] -= stats[:, 3]
stats[:, 2] -= stats[:, 4]
print()
print(stats)
