import sys

sys.path.append('../')
import pandas as pd
import os
from klasses.stats_items import *
from klasses.miscellaneous import MPTime, WinLoseCounter
from util import LoadPickle
import numpy as np
import math


as_str = ['Date', 'Age', 'Tm', 'RoH', 'Opp', 'MP']    # 可作为字符串直接比较
as_other = ['WoL', 'RoH'', Date', 'Playoffs']        # 需要做处理后再比较


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
                count = tmp[k].value_counts()
                try:
                    ave.append('%d主/%d客' % (tmp.shape[0] - count.loc['@'], count.loc['@']))
                    sumn.append('%d主/%d客' % (tmp.shape[0] - count.loc['@'], count.loc['@']))
                except:
                    ave.append('%d主/%d客' % (tmp.shape[0], 0))
                    sumn.append('%d主/%d客' % (tmp.shape[0], 0))
            elif k == 'WoL':  # 统计几胜几负
                origin = WinLoseCounter(False)
                for i in tmp[k]:
                    origin += WinLoseCounter(True, strwl=i)
                ave.append(origin.average())
                sumn.append(origin)
            elif k == 'GS':  # 统计首发次数
                count = tmp[k].value_counts()
                started = count.loc['1'] if '1' in list(count.index) else 0
                ave.append('%d/%d' % (started, tmp.shape[0]))
                sumn.append('%d/%d' % (started, tmp.shape[0]))
            elif k == 'MP':  # 时间加和与平均
                sum_time = MPTime('0:00.0', reverse=False)
                for i in tmp[k]:
                    if isinstance(i, str):
                        sum_time += MPTime(i, reverse=False)
                ave.append(sum_time.average(tmp.shape[0]))
                sumn.append(sum_time.strtime[:-2])
            elif '%' in k:  # 命中率单独计算
                if sumn[-2] and sumn[-1]:
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
                s = '%.1f' % tmp_sg.astype('float').sum() if k == 'GmSc' else int(tmp_sg.astype('int').sum())
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
            if self.dt[k] >= self.dt['FG'] or k in ['G', 'GS', 'G#']:
                tp = 0
                target = [int(x) for x in stats[k][1]]
                tmp_item = games[k].astype('float')
            elif k in ['Age', 'Tm', 'Opp', 'MP', 'Series']:
                tp = 1
                target = [x if k != 'MP' else x + ':00' for x in stats[k][1]]
                tmp_item = games[k].astype('str')
            else:
                continue
            if stats[k][0] == 0:
                cmp = ['>=']
            elif stats[k][0] == 1:
                cmp = ['<=']
            elif stats[k][0] == -1:
                cmp = ['==']
            else:
                cmp = ['<=', '>=']
            # print(target, cmp)
            for cmp_i, t in enumerate(target):
                games = eval('games[tmp_item %s %d]' % (cmp[cmp_i], t)) if not tp else eval('games[tmp_item %s "%s"]' % (cmp[cmp_i], t))
                # print(games)
        resL = list(games.values)
        if resL:
            resL += self.ave_and_sum(resL)

        return resL
        if games:
            resL = []
            # 字符型数据比较大小或相等
            for game in games:
                res = 1
                for k in stats:
                    if stats[k][0] == -1:    # 相等比较
                        if k == 'RoH':
                            x = '"0"' if game[self.dt[k]] == '@' else '"1"'
                        elif k == 'WoL':
                            x = '"%s"' % game[self.dt[k]][0]
                        else:
                            x = '"%s"' % game[self.dt[k]]
                        if not eval('%s%s%s' % (x, '==', '"%s"' % stats[k][1][0])):
                            res = 0
                            break
                    else:    # 大小比较（整理部分数据格式—>双边区间比较或单边大小比较）
                        # 先整理部分统计项数据格式
                        if k == 'Date' or k == 'Playoffs':
                            x = game[self.dt[k]][:8]
                        elif k in ['Age', 'MP']:
                            x = game[self.dt[k]][:2] + game[self.dt[k]][3:]
                        elif k == 'Diff':
                            x = game[6][3:-1] if not self.RoP else game[7][3:-1]
                        else:
                            # print(self.pm, game, k)
                            x = game[self.dt[k]]

                        if stats[k][0] == 2:    # 区间比较
                            # 年龄和上场时间格式特殊处理
                            if k in ['Age', 'MP']:
                                y = [stats[k][1][0][:2] + stats[k][1][0][3:],
                                     stats[k][1][1][:2] + stats[k][1][1][3:]]
                            else:
                                y = [stats[k][1][0], stats[k][1][1]]
                            # 比较
                            if not eval(x + '>=' + y[0] + ' and ' + x + '<=' + y[1]):
                                res = 0
                                break
                        else:    # 大于或小于
                            # 年龄和上场时间格式特殊处理
                            if k in ['Age', 'MP']:
                                y = stats[k][1][0][:2] + stats[k][1][0][3:]
                                x = game[self.dt[k]][:2] + game[self.dt[k]][3:]
                            else:
                                y = stats[k][1][0]
                                x = game[self.dt[k]] if k != 'Diff' else x
                            comp = '<=' if stats[k][0] else '>='
                            # 比较
                            # print(type(x), x, y, self.pm)
                            if (isinstance(x, float) and math.isnan(x)) or not eval(str(x) + comp + y):
                                res = 0
                                break
                if res:  # 符合条件，添加至结果列表
                    resL.append(game)
        # 求取平均和总和
        if resL:
            resL += self.ave_and_sum(resL)

        return resL
