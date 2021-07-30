import sys
sys.path.append('../')
from util import LoadPickle, writeToPickle
from klasses.Game import Game
import os
import time
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import metrics
import numpy as np
import pandas as pd
from collections import Counter
from util_clusters import mse, ios, deDuplicated, plyrInLeaf_ranking, amongLeafs_ranking, outputdf, yieldSingleGameStatsAllSeasons
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
    
    def count_and_topN(self, N=30):
        '''
        统计节点分裂后，分到每一类的样本数，以及每一类中场次前N位的球员
        '''
        df = pd.DataFrame(columns=self.cols)
        for i in range(self.cs):
            tmp = self.estimator.cluster_centers_[i] * self.absmax
            tmp = pd.DataFrame(tmp.reshape((1, -1)), columns=self.cols)
            tmp['COUNT'] = np.sum(self.label_pred == i)
            # 每一类中球员场次排名前N位
            tmp_p = self.plyrs[np.where(self.label_pred == i)[0]]
            topN = Counter(tmp_p).most_common(N)
            topN = [(self.pm2pn[x[0]], x[1]) for x in topN]
            tmp['plyrs'] = str(topN)
            df = df.append(tmp.iloc[0])
        self.df = df
    
    def outputCts(self, save=''):
        self.count_and_topN()
        self.df = outputdf(self.df)
        if save:
            self.df.to_csv(save + '.csv', index=False)
    
    def outputStats(self, save=''):
        df = pd.DataFrame(self.stats * self.absmax, columns=self.cols)
        df = outputdf(df, single=True)
        df['plyr'] = [self.pm2pn[x] for x in self.plyrs]
        df['gamemark'] = self.gamemarks
        if save:
            df.to_csv(save + '.csv', index=False)


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
        self.shape = 0
    
    def doKMeans(self, repeat):
        '''
        使用KMeans进行节点分裂
        '''
        self.clustor.determineK(repeat)
        self.clustor.outputCts()
    
    def createLeaves(self, maxcs=10):
        '''
        按照分裂出的聚类中心生成子节点
        '''
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
            self.leaves[-1].shape = self.leaves[-1].clustor.stats.shape[0]
    
    # =========判断节点是否可再分=========
    def isFather(self):
        if self.leaves:
            return True
        return False
    # ==================================
    
    # =========输出节点信息========================================================================
    def outputCts(self, save=''):
        '''
        输出父节点分裂出的聚类中心(csv)    *No必须是一个父节点
        '''
        if not self.isFather():
            print('func outputCts err: 非父节点无分裂聚类中心')
        self.clustor.df.to_csv(fname + '.csv', index=False)
    
    def outputStats(self, save=''):
        '''
        输出节点的所有球员数据(csv)
        '''
        self.clustor.outputStats(save=save)
    # ===========================================================================================
    
    # =========节点内球员数据排名==============================================================================================
    def plyrRanking(self, pm):
        '''
        统计单个球员在某一节点内部各项数据的排名情况，分值越大越好
        '''
        index = self.clustor.plyrs == pm
        percent = self.clustor.stats[index].shape[0] / self.clustor.stats.shape[0]
        ranking = plyrInLeaf_ranking(index, self.clustor.stats)
        return percent, ranking
    
    def allPlyrsLeafRanking(self, plyrs):
        '''
        统计某一节点内部各球员各项数据的排名情况
        '''
        null = np.zeros((16, )) - 1
        nums = self.clustor.stats.shape[0]
        # print(self.clustor.plyrs.shape)
        selections = self.clustor.plyrs == plyrs
        plyr_stats = [self.clustor.stats[x] for x in selections]
        games = np.array([x.shape[0] for x in plyr_stats])
        percent = games / nums    # 每个球员在此叶子节点中的占比
        plyr_means = [np.mean(x, axis=0) if x.shape[0] > 0 else x for x in plyr_stats]
        ranking = np.array([np.sum(x > self.clustor.stats, axis=0) / nums if x.shape[0] > 0 else null for x in plyr_means])
        ranking[ranking == -1] = np.nan
        # print(ranking.shape)    # (1178, 16)
        return games, percent, ranking
    # ======================================================================================================================
    
    
