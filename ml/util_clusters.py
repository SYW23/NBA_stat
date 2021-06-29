import sys
sys.path.append('../')
from util import LoadPickle, writeToPickle
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
np.set_printoptions(suppress=True)


def mse(a, b):
    diff = np.abs(a - b)
    return np.sum(diff ** 2)

def ios(ct, stats):
    d = stats - ct
    return np.sum(np.sqrt(np.sum(d ** 2, axis=1))) / d.shape[0]

def deDuplicated(stats):
    df = pd.DataFrame(stats)
    return stats[~df.duplicated().values]

def elbow(stats):
    '''
    stats: 数据集
    '''
    SSE = []    # 存放每次结果的误差平方和
    SIL = []    # 存放每次结果的轮廓系数
    CHS = []    # 存放每次结果的CH分(Calinski-Harabaz)
    DBI = []    # 存放每次结果的戴维森堡丁指数
    start, end = 2, 21
    for k in tqdm(range(start, end)):
        estimator = KMeans(n_clusters=k, init='k-means++')  # 构造聚类器
        estimator.fit(stats)
        label_pred = estimator.labels_
        SSE.append(estimator.inertia_)
        SIL.append(metrics.silhouette_score(stats, label_pred))
        CHS.append(metrics.calinski_harabasz_score(stats, label_pred))
        DBI.append(metrics.davies_bouldin_score(stats, label_pred))
    X = range(start, end)
    plt.subplot(221)
    plt.xlabel('k')
    plt.ylabel('SSE')
    plt.plot(X, SSE,'o-', label='SSE')
    plt.subplot(222)
    plt.xlabel('k')
    plt.ylabel('SIL')
    plt.plot(X, SIL,'x-', label='SIL')
    plt.subplot(223)
    plt.xlabel('k')
    plt.ylabel('CHS')
    plt.plot(X, CHS,'+-', label='CHS')
    plt.subplot(224)
    plt.xlabel('k')
    plt.ylabel('DBI')
    plt.plot(X, DBI,'2-', label='DBI')
    plt.show()


def cl_cts_finetuning(estimator, repeat, stats, cs):
    '''
    estimator: 初始聚类器
    repeat: 重复聚类次数
    stats: 数据集
    cs: 类别数
    '''
    # 多次聚类，匹配每次聚类与初始聚类的结果，求均值
    count = 0
    cl_cts_ave = estimator.cluster_centers_.copy()
    cl_cts_count = np.array([np.sum(estimator.labels_ == x) for x in range(cs)]).reshape(cs, 1)
    for i in tqdm(range(repeat)):
        mse_mat = np.zeros((cs, cs))
        estimator_tmp = KMeans(n_clusters=cs, init='k-means++')
        estimator_tmp.fit(stats)
        label_pred_tmp = estimator_tmp.labels_
        cl_cts_tmp = estimator_tmp.cluster_centers_
        # 以欧式距离匹配本次聚类与初始聚类的结果
        for x in range(cs):
            for y in range(cs):
                mse_mat[x, y] = mse(estimator.cluster_centers_[x], cl_cts_tmp[y])
        # plt.matshow(mse_mat)
        # plt.colorbar()
        minx = np.argmin(mse_mat, axis=0)
        miny = np.argmin(mse_mat, axis=1)
        # 检查是否一对一匹配
        if sorted(list(minx)) != sorted(list(miny)):
            count += 1
            # print('ooooops')
            raise KeyError
        # 均值修正
        cl_cts_count_tmp = np.array([np.sum(label_pred_tmp == x) for x in range(cs)])[miny].reshape(cs, 1)
        cl_cts_tmp = cl_cts_tmp[miny]
        cl_cts_ave = (cl_cts_ave * cl_cts_count + cl_cts_tmp * cl_cts_count_tmp) / (cl_cts_count + cl_cts_count_tmp)
        cl_cts_count += cl_cts_count_tmp
    print('\n%d/%d' % (count, repeat))
    return cl_cts_ave[np.argsort(cl_cts_ave[:,14])[::-1]]    # 按照MP从大到小排序


