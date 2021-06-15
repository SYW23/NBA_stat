#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from util import LoadPickle
from klasses.Game import Game
import os
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import metrics
import numpy as np
import pandas as pd
from collections import Counter
from util_clusters import mse, elbow, cl_cts_finetuning, count_and_top20, outputdf
np.set_printoptions(suppress=True)
f = open('../data/playermark2playername.pickle', 'rb')
pm2pn = pickle.load(f)
f.close()
load = 1


#%%
if not load:
    regularOrPlayoffs = ['regular', 'playoff']
    plyrs = []
    stats = []
    for i in range(1):
        for season in range(2020, 2021):
            ss = '%d_%d' % (season, season + 1)
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            print(len(gms))
            for gm in tqdm(gms):
                # print(gm)
                game = Game(gm, regularOrPlayoffs[i])
                record, rot, bxs = game.preprocess(load=1)
                for RoH in range(2):
                    for plyr in bxs.tdbxs[RoH][0]:
                        if plyr != 'team':
                            plyrs.append(plyr)
                            tmp = bxs.tdbxs[RoH][0][plyr][0]
                            stats.append(tmp[[0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20]])
    
    plyrs = np.array(plyrs)
    stats = np.array(stats)
    print(stats.shape)
    stats[:, 0] -= stats[:, 2]
    stats[:, 1] -= stats[:, 3]
    # 归一化
    absmax = np.max(np.abs(stats), axis=0)
    stats /= absmax
    # 求球员平均
    unique_stats = []
    unique_plyrs = list(set(plyrs))
    for p in unique_plyrs:
        unique_stats.append(np.mean(stats[plyrs == p], axis=0))
    unique_stats = np.array(unique_stats)


#%%
# 读取数据
plyrs = LoadPickle('2000_2021_singleGameBasicStats_plyrs.pickle')
stats = LoadPickle('2000_2021_singleGameBasicStats.pickle')
absmax = LoadPickle('2000_2021_singleGameBasicStats_absmax.pickle')


#%%
# 通过手肘法确定Kmeans聚类的最优K值
# elbow(stats * absmax)


#%%
# KMeans聚类分析
# cs = 9
repeat = 1000

# 多次聚类，匹配每次聚类与初始聚类的结果，求均值
for cs in range(10, 1, -1):
    # 初始聚类
    estimator = KMeans(n_clusters=cs, init='k-means++')
    estimator.fit(stats)
    try:
        cl_cts_ave = cl_cts_finetuning(estimator, repeat, stats, cs)
    except KeyError:
        print('%d down!' % cs)
        continue
    else:
        break
print('选定簇的个数：%d' % cs)
# cl_cts_ave = cl_cts_finetuning(estimator, repeat, stats, cs)

# 将修正后的聚类中心更新聚类器并重新聚类
estimator.cluster_centers_ = cl_cts_ave
label_pred = estimator.predict(stats)

# 调整及新增部分数据栏位，整合结果
df = count_and_top20(cs, estimator, absmax, label_pred, plyrs, pm2pn)
df = outputdf(df)
df.to_csv('tmp_all.csv', index=False)


#%%
for i in range(7, 8):
    print('第%d类：' % i)
    stats_cs = stats[label_pred == i]
    plyrs_cs = plyrs[label_pred == i]
    elbow(stats_cs * absmax)
    for cs_cs in range(10, 1, -1):
        estimator_cs = KMeans(n_clusters=cs_cs, init='k-means++')
        estimator_cs.fit(stats_cs)
        try:
            cl_cts_ave_cs = cl_cts_finetuning(estimator_cs, repeat, stats_cs, cs_cs)
        except KeyError:
            print('%d down!' % cs_cs)
            continue
        else:
            break
    print('第%d类再聚类，选定簇的个数：%d' % (i, cs_cs))
    estimator_cs.cluster_centers_ = cl_cts_ave_cs
    label_pred_cs = estimator_cs.predict(stats_cs)
    df_cs = count_and_top20(cs_cs, estimator_cs, absmax, label_pred_cs, plyrs_cs, pm2pn)
    df_cs = outputdf(df_cs)
    df_cs.to_csv('tmp_%d.csv' % i, index=False)









