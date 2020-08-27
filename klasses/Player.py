import sys
sys.path.append('../')
import pandas as pd
from klasses.stats_items import regular_items, playoff_items
import numpy as np

class Player(object):
    def __init__(self, pm, ROP):    # 构造参数：球员唯一识别号，常规赛or季后赛
        self.pm = pm
        self.playerFileDir = 'D:/sunyiwu/stat/data/players/' + pm + '/%sGames/%sGameBasicStat.csv' % (ROP, ROP)
        self.ROP = ROP
        self.games = pd.read_csv(self.playerFileDir)
        self.seasons = np.sum(self.games['G'] == 'G') + 1
        self.season_index = [-1] + list(self.games[self.games['G'].isin(['G'])].index) + [self.games.shape[0]]
    
    def yieldSeasons(self):    # 按赛季返回
        for i in range(self.seasons):
            yield self.games.loc[self.season_index[i]+1:self.season_index[i+1]-1]
    
    def yieldGames(self, season, del_absent=True):    # 按单场比赛返回
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
        season = season.where(season.notnull(), '')
        for i in season.values:
            yield i

    def seasonAVE(self, ind, item, ROP):
        # 求取赛季平均，传入参数：赛季序号、统计项名称、常规赛or季后赛
        season_games = self.games.loc[self.season_index[ind]+1:self.season_index[ind+1]-1]
        season_games = self.season_games.loc[season_games['G'].notna()]    # 去除未出场的比赛
        i = regular_items[item] if ROP == 'regular' else playoff_items[item]
        return np.mean(season_games.iloc[:, i].astype(np.float64))
    
    def searchGame(self, comboboxs, stats):
        # 单场比赛数据查询
        flag = 0
        for i in stats:
            if i.get():    # 未设置查询条件
                flag = 1
                break
        if not flag:    # 未设置查询条件，返回[-1]
            return [-1]
        RP = 1 if self.ROP == 'regular' else 0
        resL = []
        for s in self.yieldSeasons():
            for game in self.yieldGames(s):
                res = 1
                for i, item in enumerate(list(game) + ['']):
                    if stats[i].get():    # 本项数据统计有设置
                        if comboboxs[i].get() in ['    >=', '    <=']:    # 数值或字符串比较
                            if i == 1:    # 日期
                                x = item[:8]
                                y = stats[i].get()
                            elif (RP and (i == 2 or i == 8)) or (not RP and i == 9):    # 年龄或上场时间
                                x = item[:2] + item[3:]
                                y = stats[i].get()[:2] + stats[i].get()[3:]
                            elif (RP and i == 29) or (not RP and i == 30):    # 分差
                                x = game[6][3:-1] if RP else game[7][3:-1]
                                y = stats[i].get()
                            else:
                                x = item
                                y = stats[i].get()
                            if not eval(x + comboboxs[i].get() + y):
                                res = 0
                                break
                        else:    # 字符串相等比较
                            if i == 4:    # 主客场
                                x = 0 if item else 1
                                y = stats[i].get()
                            elif (RP and i == 6) or (not RP and i == 7):    # 赛果
                                x = item[0]
                            else:
                                x = item
                            if not eval('\'%s\'%s\'%s\'' % (x, comboboxs[i].get(), stats[i].get())):
                                res = 0
                                break
                if res:    # 符合条件，添加至结果列表
                    resL.append(game)
        return resL
    
    
    
    
    