def count_and_top20(cs, estimator, absmax, label_pred, plyrs, pm2pn):
    '''
    cs: 类别数
    estimator: 修正后的聚类器
    absmax: 归一化系数
    label_pred: 使用修正后的聚类器重新聚类的结果
    plyrs: 球员码列表（与数据集一一对应）
    pm2pn: 球员姓名转换字典
    '''
    cols = ['2P', '2PA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
            'AST', 'STL', 'BLK', 'TOV', 'PF', 'BP', 'MP', '+/-']
    df = pd.DataFrame(columns=cols)
    for i in range(cs):
        tmp = estimator.cluster_centers_[i] * absmax
        tmp = pd.DataFrame(tmp.reshape((1, -1)), columns=cols)
        tmp['COUNT'] = np.sum(label_pred == i)
        
        # 每一类中球员占比前n名
        tmp_p = plyrs[np.where(label_pred == i)[0]]
        top20 = Counter(tmp_p).most_common(20)
        top20 = [(pm2pn[x[0]], x[1]) for x in top20]
        tmp['plyrs'] = str(top20)
        # print()
        df = df.append(tmp.iloc[0])
    return df


def outputdf(df, single=False):
    # 计算衍生数据项
    df['PTS'] = 2 * df['2P'] + 3 * df['3P'] + df['FT']
    df['TRB'] = df['ORB'] + df['DRB']
    df['MP'] = df['MP'] / 60
    df['BP'] = 48 / df['MP'] * df['BP']
    df['2P%'] = df['2P'] / df['2PA']
    df['3P%'] = df['3P'] / df['3PA']
    df['FT%'] = df['FT'] / df['FTA']
    df['eFG%'] = (df['2P'] + 1.5 * df['3P']) / (df['2PA'] + df['3PA'])
    df['TS%'] = df['PTS'] / 2 / (df['2PA'] + df['3PA'] + 0.44 * df['FTA'])
    if single:
        df = df[['2P', '2PA', '2P%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'eFG%',
                 'TS%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'BP',
                 'MP', 'PTS', '+/-']]
    else:
        df = df[['2P', '2PA', '2P%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'eFG%',
                 'TS%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'BP',
                 'MP', 'PTS', '+/-', 'COUNT', 'plyrs']]
    return df


def loadSingleGameStatsAllSeasons(start, end, ROF):
    '''
    start: 起始赛季
    end: 结束赛季
    ROF: 'regular' or 'playoff'
    '''
    # regularOrPlayoffs = ['regular', 'playoff']
    plyrs = []
    stats = []
    gamemarks = []
    for season in range(start, end):
        ss = '%d_%d' % (season, season + 1)
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, ROF))
        print(len(gms))
        for gm in tqdm(gms):
            # print(gm)
            game = Game(gm, ROF)
            record, rot, bxs = game.preprocess(load=1)
            for RoH in range(2):
                for plyr in bxs.tdbxs[RoH][0]:
                    if plyr != 'team':
                        plyrs.append(plyr)
                        gamemarks.append(gm)
                        tmp = bxs.tdbxs[RoH][0][plyr][0]
                        # OffRtg、DefRtg、前场篮板率和防守篮板率
                        # OffRtg = bxs.tdbxs[RoH][0][plyr][1][0][-4] * 100 / tmp[-3]
                        # DefRtg = bxs.tdbxs[RoH][0][plyr][1][1][-4] * 100 / tmp[-3]
                        # OrebPerc = tmp[9] / (bxs.tdbxs[RoH][0][plyr][1][0][9] + bxs.tdbxs[RoH][0][plyr][1][1][10])
                        # DrebPerc = tmp[10] / (bxs.tdbxs[RoH][0][plyr][1][0][10] + bxs.tdbxs[RoH][0][plyr][1][1][9])
                        # eFGPerc = (tmp[0] + 1.5 * tmp[3]) / (tmp[1] + tmp[4])    # 有效命中率
                        # tSPerc = tmp[-4] / 2 / (tmp[1] + 0.44 * tmp[7])    # 真实命中率
                        # ptsPerc = (tmp[1] + 0.44 * tmp[7]) / tmp[-3]    # 得分占有率
                        # astPerc = tmp[12] / tmp[-3]    # 助攻占有率
                        # tovPerc = tmp[-6] / tmp[-3]    # 失误占有率
                        # orebPerc = tmp[9] / tmp[-3]    # 前场篮板占有率
                        # FTr = tmp[6] / tmp[-3]    # 罚球占有率
                        # blkPerc =
                        # stlPerc =
                        # drebPerc =
                        stats.append(tmp[[0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20]])
                        # print(len(stats), stats[-1], plyr, gm)
                        if len(plyrs) % 10000 == 0:
                            print(len(plyrs), ss)
    
    plyrs = np.array(plyrs)
    stats = np.array(stats)
    # stats[np.isnan(stats)] = -1
    gamemarks = np.array(gamemarks)
    print(stats.shape)
    stats[:, 0] -= stats[:, 2]
    stats[:, 1] -= stats[:, 3]
    # 归一化
    absmax = np.max(np.abs(stats), axis=0)
    stats /= absmax
    writeToPickle('%d_%d_%s_singleGameBasicStats.pickle' % (start, end, ROF), stats)
    writeToPickle('%d_%d_%s_singleGameBasicStats_plyrs.pickle' % (start, end, ROF), plyrs)
    writeToPickle('%d_%d_%s_singleGameBasicStats_absmax.pickle' % (start, end, ROF), absmax)
    writeToPickle('%d_%d_%s_singleGameBasicStats_gamemarks.pickle' % (start, end, ROF), gamemarks)