class Basic16_clustorTree(object):
    def __init__(self, root, threshold):
        self.root = root
        self.klass = ['持球核心', '射术为王', '制霸篮下', '节节败退', '中规中矩',
                      '高配首发', '到点轮换', '肉盾替补', '垃圾时间']
        self.colors = ['royalblue', 'darkorange', 'gold', 'r', 'green',
                       'lime', 'darkorchid', 'darkblue', 'dimgrey']
        self.threshold = threshold
        self.leafNos = 0    # 叶子节点个数
        
    # =========生成树===================================================================================================
    def generatorKMeans(self, maxN, maxcs=10, repeat=1000):
        '''
        生成树
        '''
        queue = []
        queue.append(self.root)
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
                # 节省内存：清空根节点以外节点的stats、plyrs、gamemarks
                first.clustor.stats = None
                first.clustor.plyrs = None
                first.clustor.gamemarks = None
                for p in first.leaves:
                    queue.append(p)
            else:
                self.leafNos += 1
                print('\t叶子节点No.%d  %s\t%d\t%f' % (self.leafNos, first.No, first.clustor.stats.shape[0], clustorIOS))
            queue.remove(first)
        print('叶子节点共%d个' % self.leafNos)
    # ==================================================================================================================
    
    # =========节点定位方法==============================
    def findEndLeaves(self):
        '''
        层序遍历，yield所有叶子节点
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
    
    def findDiverg(self, No):
        '''
        给定节点标号，定位并返回该节点
        '''
        s = No.split('-')[1:]
        f = self.root
        for i in s:
            f = f.leaves[int(i) - 1]
        return f
    
    def findFather(self, No):
        '''
        给定节点标号，定位并返回其父节点
        '''
        assert No != '1'
        return self.findDiverg(self.findDiverg(No).father)
    # =================================================
    
    # =========节点聚类中心=================================================
    def findCt(self, No):
        '''
        返回节点聚类中心
        '''
        assert No != '1'
        father = self.findFather(No)
        return father.clustor.estimator.cluster_centers_[int(No[-1]) - 1]
    # ====================================================================
    
    # =========球员数据整树推演======================================================
    def predictThorough(self, stats, single=False):
        '''
        数据整树推演(将数据从根节点一直推算至叶子节点)
        '''
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
            queue.pop(0)
        if single:
            return list(res)[0]
        ixs = np.zeros((len(self.leafNos), ))
        print(res)
        for c in res:
            ixs[np.where(self.leafNos == c)[0][0]] = res[c]
        ixs = ixs[self.leafRankings_order]
        return ixs
    # ============================================================================
    
    # =========树的自解析=============================================
    def leafRoughRanking(self, ROF):
        '''
        叶子节点模糊排名
        '''
        leafCts, Nos, counts, leafNos = [], [], [], []
        for leaf in self.findEndLeaves():
            leafNos.append(leaf.No)
            ct = self.findCt(leaf.No)
            leafCts.append(ct)
            Nos.append("'%s'" % leaf.No)
            counts.append(leaf.clustor.stats.shape[0])
        leafCts = np.array(leafCts) * self.root.clustor.absmax
        
        df = pd.DataFrame(leafCts, columns=self.root.clustor.cols)
        # print(df)
        df = outputdf(df, single=True)
        df['ave'] = amongLeafs_ranking(leafCts)
        df['No'] = Nos
        df['COUNTS'] = counts
        df.sort_values('ave', ascending=True, inplace=True)
        df.to_csv('leafRankings_%s.csv' % ROF)
        self.leafRankings_order = df.index.values
        self.leafNos = np.array(leafNos)
    # ==============================================================

    # =========初始8/9类分析============================================================================================
    def plyrInitialKlass(root, pm, ROF):
        '''
        输出指定球员每场比赛数据在初始9大类中的占比饼图
        '''
        label_pred = root.root.clustor.label_pred[root.root.clustor.plyrs == pm]
        part = np.array([np.sum(label_pred == i) / label_pred.shape[0] for i in range(root.root.clustor.cs)])
        part = part[part != 0]
        # print(part)
        labels = np.array([root.klass[x] for x in np.argwhere(part != 0).reshape(1, -1)[0]])[part.argsort()[::-1]]
        colors = np.array([root.colors[x] for x in np.argwhere(part != 0).reshape(1, -1)[0]])[part.argsort()[::-1]]
        part = part[part.argsort()[::-1]]
        lt25 = np.sum(part >= 0.25)
        explode = [0.06] * lt25 + [0] * (part.shape[0] - lt25)
        
        plt.figure(figsize=(15, 9))
        _, texts, _ = plt.pie(part, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=120)
        for t in texts:
            t.set_size(10)
        plt.title(root.root.clustor.pm2pn[pm] + '  %s共计%d场比赛\n' % (ROF[0].upper() + ROF[1:], label_pred.shape[0]))
        plt.axis('equal')
        plt.legend()
        plt.show()
    # ================================================================================================================


if __name__ == '__main__':
    
    mode = 0    # 常规赛0季后赛1
    
    if mode:    # 季后赛
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
        max_plyr_in_one_game = 8
    else:    # 常规赛
        maxcs = 11
        maxN = 2000
        repeat = 1000
        fname = '2000_2021'
        ROF = 'regular'
        threshold = 0.2
        rootKlass = ['制霸篮下', '持球核心', '射术为王', '节节败退', '内线肉盾',
                     '高配首发', '中规中矩', '到点轮换', '肉盾替补', '垃圾时间']
        rootColors = ['gold', 'royalblue', 'darkorange', 'r', 'y',
                      'lime', 'green', 'darkorchid', 'darkblue', 'dimgrey']
        max_plyr_in_one_game = 8
# =============================================================================
#     # %%
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

    # %%
    MVPs = ['duncati01', 'garneke01', 'nashst01', 'nowitdi01', 'bryanko01',
            'jamesle01', 'rosede01', 'duranke01', 'curryst01', 'westbru01',
            'hardeja01', 'antetgi01', 'jokicni01']
    
    root = LoadPickle('%s_%s_Basic16_clustorTree.pickle' % (fname, ROF))
    root.klass = rootKlass
    root.colors = rootColors
    plyrs = LoadPickle('%s_%s_singleGameBasicStats_plyrs.pickle' % (fname, ROF))
    plyrs = np.array(list(set(plyrs))).reshape(-1, 1)
    x, countLeaf, countFather = 0, 0, 0
    father = {}
    # 每个叶子节点  球员的比赛数games
    #             球员的比赛数占叶子节点总比赛数的比例percent
    #             球员的各项数据在叶子节点中的排名（前百分比）allPlyrsLeafRankings
    games, percent, allPlyrsLeafRankings = [], [], []
    
    maxN, minN, maxLevel = 0, 10000, 0
    for leaf in root.findEndLeaves():
        countLeaf += 1
        x += leaf.clustor.stats.shape[0]
        # 父节点统计
        if leaf.father not in father:
            fatherLeaf = root.findFather(leaf.No)
            countFather += 1
            father[leaf.father] = ''
            # print('父 ', leaf.father, leaf.clustorIOS if leaf.father != '1' else '', fatherLeaf.clustor.stats.shape, fatherLeaf.clustor.cs)
        # 统计每个叶子节点中所有球员的占比、ranking
        games_, percent_, ranking = leaf.allPlyrsLeafRanking(plyrs)
        games.append(games_)
        percent.append(percent_)
        ranking[ranking == -1] = np.nan
        allPlyrsLeafRankings.append(ranking)
        if leaf.clustor.stats.shape[0] > maxN:
            maxN = leaf.clustor.stats.shape[0]
        if leaf.clustor.stats.shape[0] < minN:
            minN = leaf.clustor.stats.shape[0]
        if leaf.level > maxLevel:
            maxLevel = leaf.level
        # print('\t|__叶子', leaf.No, leaf.clustorIOS, leaf.clustor.stats.shape)
        
    print('总数据量:', x, '父节点数量:', countFather, '叶子节点数量:', countLeaf, '叶子节点最大样本数:', maxN, '叶子节点最小样本数:', minN, '树的最大深度:', maxLevel)
    games = np.array(games)
    percent = np.array(percent)
    allPlyrsLeafRankings = np.array(allPlyrsLeafRankings).transpose(1, 0, 2)
    root.leafRoughRanking(ROF)
    # writeToPickle('allPlyrsLeafRankings.pickle', allPlyrsLeafRankings)
    
    
# =============================================================================
#     # %%
#     root.plyrInitialKlass('greendr01', ROF)
#     print(root.findDiverg('1-1-2-1-1').plyrRanking('jamesle01'))
# =============================================================================


# =============================================================================
#     # %%
#     # 绘制单个球员叶子节点各项数据ranking矩阵
#     pm = 'jamesle01'
#     xticks = np.arange(root.leafRankings_order.shape[0])
#     yticks = np.arange(root.root.clustor.stats.shape[1])
#     plt.matshow(allPlyrsLeafRankings[np.where(plyrs == pm)[0][0]][root.leafRankings_order].T)
#     plt.xticks(xticks, [str(x) for x in games[:, np.where(plyrs == pm)[0][0]][root.leafRankings_order]], rotation=45)
#     plt.yticks(yticks, root.root.clustor.cols)
#     plt.colorbar()
#     
#     # MVP球员叶子节点各项数据ranking矩阵
#     fig, ax = plt.subplots(13, figsize=(120,80))
#     for i in range(len(MVPs)):
#         ax[i].matshow(allPlyrsLeafRankings[np.where(plyrs == MVPs[i])[0][0]][root.leafRankings_order].T)
#         ax[i].set_xticks(xticks)
#         ax[i].set_xticklabels([str(x) for x in games[:, np.where(plyrs == MVPs[i])[0][0]][root.leafRankings_order]], rotation=60, fontsize=18)
#         ax[i].set_yticks(yticks)
#         ax[i].set_yticklabels(root.root.clustor.cols)
#         ax[i].set_ylabel(root.root.clustor.pm2pn[MVPs[i]], fontsize=50)
#     # plt.colorbar(ax=ax[0])
#     plt.savefig('mvp_%s.png' % ROF)
#     plt.close()
# =============================================================================
    
# =============================================================================
#     # %%
#     # 球员数据整树推演
#     resd = root.predictThorough(root.root.clustor.stats[root.root.clustor.plyrs == 'jamesle01'])
# =============================================================================
    
    # %%
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
#                 ixs = np.zeros((len(root.leafNos), ))
#                 for c in resd:
#                     ixs[np.where(root.leafNos == c)[0][0]] = resd[c]
#                 ixs = ixs[root.leafRankings_order]
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
#     # %%
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
#         ixs = np.zeros((len(root.leafNos), ))
#         for c in resd:
#             ixs[np.where(root.leafNos == c)[0][0]] = resd[c]
#         mvps.append(ixs[root.leafRankings_order])
#     mvps = np.array(mvps)
#     
#     df = pd.DataFrame(mvps, index=names)
#     df.to_csv('mvp_seasons.csv')
# =============================================================================

# =============================================================================
#     # %%
#     # 由叶子节点编号推得节点stats、plyrs、gamemarks等信息（节省储存空间）
#     leaf = root.findDiverg('1-1-2-1-1')
#     print(leaf.clustor.plyrs.shape)
#     fs = []
#     tmp = leaf
#     while tmp is not root.root:
#         fs.append(root.findFather(tmp.No))
#         tmp = fs[-1]
#     s = [int(x) - 1 for x in '1-1-2-1-1'.split('-')[1:]]
#     tmp = root.root.clustor.plyrs
#     for ix, i in enumerate(fs[::-1]):
#         tmp = tmp[i.clustor.label_pred == s[ix]]
#     print(tmp)
# =============================================================================
    
    # %%
    def alter_wol(key, dikt, wol, x, gm, ts):
        if key not in dikt:
            dikt[key] = [0, 0, 0, []]
        dikt[key][0 if wol == x else 1] += 1
        dikt[key][3].append([gm[:-7], ts])
    
    def mode_module(mode):
        return '-'.join([str(x + 1) for x in sorted(mode)[:max_plyr_in_one_game]])
    
    def set_module(mode):
        return '-'.join([str(x + 1) for x in list(set(sorted(mode)[:max_plyr_in_one_game]))])
    
    leaf_wols = {}    # {'leafNo': [胜场数, 负场数, 胜率, [[gm, [胜队, 负队]], ...]]}
    wol_modes = {}    # {'mode': [胜场数, 负场数, 胜率, [[gm, [胜队, 负队]], ...]]}
    wol_sets = {}    # {'modeset': [胜场数, 负场数, 胜率, [[gm, [胜队, 负队]], ...]]}
    count = 0
    for _, stats_game, gm_game, wol_game, wol_teams in yieldSingleGameStatsAllSeasons(2000, 2020, ROF):
        count += 1
        for i in range(2):
            roughKlass = root.root.clustor.estimator.predict(stats_game[i] / root.root.clustor.absmax)
            roughKlass_set = set_module(roughKlass)
            roughKlass_str = mode_module(roughKlass)
            alter_wol(roughKlass_str, wol_modes, wol_game, i, gm_game, wol_teams)
            alter_wol(roughKlass_set, wol_sets, wol_game, i, gm_game, wol_teams)
            for stat in stats_game[i]:
                # start = time.time()
                leafNo = root.predictThorough(stat.reshape(1, -1) / root.root.clustor.absmax, single=True)
                alter_wol(leafNo, leaf_wols, wol_game, i, gm_game, wol_teams)
                # print('\t', time.time() - start)
    for m in [leaf_wols, wol_modes, wol_sets]:
        for k in m:
            m[k][2] = m[k][0] / (m[k][1] + m[k][0])
    
    leaf_order = sorted(leaf_wols.items(), key=lambda x:[x[1][2], x[1][0] if x[1][2] >= 0.5 else -x[1][1]], reverse=True)    # 按胜率（首选）、胜场数（次选）排名
    mode_order = sorted(wol_modes.items(), key=lambda x:[x[1][2], x[1][0] if x[1][2] >= 0.5 else -x[1][1]], reverse=True)
    modeset_order = sorted(wol_sets.items(), key=lambda x:[x[1][2], x[1][0] if x[1][2] >= 0.5 else -x[1][1]], reverse=True)
    print('总比赛数:', count)
    
    # %%
    mode = [[0, 0, 0, 3, 4, 5, 6, 7, 6, 7, 7], [0, 0, 3, 3, 3, 5, 6, 7, 6, 7, 7]]
    
    print(wol_modes[mode_module(mode[0])][:2])
    print(wol_sets[set_module(mode[0])][:2])
    print(wol_modes[mode_module(mode[1])][:2])
    print(wol_sets[set_module(mode[1])][:2])
    
    
    # %%
    # 预测胜率
    def predictWLr(mode, ret='both'):    # rate: 返回预测胜率; side: 返回预测胜方; both: 返回预测胜率和胜方
        assert ret in ['rate', 'side', 'both']
        set_WLr = [wol_sets[set_module(mode[i])][2] for i in range(2)]
        # print(set_WLr)
        maxi = 0 if set_WLr[0] > set_WLr[1] else 1
        if ret == 'side':
            return maxi
        max_WLr = 100 / (set_WLr[maxi] / set_WLr[maxi - 1] + 1) * set_WLr[maxi] / set_WLr[maxi - 1] if set_WLr[maxi - 1] else 100
        min_WLr = 100 - max_WLr
        res = [0, 0]
        res[maxi], res[maxi - 1] = max_WLr, min_WLr
        if ret == 'rate':
            return res
        else:
            return res, maxi
    
    # print(predictWLr(mode))
    error, count = 0, 0
    for _, stats_game, gm_game, wol_game, _ in yieldSingleGameStatsAllSeasons(2019, 2020, ROF):
        count += 1
        mode = []
        for i in range(2):
            mode.append(root.root.clustor.estimator.predict(stats_game[i] / root.root.clustor.absmax))
        WLr, winner = predictWLr(mode)
        # print(WLr, winner)
        if WLr == [50, 50]:
            print('ooooooops', gm_game)
        if winner != wol_game:
            error += 1
            print(WLr, gm_game)
    print('accuracy:', 1 - error / count, '%')
    
    
    
    