import sys

sys.path.append('../')
import pandas as pd
import os
from klasses.stats_items import *
from klasses.miscellaneous import MPTime, WinLoseCounter
from util import LoadPickle
import numpy as np
import math


# as_str = ['Date', 'Age', 'Tm', 'RoH', 'Opp', 'MP']    # 可作为字符串直接比较
# as_other = ['WoL', 'RoH'', Date', 'Playoffs']        # 需要做处理后再比较
cmps = {-1: ['=='], 0: ['>='], 1: ['<='], 2: ['>=', '<=']}
cmps_ = {-1: ['!='], 0: ['>='], 1: ['<='], 2: ['>=', '<=']}

class Player(object):
    def __init__(self, pm, RoP, csv=False):  # 构造参数：球员唯一识别号，常规赛or季后赛('regular' or 'playoff')
        # print(pm)
        self.pm = pm
        self.RoP = 0 if RoP == 'regular' else 1
        if not csv:
            plyrdr = 'D:/sunyiwu/stat/data/players/%s/%sGames/%sGameBasicStat.pickle' % (pm, RoP, RoP)
            if os.path.exists(plyrdr):
                self.dt = regular_items_en if not self.RoP else playoff_items_en
                self.ucgd_its = [12, 13]    # unchanged_items 前几列数据项雷打不动
                self.exists = True
                self.plyrFD = plyrdr    # 球员个人文件目录
                self.data = LoadPickle(self.plyrFD)
                if not isinstance(self.data, list):
                    self.data.reset_index(drop=True)
                else:
                    return
                self.cols = list(self.data.columns)
                self.cols[:self.ucgd_its[self.RoP]] = list(self.dt.keys())[:self.ucgd_its[self.RoP]]
                self.seasons = np.sum(self.data['G'] == '1')    # 赛季数
                self.games = self.data.shape[0]
                self.ss_ix = list(self.data[self.data['G'] == '1'].index) + [self.data.shape[0]]
            else:
                self.exists = False
                return

    # def _items_cmp(self, columns):    # 找出赛季数据统计缺失项并按顺序返回
    #     if not self.RoP:
    #         return sorted([[regular_items_en[x], x] for x in list(set(regular_items_en.keys()) - set(columns))])
    #     else:
    #         return sorted([[playoff_items_en[x], x] for x in list(set(playoff_items_en.keys()) - set(columns))])

    def yieldSeasons(self):  # 按赛季返回
        for i in range(self.seasons):
            yield self.data[self.ss_ix[i]:self.ss_ix[i + 1]]

    def on_board_games(self, games):
        return games[games['G'].notna()]

    def yieldGames(self, season, del_absent=True):  # 按单场比赛返回
        if del_absent:
            season = self.on_board_games(season)
        for i in season.values:
            yield i

    def _get_item(self, item, season_index=None):
        games = self.data[self.ss_ix[season_index - 1]:self.ss_ix[season_index]] if season_index else self.data
        return self.on_board_games(games)[item]

    def seasonAVE(self, ind, item):
        # 求取赛季平均，传入参数：赛季序号、统计项名称
        return np.mean(self._get_item(item, season_index=ind).astype(np.float64))

    def average(self, item):
        return np.mean(self._get_item(item).astype(np.float64))

    def seasonSUM(self, ind, item):
        # 求取赛季平均，传入参数：赛季序号、统计项名称
        return np.sum(self._get_item(item, season_index=ind).astype(np.float64))

    def sum(self, item):
        return np.sum(self._get_item(item).astype(np.float64))

    def ave_and_sum(self, resL):
        # print(self.pm)
        tmp = pd.DataFrame(resL, columns=regular_items_en.keys() if not self.RoP else playoff_items_en.keys())
        ave = []
        sumn = []
        for k in tmp.columns:
            # 几项特殊的均值/总和计算方式
            if k == 'G':  # 首列
                ave.append('%d场平均' % tmp.shape[0])
                sumn.append('%d场总和' % tmp.shape[0])
            elif k in ['Playoffs', 'Date', 'Age', 'Tm', 'Opp', 'Series', 'G#']:
                ave.append('/')
                sumn.append('/')
            elif k == 'RoH':  # 统计主客场数量
                try:
                    at = np.sum(tmp[k] == '@')
                except:
                    at = 0
                ave.append('%dr/%dh' % (at, tmp.shape[0] - at))
                sumn.append('%dr/%dh' % (at, tmp.shape[0] - at))
            elif k == 'WoL':  # 统计几胜几负
                origin = WinLoseCounter(False)
                for i in tmp[k]:
                    origin += WinLoseCounter(True, strwl=i)
                ave.append(origin.average())
                sumn.append(origin)
            elif k == 'GS':  # 统计首发次数
                try:
                    s = np.sum(tmp[k] == '1')
                except:
                    s = 0
                ave.append('%d/%d' % (s, tmp.shape[0]))
                sumn.append('%d/%d' % (s, tmp.shape[0]))
            elif k == 'MP':  # 时间加和与平均
                sum_time = MPTime('0:00.0', reverse=False)
                for i in tmp[k]:
                    if isinstance(i, str):
                        sum_time += MPTime(i, reverse=False)
                ave.append(sum_time.average(tmp.shape[0]))
                sumn.append(sum_time.strtime[:-2])
            elif '%' in k:  # 命中率单独计算
                if sumn[-2] >= 0 and sumn[-1] > 0:
                    p = '%.3f' % (sumn[-2] / sumn[-1])
                    if p != '1.000':
                        p = p[1:]
                else:
                    p = ''
                ave.append(p)
                sumn.append(p)
            else:
                tmp_sg = tmp[k][tmp[k].notna()]
                a = '%.1f' % tmp_sg.astype('float').mean()
                s = '%.1f' % tmp_sg.astype('float').sum() if k == 'GmSc' else int(tmp_sg.astype('int').sum())    # 除比赛评分以外其他求和结果均为整数
                if k == '+/-':  # 正负值加+号
                    if s != 0 and a[0] != '-':
                        a = '+' + a
                    if s > 0:
                        s = '+%d' % s
                if a == 'nan':
                    a = ''
                    s = ''
                ave.append(a)
                sumn.append(s)
        return [ave, sumn]

    def searchGame(self, stats):
        # print(stats)
        # 可统一比较大小或判断相等
        games = self.data
        games = self.on_board_games(games)
        for k in stats:
            if k != 'Diff' and self.dt[k] >= self.dt['FG'] or k in ['G', 'GS', 'G#']:
                tp = 0    # 数值型
                target = [int(x) for x in stats[k][1]]
                tmp_item = games[k].astype('float')
            elif k in ['Age', 'Tm', 'Opp', 'Series']:
                tp = 1    # 字符型
                target = stats[k][1]
                tmp_item = games[k].astype('str')
            else:
                continue
            cmp = cmps[stats[k][0]]
            # print(target, cmp)
            for cmp_i, t in enumerate(target):
                games = eval('games[tmp_item %s "%s"]' % (cmp[cmp_i], t) if tp else 'games[tmp_item %s %d]' % (cmp[cmp_i], t))
        games = list(games.values)
        if games:
            # 需要先作预处理后再比较大小或判断相等
            dup = set(stats) & {'WoL', 'RoH', 'Date', 'Playoffs', 'Diff', 'MP'}
            if dup:    # 如果条件中包含这四个选项，则做进一步筛选
                resL = []
                for game in games:
                    res, ToF = 1, True
                    for k in dup:
                        if ToF:
                            tp = 0
                            if k == 'WoL':
                                tp, x = 1, '"%s"' % game[7 if self.RoP else 6][0]
                            elif k == 'RoH':
                                x = '0' if game[4] == '@' else '1'
                            elif k == 'Date' or k == 'Playoffs':
                                x = '%s' % game[1][:8]
                            elif k == 'MP':
                                tmp = game[9 if self.RoP else 8]
                                tmp = '0' + tmp if int(tmp[:tmp.index(':')]) < 10 else tmp    # 分钟数小于10前面加0
                                if len(tmp) == 5:    # 没有数秒位
                                    tmp += ':00'
                                tp, x = 1, '"%s"' % tmp
                            else:
                                x = '%s' % game[7 if self.RoP else 6][3:-1]
                            cmp = cmps_[stats[k][0]]
                            for cmp_i, t in enumerate(stats[k][1]):
                                t = t + ':00'if k == 'MP' else t
                                if not eval('%s%s"%s"' % (x, cmp[cmp_i], t) if tp else '%s%s%s' % (x, cmp[cmp_i], t)):
                                    res, ToF = 0, False
                                    break
                        else:
                            break
                    if res:  # 符合条件，添加至结果列表
                        resL.append(game)
                if not resL:
                    return []
            else:
                resL = games
            resL += self.ave_and_sum(resL)    # 求取平均和总和
            return resL
        else:
            return []

