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
from util_clusters import mse, ios, deDuplicated, outputdf
np.set_printoptions(suppress=True)
plt.rcParams['font.sans-serif']=['KaiTi', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
pm2pn = LoadPickle('../data/playermark2playername.pickle')


class Basic16_clustor(object):
    '''
    聚类器类
    必要属性：plyrs、stats、absmax
    '''
    def __init__(self, maxcs=10):
        self.cols = ['2P', '2PA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
                     'AST', 'STL', 'BLK', 'TOV', 'PF', 'BP', 'MP', '+/-']
        self.maxcs = maxcs
        f = open('../data/playermark2playername.pickle', 'rb')
        self.pm2pn = pickle.load(f)
        f.close()
        self.plyrs = None
        self.gamemarks = None
        self.stats = None
        self.absmax = None
        
    def readfiles(self, fname):
        self.plyrs = LoadPickle('%s_plyrs.pickle' % fname)
        self.gamemarks = LoadPickle('%s_gamemarks.pickle' % fname)
        self.stats = LoadPickle('%s.pickle' % fname)
        self.absmax = LoadPickle('%s_absmax.pickle' % fname)
        self.stats[self.stats == np.inf] = -1
        
    def elbow(self, start, end):
        # 存放每次结果的误差平方和、轮廓系数、CH分(Calinski-Harabaz)、戴维森堡丁指数
        self.indicators = {'SSE': [], 'SIL': [], 'CHS': [], 'DBI': []}
        self.start, self.end = start, end
        for k in tqdm(range(start, end)):
            estimator = KMeans(n_clusters=k, init='k-means++')  # 构造聚类器
            estimator.fit(self.stats * self.absmax)
            label_pred = estimator.labels_
            self.indicators['SSE'].append(estimator.inertia_)
            self.indicators['SIL'].append(metrics.silhouette_score(self.stats * self.absmax, label_pred))
            self.indicators['CHS'].append(metrics.calinski_harabasz_score(self.stats * self.absmax, label_pred))
            self.indicators['DBI'].append(metrics.davies_bouldin_score(self.stats * self.absmax, label_pred))
        
    def elbow_plot(self):
        X = range(self.start, self.end)
        plt.subplot(221)
        plt.xlabel('k')
        plt.ylabel('SSE')
        plt.plot(X, self.indicators['SSE'],'o-', label='SSE')
        plt.subplot(222)
        plt.xlabel('k')
        plt.ylabel('SIL')
        plt.plot(X, self.indicators['SIL'],'x-', label='SIL')
        plt.subplot(223)
        plt.xlabel('k')
        plt.ylabel('CHS')
        plt.plot(X, self.indicators['CHS'],'+-', label='CHS')
        plt.subplot(224)
        plt.xlabel('k')
        plt.ylabel('DBI')
        plt.plot(X, self.indicators['DBI'],'2-', label='DBI')
        plt.show()
        
    def cl_cts_finetuning(self, cs, repeat):
        '''
        repeat: 重复聚类次数
        '''
        self.cs = cs    # 类别数
        # 初始聚类器
        self.estimator = KMeans(n_clusters=cs, init='k-means++')
        self.estimator.fit(self.deDuplicatedData)
        # 多次聚类，匹配每次聚类与初始聚类的结果，求均值
        count = 0
        cl_cts_ave = self.estimator.cluster_centers_.copy()
        cl_cts_count = np.array([np.sum(self.estimator.labels_ == x) for x in range(self.cs)]).reshape(self.cs, 1)
        for i in range(repeat):
            mse_mat = np.zeros((self.cs, self.cs))
            estimator_tmp = KMeans(n_clusters=self.cs, init='k-means++')
            estimator_tmp.fit(self.deDuplicatedData)
            label_pred_tmp = estimator_tmp.labels_
            cl_cts_tmp = estimator_tmp.cluster_centers_
            # 以欧式距离匹配本次聚类与初始聚类的结果
            for x in range(self.cs):
                for y in range(self.cs):
                    mse_mat[x, y] = mse(self.estimator.cluster_centers_[x], cl_cts_tmp[y])
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
            cl_cts_count_tmp = np.array([np.sum(label_pred_tmp == x) for x in range(self.cs)])[miny].reshape(self.cs, 1)
            cl_cts_tmp = cl_cts_tmp[miny]
            cl_cts_ave = (cl_cts_ave * cl_cts_count + cl_cts_tmp * cl_cts_count_tmp) / (cl_cts_count + cl_cts_count_tmp)
            cl_cts_count += cl_cts_count_tmp
        # print('%d/%d' % (count, repeat))
        self.estimator.cluster_centers_ = cl_cts_ave[np.argsort(cl_cts_ave[:, 14])[::-1]]    # 按照MP从大到小排序
    
    def determineK(self, repeat):
        for k in range(self.maxcs, 1, -1):
            self.estimator = KMeans(n_clusters=k, init='k-means++')
            self.deDuplicatedData = deDuplicated(self.stats)    # 数据去重
            # self.estimator.fit(self.deDuplicatedData)
            try:
                self.cl_cts_finetuning(k, repeat)
            except KeyError:
                print('%d down!' % k)
                continue
            else:
                self.cs = k
                break
            self.deDuplicatedData = []
        self.label_pred = self.estimator.predict(self.stats)    # 按照排序后的center重新确定label
        # print('选定簇的个数：%d' % k)
    
    def count_and_top20(self):
        df = pd.DataFrame(columns=self.cols)
        for i in range(self.cs):
            tmp = self.estimator.cluster_centers_[i] * self.absmax
            tmp = pd.DataFrame(tmp.reshape((1, -1)), columns=self.cols)
            tmp['COUNT'] = np.sum(self.label_pred == i)
            # 每一类中球员占比前n名
            tmp_p = self.plyrs[np.where(self.label_pred == i)[0]]
            top20 = Counter(tmp_p).most_common(20)
            top20 = [(self.pm2pn[x[0]], x[1]) for x in top20]
            tmp['plyrs'] = str(top20)
            # print()
            df = df.append(tmp.iloc[0])
        self.df = df
    
    def outputdf(self, save=''):
        self.count_and_top20()
        self.df = outputdf(self.df)
        if save:
            self.df.to_csv(save + '.csv', index=False)


class Basic16_clustorDiverg(object):
    '''
    聚类器发散节点类
    '''
    def __init__(self, clustor):
        self.clustor = clustor
        self.leaves = []
        self.clustorIOS = 0
        self.level = 1
        self.leafNo = 1
        self.father = None
        self.No = '1'
    
    def doKMeans(self, repeat):
        self.clustor.determineK(repeat)
        self.clustor.outputdf()
    
    def createLeaves(self, maxcs=10):
        for i in range(self.clustor.cs):
            self.leaves.append(Basic16_clustorDiverg(Basic16_clustor(maxcs=maxcs)))
            self.leaves[-1].clustor.stats = self.clustor.stats[self.clustor.label_pred == i]
            self.leaves[-1].clustor.plyrs = self.clustor.plyrs[self.clustor.label_pred == i]
            self.leaves[-1].clustor.gamemarks = self.clustor.gamemarks[self.clustor.label_pred == i]
            self.leaves[-1].clustor.absmax = self.clustor.absmax
            self.leaves[-1].level = self.level + 1
            self.leaves[-1].leafNo = i + 1
            self.leaves[-1].father = self.No
            self.leaves[-1].No = self.No + '-%d' % self.leaves[-1].leafNo
            

class Basic16_clustorTree(object):
    def __init__(self, root, threshold):
        self.root = root
        self.klass = ['持球核心', '射术为王', '制霸篮下', '节节败退', '中规中矩',
                      '高配首发', '到点轮换', '肉盾替补', '垃圾时间']
        self.colors = ['royalblue', 'darkorange', 'gold', 'r', 'green',
                       'lime', 'darkorchid', 'darkblue', 'dimgrey']
        self.threshold = threshold
        
    def generatorKMeans(self, maxN, maxcs=10, repeat=1000):
        queue = []
        queue.append(self.root)
        count = 0
        while True:
            if not queue:
                break
            print(queue[0].No)
            first = queue[0]
            # 如果不是根节点，计算类内平均间距
            if first is not self.root:
                fatherCT = self.findFather(first.No).clustor.estimator.cluster_centers_[int(first.No[-1]) - 1]
                clustorIOS = ios(fatherCT, first.clustor.stats)
                first.clustorIOS = clustorIOS
            if first is self.root or (first.clustor.stats.shape[0] > maxN and clustorIOS > self.threshold):
                # 未满足一定条件，节点继续使用KMeans发散
                if first is self.root:
                    print('\t节点发散中...\t%d' % first.clustor.stats.shape[0])
                else:
                    print('\t节点发散中...\t%d\t%f' % (first.clustor.stats.shape[0], clustorIOS))
                first.doKMeans(repeat)
                print('\t节点发散—>%d' % first.clustor.cs)
                # print(first.clustor.df)
                first.createLeaves(maxcs=maxcs)
                for p in first.leaves:
                    queue.append(p)
            else:
                count += 1
                print('\t叶子节点No.%d  %s\t%d\t%f' % (count, first.No, first.clustor.stats.shape[0], clustorIOS))
            queue.remove(first)
        print('叶子节点共%d个' % count)
    
    def findEndLeaves(self):
        '''
        yield叶子节点
        '''
        queue = []
        queue.append(self.root)
        while True:
            if not queue:
                break
            first = queue[0]
            for p in first.leaves:
                queue.append(p)
            if not first.leaves:
                yield first
            queue.remove(first)
    
    def findLeaf(self, No):
        '''
        给定叶子节点标号，找到叶子节点
        '''
        s = No.split('-')[1:]
        f = self.root
        for i in s:
            f = f.leaves[int(i) - 1]
        return f
    
    def findFather(self, No):
        '''
        给定节点标号，找到其父节点
        '''
        return self.findLeaf(self.findLeaf(No).father)
    
    def findLeafCt(self, No):
        '''
        返回叶子节点聚类中心
        '''
        father = self.findFather(No)
        return father.clustor.estimator.cluster_centers_[int(No[-1]) - 1]
    
    def iosOfLeaf(self, No):
        '''
        给定叶子节点标号，计算其各点距聚类中心的平均欧氏距离
        '''
        leaf = self.findLeaf(No)
        return ios(self.findLeafCt(No), leaf.clustor.stats)
    
    def printLeafCts(self, No, fname=''):
        '''
        输出节点的聚类中心（csv），只适用于非叶子节点
        '''
        leaf = self.findLeaf(No)
        leaf.clustor.outputdf()
        # print(leaf.clustor.df)
        if fname:
            leaf.clustor.df.to_csv('%s.csv' % fname, index=False)
    
    def printLeafStats(self, No, fname=''):
        '''
        输出节点的所有球员数据（csv）
        '''
        leaf = self.findLeaf(No)
        df = pd.DataFrame(leaf.clustor.stats * leaf.clustor.absmax, columns=leaf.clustor.cols)
        df = outputdf(df, single=True)
        df['plyr'] = [leaf.clustor.pm2pn[x] for x in leaf.clustor.plyrs]
        df['gamemark'] = leaf.clustor.gamemarks
        if fname:
            df.to_csv('%s.csv' % fname, index=False)
            
    def plyrInitialKlass(self, pm, ROF):
        '''
        输出指定球员每场比赛数据在初始9大类中的占比饼图
        '''
        stat_plyr = self.root.clustor.stats[self.root.clustor.plyrs == pm]
        label_pred = self.root.clustor.estimator.predict(stat_plyr)
        part = np.array([np.sum(label_pred == i) / label_pred.shape[0] for i in range(self.root.clustor.cs)])
        part = part[part != 0]
        # print(part)
        labels = np.array([self.klass[x] for x in np.argwhere(part != 0).reshape(1, -1)[0]])[part.argsort()[::-1]]
        colors = np.array([self.colors[x] for x in np.argwhere(part != 0).reshape(1, -1)[0]])[part.argsort()[::-1]]
        part = part[part.argsort()[::-1]]
        lt25 = np.sum(part >= 0.25)
        explode = [0.06] * lt25 + [0] * (part.shape[0] - lt25)
        
        plt.figure(figsize=(15, 9))
        _, texts, _ = plt.pie(part, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=120)
        for t in texts:
            t.set_size(10)
        plt.title(self.root.clustor.pm2pn[pm] + '  %s共计%d场比赛\n' % (ROF[0].upper() + ROF[1:], label_pred.shape[0]))
        plt.axis('equal')
        plt.legend()
        plt.show()
    
    def plyrLeafRanking(self, pm, No):
        '''
        统计单个球员在某一节点内部各项数据的排名情况
        '''
        leaf = self.findLeaf(No)
        # print(leaf.clustor.stats.shape, (leaf.clustor.plyrs == pm).shape)
        plyr_stats = leaf.clustor.stats[leaf.clustor.plyrs == pm]
        percent = plyr_stats.shape[0] / leaf.clustor.stats.shape[0]
        # print('占比:', percent)
        ranking = np.sum(np.mean(plyr_stats, axis=0) > leaf.clustor.stats, axis=0) / leaf.clustor.stats.shape[0]
        # print(ranking)
        return percent, ranking
    
    def allPlyrsLeafRanking(self, plyrs, No):
        '''
        统计所有球员在某一节点内部各项数据的排名情况
        '''
        leaf = self.findLeaf(No)
        null = np.zeros((16, )) - 1
        nums = leaf.clustor.stats.shape[0]
        selections = leaf.clustor.plyrs == plyrs
        plyr_stats = [leaf.clustor.stats[x] for x in selections]
        games = np.array([x.shape[0] for x in plyr_stats])
        percent = games / nums    # 每个球员在此叶子节点中的占比
        plyr_means = [np.mean(x, axis=0) if x.shape[0] > 0 else x for x in plyr_stats]
        ranking = np.array([np.sum(x > leaf.clustor.stats, axis=0) / nums if x.shape[0] > 0 else null for x in plyr_means])
        ranking[ranking == -1] = np.nan
        return games, percent, ranking
    
    def predictThorough(self, stats):
        # clustor = self.root.clustor
        # label_pred = clustor.estimator.predict(stats)
        # print(label_pred.shape)
        
        queue = []
        queue.append([self.root, stats])
        res = {}
        while True:
            if not queue:
                break
            first = queue[0]
            
            if 'estimator' in first[0].clustor.__dir__():    # 如果节点可分
                label_pred = first[0].clustor.estimator.predict(first[1])
                ixs = np.unique(label_pred)
                # print(first[0].No, ixs, len(first[1]))
                for p in ixs:
                    queue.append([first[0].leaves[p], first[1][label_pred == p]])
            else:
                res[first[0].No] = len(first[1])
            # if not first.leaves:
                # yield first
            queue.pop(0)
        return res
    
    def leafRanking(self, ROF):
        leafRankings = []
        for leaf in self.findEndLeaves():
            ct = self.findLeafCt(leaf.No)
            leafRankings.append(np.sum(ct > self.root.clustor.stats, axis=0) / self.root.clustor.stats.shape[0])
        leafRankings = np.array(leafRankings)
        order = np.argsort(np.mean(leafRankings, axis=1))[::-1]
        leafRankings = leafRankings[order]
        df = pd.DataFrame(leafRankings, columns=self.root.clustor.cols)
        df['RK'] = order + 1
        df.to_csv('leafRankings_%s.csv' % ROF)


if __name__ == '__main__':
    
    mode = 0    # 常规赛0季后赛1
    
    if mode:
        maxcs = 8
        maxN = 100
        repeat = 1000
        fname = '2000_2020'
        ROF = 'playoff'
        threshold = 0.2
        rootKlass = ['球队核心', '射术为王', '内线支柱', '节节败退', '高配首发',
                     '肉盾替补', '空间射手', '垃圾时间']
        rootColors = ['royalblue', 'darkorange', 'gold', 'r', 'lime',
                      'darkblue', 'green', 'dimgrey']
    else:
        maxcs = 10
        maxN = 5000
        repeat = 500
        fname = '2000_2021'
        ROF = 'regular'
        threshold = 0.25
        rootKlass = ['制霸篮下', '持球核心', '射术为王', '节节败退', '内线肉盾',
                     '高配首发', '中规中矩', '到点轮换', '肉盾替补', '垃圾时间']
        rootColors = ['gold', 'royalblue', 'darkorange', 'r', 'y',
                      'lime', 'green', 'darkorchid', 'darkblue', 'dimgrey']
        
# =============================================================================
#     #%%
#     # 创建根聚类器
#     rootClustor = Basic16_clustor(maxcs=maxcs)
#     rootClustor.readfiles('%s_%s_singleGameBasicStats' % (fname, ROF))
#     # root.elbow(2, 21)
#     # root.elbow_plot()
#     
#     # 创建根发散节点
#     rootDiverg = Basic16_clustorDiverg(rootClustor)
#     
#     root = Basic16_clustorTree(rootDiverg, threshold)
#     root.generatorKMeans(maxN, maxcs=maxcs, repeat=repeat)
#     writeToPickle('%s_%s_Basic16_clustorTree.pickle' % (fname, ROF), root)
# =============================================================================

    #%%
    MVPs = ['duncati01', 'garneke01', 'nashst01', 'nowitdi01', 'bryanko01',
            'jamesle01', 'rosede01', 'duranke01', 'curryst01', 'westbru01',
            'hardeja01', 'antetgi01', 'jokicni01']
    
    root = LoadPickle('%s_%s_Basic16_clustorTree.pickle' % (fname, ROF))
    root.klass = rootKlass
    root.colors = rootColors
    plyrs = LoadPickle('%s_%s_singleGameBasicStats_plyrs.pickle' % (fname, ROF))
    plyrs = np.array(list(set(plyrs))).reshape(-1, 1)
    x, count, countFather = 0, 0, 0
    father = {}
    # 每个叶子节点  球员的比赛数games
    #             球员的比赛数占叶子节点总比赛数的比例percent
    #             球员的各项数据在叶子节点中的排名（前百分比）allPlyrsEndLeafRankings
    #             每个叶子节点聚类中心聚类中心（上场时间，+/-值与上场时间的比值）
    games, percent, allPlyrsEndLeafRankings, endLeafRanking = [], [], [], []
    
    leafNos = []
    for endLeaf in root.findEndLeaves():
        count += 1
        x += endLeaf.clustor.stats.shape[0]
        leafNos.append(endLeaf.No)
        # 计算父节点的类间距离
        if endLeaf.father not in father:
            fatherLeaf = root.findFather(endLeaf.No)
            countFather += 1
            father[endLeaf.father] = ''
            # 打印父节点的聚类中心
            # root.printLeafCts('%s' % fatherLeaf.No, fname='./k10_fatherLeafs/%s' % fatherLeaf.No)
            if endLeaf.father == '1':
                print('父 ', endLeaf.father, fatherLeaf.clustor.stats.shape, fatherLeaf.clustor.cs)
            else:
                print('父 ', endLeaf.father, endLeaf.clustorIOS, fatherLeaf.clustor.stats.shape, fatherLeaf.clustor.cs)
        
        # 统计每个叶子节点中所有球员的占比、ranking
        games_, percent_, ranking = root.allPlyrsLeafRanking(plyrs, endLeaf.No)
        games.append(games_)
        percent.append(percent_)
        ranking[ranking == -1] = np.nan
        allPlyrsEndLeafRankings.append(ranking)
        
        # 计算叶子节点聚类中心各项排名
        ct = root.findLeafCt(endLeaf.No)
        endLeafRanking.append(np.sum(ct > root.root.clustor.stats, axis=0) / root.root.clustor.stats.shape[0])
        
        
        interOuSqr = root.iosOfLeaf(endLeaf.No)
        print('\t|__叶子', endLeaf.No, interOuSqr, endLeaf.clustor.stats.shape, endLeaf.clustor.stats.shape[0] / interOuSqr)
        
    print('总数据量:', x, '父节点数量:', countFather, '叶子节点数量:', count)
    games = np.array(games)
    percent = np.array(percent)
    leafNos = np.array(leafNos)
    endLeafRanking = np.array(endLeafRanking)
    endLeafRanking_order = np.argsort(np.mean(endLeafRanking, axis=1))[::-1]
    allPlyrsEndLeafRankings = np.array(allPlyrsEndLeafRankings).transpose(1, 0, 2)
    
    # writeToPickle('allPlyrsEndLeafRanking.pickle', allPlyrsEndLeafRankings)
    
    # root.printLeafCts('1-2-4-3-2', fname='./1-2-4-3-2')
    # root.printLeafStats('1-2-4-3-2', fname='1-2-4-3-2')
    # root.plyrInitialKlass('greendr01', ROF)
    # print(root.plyrLeafRanking('jamesle01', '1-2'))
    
    #%%
    # 绘制单个球员叶子节点各项数据ranking矩阵
    pm = 'jamesle01'
    xticks = np.arange(endLeafRanking_order.shape[0])
    yticks = np.arange(root.root.clustor.stats.shape[1])
    plt.matshow(allPlyrsEndLeafRankings[np.where(plyrs == pm)[0][0]][endLeafRanking_order].T)
    plt.xticks(xticks, [str(x) for x in games[:, np.where(plyrs == pm)[0][0]][endLeafRanking_order]], rotation=45)
    plt.yticks(yticks, root.root.clustor.cols)
    plt.colorbar()
    
    # MVP球员叶子节点各项数据ranking矩阵
    fig, ax = plt.subplots(13, figsize=(120,80))
    for i in range(len(MVPs)):
        ax[i].matshow(allPlyrsEndLeafRankings[np.where(plyrs == MVPs[i])[0][0]][endLeafRanking_order].T)
        ax[i].set_xticks(xticks)
        ax[i].set_xticklabels([str(x) for x in games[:, np.where(plyrs == MVPs[i])[0][0]][endLeafRanking_order]], rotation=60, fontsize=18)
        ax[i].set_yticks(yticks)
        ax[i].set_yticklabels(root.root.clustor.cols)
        ax[i].set_ylabel(root.root.clustor.pm2pn[MVPs[i]], fontsize=50)
    # plt.colorbar(ax=ax[0])
    plt.savefig('mvp_%s.png' % ROF)
    plt.close()
    
# =============================================================================
#     #%%
#     # 球员数据整树推演
#     resd = root.predictThorough(root.root.clustor.stats[root.root.clustor.plyrs == 'jamesle01'])
#     ixs = np.zeros((len(leafNos), ))
#     for c in resd:
#         ixs[np.where(leafNos == c)[0][0]] = resd[c]
#     ixs = ixs[endLeafRanking_order]
# =============================================================================

    
    #%%
    # 球员分赛季数据整树推演
# =============================================================================
#     stats_bySeason = LoadPickle('2000_2021_singleGameBasicStatsByPlayerBySeason.pickle')
#     seasonBP_ave = LoadPickle('2000_2021_seasonBP_ave.pickle')
#     absmax = LoadPickle('2000_2021_singleGameBasicStats_absmax.pickle')
#     fullGames = {'2000_2001': 82, '2001_2002': 82, '2002_2003': 82, '2003_2004': 82,
#                  '2004_2005': 82, '2005_2006': 82, '2006_2007': 82, '2007_2008': 82,
#                  '2008_2009': 82, '2009_2010': 82, '2010_2011': 82, '2011_2012': 66,
#                  '2012_2013': 82, '2013_2014': 82, '2014_2015': 82, '2015_2016': 82,
#                  '2016_2017': 82, '2017_2018': 82, '2018_2019': 82, '2019_2020': 72,
#                  '2020_2021': 72}
#     plyr_season_leafs = []
#     y = []
#     seasons = []
#     plyr_names = []
#     mvp_shares = {}
#     for season in range(2000, 2021):
#         ss = '%d_%d' % (season, season + 1)
#         mvp_share = pd.read_csv('../data/awards/%d_mvp_awards_share.csv' % (season + 1))
#         mvp_shares[ss] = mvp_share
#     
#     for plyr in tqdm(stats_bySeason):
#         for ss in stats_bySeason[plyr]:
#             # print(ss)
#             stats_plyr = stats_bySeason[plyr][ss]
#             # print(stats_plyr)
#             plyr_mean = np.mean(np.array(stats_plyr[0]), axis=0)
#             if plyr_mean[4] + 2 * plyr_mean[0] + 3 * plyr_mean[2] > 5 or plyr in mvp_shares[ss]['Player'].values:
#                 stats_plyr[0] = np.array(stats_plyr[0]) / absmax
#                 resd = root.predictThorough(stats_plyr[0])
#                 ixs = np.zeros((len(leafNos), ))
#                 for c in resd:
#                     ixs[np.where(leafNos == c)[0][0]] = resd[c]
#                 ixs = ixs[endLeafRanking_order]
#                 ixs = np.append(ixs, [stats_plyr[1], stats_plyr[2], seasonBP_ave[ss], fullGames[ss]])
#                 # print(ixs)
#                 share = 0
#                 ix = mvp_shares[ss][mvp_shares[ss]['Player'] == plyr]
#                 if not ix.empty:
#                     share = ix['Share'].values[0]
#                     
#                 plyr_season_leafs.append(ixs)
#                 y.append(share)
#                 seasons.append(ss)
#                 plyr_names.append(plyr)
#     writeToPickle('mvp_share_training_data.pickle', [np.array(x) for x in [plyr_season_leafs, y, seasons, plyr_names]])
# =============================================================================
    
# =============================================================================
#     #%%
#     # 球员MVP赛季数据整树推演
#     stats_bySeason = LoadPickle('2000_2021_singleGameBasicStatsByPlayerBySeason.pickle')
#     absmax = LoadPickle('2000_2021_singleGameBasicStats_absmax.pickle')
#     mvps = []
#     names = []
#     for season in range(2000, 2021):
#         ss = '%d_%d' % (season, season + 1)
#         mvp_share = pd.read_csv('../data/awards/%d_mvp_awards_share.csv' % (season + 1))
#         
#         mvp = mvp_share['Player'].iloc[0]
#         names.append(pm2pn[mvp])
#         stats_plyr = stats_bySeason[mvp][ss]
#         stats_plyr[0] = np.array(stats_plyr[0]) / absmax
#         resd = root.predictThorough(stats_plyr[0])
#         ixs = np.zeros((len(leafNos), ))
#         for c in resd:
#             ixs[np.where(leafNos == c)[0][0]] = resd[c]
#         mvps.append(ixs[endLeafRanking_order])
#     mvps = np.array(mvps)
#     
#     df = pd.DataFrame(mvps, index=names)
#     df.to_csv('mvp_seasons.csv')
# =============================================================================
    
# =============================================================================
#     #%%
#     # 输出所有叶子节点Ranking
#     leafRankings = []
#     Nos = []
#     counts = []
#     for leaf in root.findEndLeaves():
#         ct = root.findLeafCt(leaf.No)
#         leafRankings.append(np.sum(ct > root.root.clustor.stats, axis=0) / root.root.clustor.stats.shape[0])
#         Nos.append("'%s'" % leaf.No)
#         counts.append(leaf.clustor.stats.shape[0])
#     leafRankings = np.array(leafRankings)
#     # order = np.argsort(np.mean(leafRankings, axis=1))[::-1]
#     # leafRankings = leafRankings[order]
#     df = pd.DataFrame(leafRankings, columns=root.root.clustor.cols)
#     df['ave'] = np.mean(leafRankings, axis=1)
#     df['No'] = Nos
#     df['COUNTS'] = counts
#     
#     df.sort_values('ave', ascending=False, inplace=True)
#     # df['RK'] = order + 1
#     df.to_csv('leafRankings_%s.csv' % ROF)
# =============================================================================
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    