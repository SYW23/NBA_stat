import sys

sys.path.append('../')
import pandas as pd
import os
from klasses.stats_items import *
from klasses.miscellaneous import MPTime, WinLoseCounter
import numpy as np
import math
from util import addMinutes


class Player(object):
    def __init__(self, pm, ROP):  # 构造参数：球员唯一识别号，常规赛or季后赛
        self.pm = pm
        plyrdr = 'D:/sunyiwu/stat/data/players/' + pm + '/%sGames/%sGameBasicStat.csv' % (ROP, ROP)
        if os.path.exists(plyrdr):
            self.exists = True
            self.playerFileDir = plyrdr
            self.ROP = ROP
            self.games = pd.read_csv(self.playerFileDir)
            col_date = self.games.columns[1]
            month = int(self.games[col_date][0][4:6])
            self.start_season = int(self.games[col_date][0][:4]) - 1 if month < 9 else int(self.games[col_date][0][:4])
            month = int(list(self.games[col_date])[-1][4:6])
            self.end_season = int(list(self.games[col_date])[-1][:4]) - 1 if month < 9\
                              else int(list(self.games[col_date])[-1][:4])
            if month >= 9 and self.end_season == 2020:
                self.end_season = 2019
            # print(self.start_season, self.end_season)
            if self.start_season == self.end_season:
                self.gameNs = 1
                self.seasons = 1
                self.season_index = [-1, self.games.shape[0]]
            else:
                # print(self.pm, self.start_season, self.end_season)
                tmp = self.games[self.games['G'] != 'G']
                self.gameNs = tmp[tmp['G'].notna()].shape[0]
                self.seasons = np.sum(self.games['G'] == 'G') + 1
                self.season_index = [-1] + list(self.games[self.games['G'].isin(['G'])].index) + [self.games.shape[0]]
            # print('生涯出场数：%d' % self.gameNs)
        else:
            self.exists = False
            return

    def _items_cmp(self, L):    # 找出赛季数据统计缺失项并按顺序返回
        if L == 19 and self.ROP == 'regular':
            return sorted([[regular_items[x], x] for x in list(set(regular_items.keys()) - set(regular_items_1973.keys()))])
        elif L == 23 and self.ROP == 'regular':
            return sorted([[regular_items[x], x] for x in list(set(regular_items.keys()) - set(regular_items_1977.keys()))])
        elif L == 25 and self.ROP == 'regular':
            return sorted([[regular_items[x], x] for x in list(set(regular_items.keys()) - set(regular_items_1979.keys()))])
        elif L == 28 and self.ROP == 'regular':
            return sorted([[regular_items[x], x] for x in list(set(regular_items.keys()) - set(regular_items_2000.keys()))])
        elif L == 20 and self.ROP == 'playoff':
            return sorted([[playoff_items[x], x] for x in list(set(playoff_items.keys()) - set(playoff_items_1973.keys()))])
        elif L == 24 and self.ROP == 'playoff':
            return sorted([[playoff_items[x], x] for x in list(set(playoff_items.keys()) - set(playoff_items_1977.keys()))])
        elif L == 26 and self.ROP == 'playoff':
            return sorted([[playoff_items[x], x] for x in list(set(playoff_items.keys()) - set(playoff_items_1979.keys()))])
        elif L == 29 and self.ROP == 'playoff':
            return sorted([[playoff_items[x], x] for x in list(set(playoff_items.keys()) - set(playoff_items_2000.keys()))])
        return []

    def yieldSeasons(self, to_integrated=False):  # 按赛季返回
        for i in range(self.seasons):
            if to_integrated:
                tmp = [float('nan') if 'Unnamed' in x else x for x in list(self.games.columns)] if i == 0\
                    else list(self.games.loc[self.season_index[i]])
                for j in tmp[::-1]:
                    if isinstance(j, float) and math.isnan(j):
                        tmp.pop()
                    else:
                        break
                omit = self._items_cmp(len(tmp))
                fm = self.games.loc[self.season_index[i] + 1:self.season_index[i + 1] - 1]
                for j in omit:
                    fm.insert(j[0], j[1], float('nan'))
                fm.drop(fm.columns[29 if self.ROP == 'regular' else 30:], axis=1, inplace=True)
                yield fm
            else:
                yield self.games.loc[self.season_index[i] + 1:self.season_index[i + 1] - 1]

    def yieldGames(self, season, del_absent=True):  # 按单场比赛返回
        '''
        现代：
        常规赛
        {0: '比赛编号', 1: 'Date', 2: 'Age', 3: 'Tm', 4: '', 5: 'Opp',
         6: '', 7: '首发', 8: 'MP', 9: 'FG', 10: 'FGA', 11: 'FG%', 12: '3P',
         13: '3PA', 14: '3P%', 15: 'FT', 16: 'FTA', 17: 'FT%', 18: 'ORB',
         19: 'DRB', 20: 'TRB', 21: 'AST', 22: 'STL', 23: 'BLK', 24: 'TOV',
         25: 'PF', 26: 'PTS', 27: 'GmSc', 28: '+/-'}
        季后赛
        {0: '比赛编号', 1: '日期', 2: '轮次', 3: 'Tm', 4: '', 5: 'Opp',
         6: '本轮比赛编号', 7: '', 8: '首发', 9: 'MP', 10: 'FG', 11: 'FGA',
         12: 'FG%', 13: '3P', 14: '3PA', 15: '3P%', 16: 'FT', 17: 'FTA',
         18: 'FT%', 19: 'ORB', 20: 'DRB', 21: 'TRB', 22: 'AST', 23: 'STL',
         24: 'BLK', 25: 'TOV', 26: 'PF', 27: 'PTS', 28: 'GmSc', 29: '+/-'}
        '''
        if del_absent:
            season = season.loc[season['G'].notna()]
        # season = season.where(season.notnull(), '')
        for i in season.values:
            yield i

    def _get_item(self, item, season_index=None):
        i = regular_items[item] if self.ROP == 'regular' else playoff_items[item]
        if season_index:
            season_games = self.games.loc[self.season_index[season_index - 1] + 1:
                                          self.season_index[season_index] - 1]
            season_games = season_games.loc[season_games['G'].notna()]  # 去除未出场的比赛
            return season_games.iloc[:, i]
        else:
            gs = self.games[self.games['G'] != 'G']
            vs = gs.iloc[:, i]
            return vs[vs.notna()]

    def seasonAVE(self, ind, item):
        # 求取赛季平均，传入参数：赛季序号、统计项名称、常规赛or季后赛
        return np.mean(self._get_item(item, season_index=ind).astype(np.float64))

    def average(self, item):
        return np.mean(self._get_item(item).astype(np.float64))

    def seasonSUM(self, ind, item):
        # 求取赛季平均，传入参数：赛季序号、统计项名称、常规赛or季后赛
        return np.sum(self._get_item(item, season_index=ind).astype(np.float64))

    def sum(self, item):
        return np.sum(self._get_item(item).astype(np.float64))

    def searchGame(self, stats):
        # 单场比赛数据查询
        RP = regular_items if self.ROP == 'regular' else playoff_items
        resL = []
        WOL = [0, 0]  # 胜负统计
        for s in self.yieldSeasons(to_integrated=True):
            for game in self.yieldGames(s):
                res = 1
                for k in stats:
                    if stats[k][0] == -1:    # 相等比较
                        if k == '主客场':
                            x = '0' if game[RP[k]] else '1'
                        elif k == '赛果':
                            x = game[RP[k]][0]
                        else:
                            x = game[RP[k]]
                        if not eval('%s%s%s' % (x, '==', stats[k][1])):
                            res = 0
                            break
                    else:    # 大小比较
                        # 整理部分统计项数据格式
                        if k == '日期':
                            x = game[RP[k]][:8]
                        elif k in ['年龄', '上场时间']:
                            x = game[RP[k]][:2] + game[RP[k]][3:]
                            # y = stats[i][:2] + stats[i][3:]
                        elif k == '分差':
                            x = game[6][3:-1] if not RP else game[7][3:-1]
                        else:
                            # print(game, k)
                            x = game[RP[k]]
                        if stats[k][0] == 2:    # 区间比较
                            # 年龄和上场时间格式特殊处理
                            if k in ['年龄', '上场时间']:
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
                            if k in ['年龄', '上场时间']:
                                y = stats[k][1][:2] + stats[k][1][3:]
                                x = game[RP[k]][:2] + game[RP[k]][3:]
                            else:
                                y = stats[k][1]
                                x = game[RP[k]]
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
            tmp = pd.DataFrame(resL, columns=regular_items.keys() if self.ROP == 'regular' else playoff_items.keys())
            ave = []
            sumn = []
            for k in tmp.columns:
                # 几项特殊的均值/总和计算方式
                if k == '比赛序号':    # 首列
                    ave.append('%d场平均' % tmp.shape[0])
                    sumn.append('%d场总和' % tmp.shape[0])
                elif k in ['日期', '年龄', '主队', '对手', '轮次', '本轮比赛序号']:
                    ave.append('/')
                    sumn.append('/')
                elif k == '主客场':    # 统计主客场数量
                    count = tmp[k].value_counts()
                    try:
                        ave.append('%d主/%d客' % (tmp.shape[0] - count.loc['@'], count.loc['@']))
                        sumn.append('%d主/%d客' % (tmp.shape[0] - count.loc['@'], count.loc['@']))
                    except:
                        ave.append('%d主/%d客' % (tmp.shape[0], 0))
                        sumn.append('%d主/%d客' % (tmp.shape[0], 0))
                elif k == '赛果':    # 统计几胜几负
                    origin = WinLoseCounter(False)
                    for i in tmp[k]:
                        origin += WinLoseCounter(True, strwl=i)
                    ave.append(origin.average())
                    sumn.append(origin)
                elif k == '是否首发':    # 统计首发次数
                    count = tmp[k].value_counts()
                    started = count.loc['1'] if '1' in list(count.index) else 0
                    ave.append('%d/%d' % (started, tmp.shape[0]))
                    sumn.append('%d/%d' % (started, tmp.shape[0]))
                elif k == '上场时间':    # 时间加和与平均
                    sum_time = MPTime('0:00.0', reverse=False)
                    for i in tmp[k]:
                        if isinstance(i, str):
                            sum_time += MPTime(i, reverse=False)
                    ave.append(sum_time.average(tmp.shape[0]))
                    sumn.append(sum_time.strtime[:-2])
                elif '命中率' in k:    # 命中率单独计算
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
                    s = '%.1f' % tmp_sg.astype('float').sum() if k == '比赛评分' else int(tmp_sg.astype('int').sum())
                    if k == '正负值':    # 正负值加+号
                        if s != 0 and a[0] != '-':
                            a = '+' + a
                        if s > 0:
                            s = '+%d' % s
                    if a == 'nan':
                        a = ''
                        s = ''
                    ave.append(a)
                    sumn.append(s)
            resL.append(ave)
            resL.append(sumn)
        return resL
