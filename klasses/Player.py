import sys

sys.path.append('../')
import pandas as pd
from klasses.stats_items import regular_items, playoff_items
import numpy as np
import math
from util import addMinutes


class Player(object):
    def __init__(self, pm, ROP):  # 构造参数：球员唯一识别号，常规赛or季后赛
        self.pm = pm
        self.playerFileDir = 'D:/sunyiwu/stat/data/players/' + pm + '/%sGames/%sGameBasicStat.csv' % (ROP, ROP)
        self.ROP = ROP
        self.games = pd.read_csv(self.playerFileDir)
        self.seasons = np.sum(self.games['G'] == 'G') + 1
        self.season_index = [-1] + list(self.games[self.games['G'].isin(['G'])].index) + [self.games.shape[0]]

    def yieldSeasons(self):  # 按赛季返回
        for i in range(self.seasons):
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

    def searchGame(self, comboboxs, stats):
        # 单场比赛数据查询
        flag = 0
        for i in stats:
            if i:    # 判断是否设置查询条件
                flag = 1
                break
        if not flag:    # 未设置查询条件，返回[-1]
            return [-1]
        RP = 0 if self.ROP == 'regular' else 1
        resL = []
        WOL = [0, 0]  # 胜负统计
        for s in self.yieldSeasons():
            for game in self.yieldGames(s):
                res = 1
                for i, item in enumerate(list(game) + ['']):
                    if stats[i]:  # 本项数据统计有设置
                        if comboboxs[i] in ['    >=', '    <=']:  # 数值或字符串比较
                            if i == 1:  # 日期
                                x = item[:8]
                                y = stats[i]
                            elif (not RP and (i == 2 or i == 8)) or (RP and i == 9):  # 年龄或上场时间
                                x = item[:2] + item[3:]
                                y = stats[i][:2] + stats[i][3:]
                            elif (not RP and i == 29) or (RP and i == 30):  # 分差
                                x = game[6][3:-1] if not RP else game[7][3:-1]
                                y = stats[i]
                            else:
                                x = item
                                y = stats[i]
                            if not eval(x + comboboxs[i] + y):
                                res = 0
                                break
                        else:  # 字符串相等比较
                            if i == 4:  # 主客场
                                x = 0 if item else 1
                            elif (not RP and i == 6) or (RP and i == 7):  # 赛果
                                x = item[0]
                            else:
                                x = item
                            if not eval('\'%s\'%s\'%s\'' % (x, comboboxs[i], stats[i].get())):
                                res = 0
                                break
                if res:  # 符合条件，添加至结果列表
                    resL.append(game)
        # 求取平均和总和
        if resL:
            tmp = pd.DataFrame(resL, columns=regular_items.keys() if not RP else playoff_items.keys())
            # tmp.to_csv('tmp.csv', index=None)
            ave = []
            sumn = []
            for i in range(tmp.shape[1]):
                # 几项特殊的均值/总和计算方式
                if i == 0:
                    ave.append('平均')
                    sumn.append('总和')
                elif (not RP and i in [1, 2, 3, 5]) or (RP and i in [1, 2, 3, 5, 6]):
                    ave.append('/')
                    sumn.append('/')
                elif i == 4:
                    count = tmp['主客场'].value_counts()
                    ave.append('%d主/%d客' % (tmp.shape[0] - count.loc['@'], count.loc['@']))
                    sumn.append('%d主/%d客' % (tmp.shape[0] - count.loc['@'], count.loc['@']))
                elif (not RP and i == 6) or (RP and i == 7):
                    w, l, diff = 0, 0, 0
                    for i in tmp['赛果']:
                        diff += float(i[3:-1])
                        if 'W' in i:
                            w += 1
                        else:
                            l += 1
                    diff_ave = diff / tmp.shape[0]
                    diff_ave = '+' + '%.1f' % diff_ave if diff_ave > 0 else '%.1f' % diff_ave
                    diff = '+' + '%d' % diff if diff > 0 else '%d' % diff
                    ave.append('%d/%d (%s)' % (w, l, diff_ave))
                    sumn.append('%d/%d (%s)' % (w, l, diff))
                elif (not RP and i == 7) or (RP and i == 8):
                    count = tmp['是否首发'].value_counts()
                    ave.append('%d/%d' % (count.loc['1'], tmp.shape[0]))
                    sumn.append('%d/%d' % (count.loc['1'], tmp.shape[0]))
                elif (not RP and i == 8) or (RP and i == 9):
                    sum_time = '0:00.0'
                    for i in tmp['上场时间']:
                        sum_time = addMinutes(sum_time, i + '.0')
                    sum_time = sum_time[:-2]
                    [min, sec] = sum_time.split(':')
                    ss = eval(min + '*60+' + str(int(sec)))
                    ss /= (60 * tmp.shape[0])
                    ss = math.modf(ss)
                    ave_time = '%d:%02d' % (ss[1], ss[0] * 60)
                    ave.append(ave_time)
                    sumn.append(sum_time)
            # 求取数值的平均值
            ind = 9 if not RP else 10
            num_ave = tmp.iloc[:, ind:].astype('float').mean(axis=0)
            num_sum = tmp.iloc[:, ind:].astype('float').sum(axis=0)
            # 命中率无均值概念，单独计算
            for i in [2, 5, 8]:
                num_ave[i] = num_ave[i - 2] / num_ave[i - 1] if num_ave[i - 1] else np.nan
                num_sum[i] = num_ave[i]
            num_ave = pd.DataFrame(num_ave.values[:, np.newaxis].T)
            num_sum = pd.DataFrame(num_sum.values[:, np.newaxis].T)
            # 小数位数调整
            num_ave = num_ave.round({0: 1, 1: 1, 2: 3, 3: 1, 4: 1, 5: 3, 6: 1, 7: 1, 8: 3, 9: 1,
                                     10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1})
            num_sum = num_sum.round({0: 0, 1: 0, 2: 3, 3: 0, 4: 0, 5: 3, 6: 0, 7: 0, 8: 3, 9: 0,
                                     10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 1, 19: 0})
            num_ave = list(num_ave.values[0])
            num_sum = list(num_sum.values[0])
            # 命中率显示保持一致（整数去掉.0，小数去掉前面的0）
            for i in range(len(num_sum)):
                if i not in [2, 5, 8, 18]:
                    num_sum[i] = int(num_sum[i])
                elif i != 18:
                    if num_sum[i] < 1:
                        num_sum[i] = str(num_sum[i])[1:]
                        num_sum[i] += '0' * (4 - len(num_sum[i]))
                        num_ave[i] = str(num_ave[i])[1:]
                        num_ave[i] += '0' * (4 - len(num_ave[i]))
                    else:
                        num_sum[i] = '1.000'
            # 正负值为正咋加上+号，为保持一致
            num_ave[-1] = '+' + str(num_ave[-1]) if num_ave[-1] > 0 else num_ave[-1]
            num_sum[-1] = '+' + str(num_sum[-1]) if num_sum[-1] > 0 else num_sum[-1]
            ave += num_ave
            sumn += num_sum
            resL.append(ave)
            resL.append(sumn)

        return resL
