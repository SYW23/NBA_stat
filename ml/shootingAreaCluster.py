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


#%%
regularOrPlayoffs = ['regular', 'playoff']
ps2 = []
ps3 = []
for i in range(1):
    for season in range(2020, 2021):
        ss = '%d_%d' % (season, season + 1)
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        print(len(gms))
        for gm in gms:
            # print(gm)
            game = Game(gm, regularOrPlayoffs[i])
            if 'LAL' in game.bxscr[0]:
                print(gm)
                record, rot, bxs = game.preprocess(load=1)
                record = game.gn.record
                plyr = {2544: 'L. James'}
                for rec in record:
                    if 'MK' in rec and rec['MK'][0] == plyr:
                        if rec['MK'][1] == 2:
                            ps2.append(rec['C'])
                        elif rec['MK'][1] == 3:
                            ps3.append(rec['C'])
print(len(ps2))
print(len(ps3))
ps2 = np.array(ps2)
ps3 = np.array(ps3)


#%%
cs2 = 9
cs3 = 6
colors = ['b', 'c', 'lime', 'maroon', 'm', 'r', 'pink', 'yellow', 'silver',
          'orange', 'gold', 'deepskyblue', 'darkviolet', 'darkgreen', 'salmon']
estimator = KMeans(n_clusters=cs2)
estimator.fit(ps2)
label_pred2 = estimator.labels_
estimator = KMeans(n_clusters=cs3)
estimator.fit(ps3)
label_pred3 = estimator.labels_



for c in range(cs2):
    tmp = ps2[label_pred2 == c]
    plt.scatter(tmp[:, 0], tmp[:, 1], c=colors[c], marker='o', label='2-points %d' % c)
for c in range(cs3):
    tmp = ps3[label_pred3 == c]
    plt.scatter(tmp[:, 0], tmp[:, 1], c=colors[c + 8], marker='o', label='3-points %d' % c)
plt.scatter([0], [0], c='w', marker='x', label='rim')
plt.legend()
plt.show()


#%%
plt.scatter(ps2[:, 0], ps2[:, 1], c='r', marker='o', label='2-points %d' % c)
plt.scatter(ps3[:, 0], ps3[:, 1], c='r', marker='o', label='3-points %d' % c)
plt.scatter([0], [0], c='w', marker='x', label='rim')

# =============================================================================
# x = np.linspace(0, 300, 100)
# for i in range(900):
#     y = np.tan(i/10/180*math.pi)*x
#     scope = y <= 350
#     tmpx = x[scope]
#     tmpy = y[scope]
#     plt.plot(tmpx, tmpy, c='orange')
# =============================================================================

plt.legend()
plt.show()