def loadSingleGameStatsByPlayerBySeason(start, end, ROF):
    '''
    start: 起始赛季
    end: 结束赛季
    ROF: 'regular' or 'playoff'
    '''
    # regularOrPlayoffs = ['regular', 'playoff']
    plyrs = {}    # {{'ss': [[[16项数据], [16项数据], []], 胜场, 负场]}, {'ss': []}, ...}
    seasonBP_ave = {}
    for season in range(start, end):
        ss = '%d_%d' % (season, season + 1)
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, ROF))
        # print(len(gms))
        if ss not in seasonBP_ave:
            seasonBP_ave[ss] = 0
        for gm in tqdm(gms):
            # print(gm)
            game = Game(gm, ROF)
            record, rot, bxs = game.preprocess(load=1)
            # 胜者
            scores = [game.bxscr[0][x][0] for x in game.bxscr[0]]
            winner = 1 if scores[0] < scores[1] else 0
            for RoH in range(2):
                seasonBP_ave[ss] += bxs.tdbxs[RoH][0]['team'][-3]
                for plyr in bxs.tdbxs[RoH][0]:
                    if plyr != 'team':
                        # 初始化球员
                        if plyr not in plyrs:
                            plyrs[plyr] = {}
                        # 初始化球员赛季
                        if ss not in plyrs[plyr]:
                            plyrs[plyr][ss] = [[], 0, 0]
                        tmp = bxs.tdbxs[RoH][0][plyr][0]
                        tmp[0], tmp[1] = tmp[0] - tmp[3], tmp[1] - tmp[4]
                        # OffRtg、DefRtg、前场篮板率和防守篮板率
                        # OffRtg = bxs.tdbxs[RoH][0][plyr][1][0][-4] * 100 / tmp[-3]
                        # DefRtg = bxs.tdbxs[RoH][0][plyr][1][1][-4] * 100 / tmp[-3]
                        # OrebPerc = tmp[9] / (bxs.tdbxs[RoH][0][plyr][1][0][9] + bxs.tdbxs[RoH][0][plyr][1][1][10])
                        # DrebPerc = tmp[10] / (bxs.tdbxs[RoH][0][plyr][1][0][10] + bxs.tdbxs[RoH][0][plyr][1][1][9])
                        plyrs[plyr][ss][0].append(tmp[[0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20]])
                        plyrs[plyr][ss][1 if winner == RoH else 2] += 1
        seasonBP_ave[ss] /= (len(gms) * 2)
    # writeToPickle('%d_%d_%s_singleGameBasicStatsByPlayerBySeason.pickle' % (start, end, ROF), plyrs)
    # writeToPickle('%d_%d_%s_seasonBP_ave.pickle' % (start, end, ROF), seasonBP_ave)
    # return plyrs, seasonBP_ave


if __name__ == '__main__':
    loadSingleGameStatsAllSeasons(2000, 2020, 'playoff')
    # loadSingleGameStatsByPlayerBySeason(2000, 2021, 'regular')
