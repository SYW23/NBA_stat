import sys
sys.path.append('../')
from util import LoadPickle
from klasses.stats_items import regular_items, playoff_items

class Player():
    def __init__(self, pm, ROP):    # 构造参数：球员唯一识别号，常规赛or季后赛
        self.pm = pm
        self.playerFileDir = 'D:/sunyiwu/stat/data/players/' + pm + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
        self.ROP = ROP
        self.games = LoadPickle(self.playerFileDir)
        self.seasons = len(self.games)\
                          if ROP == 'regular'\
                          else len(self.games) - 1
    
    def yieldSeasons(self, pt=True):
        for season in range(self.seasons):
            s = self.games[season] if self.ROP == 'regular'\
                                   else self.games[season + 1]
            if s or (len(s) == 1 and s == ['G', 'Date', 'Age', 'Tm', '', 'Opp',
                                           '', 'GS', 'MP', 'FG', 'FGA', 'FG%',
                                           '3P', '3PA', '3P%', 'FT', 'FTA',
                                           'FT%', 'ORB', 'DRB', 'TRB', 'AST',
                                           'STL', 'BLK', 'TOV', 'PF', 'PTS',
                                           'GmSc', '+/-']):
                if pt:
                    if self.ROP != 'regular':
                        print('season %s' % s[0][0][1][:4])
                    else:
                        print('season %s' % s[1][1][:4])
                yield s
    
    def yieldGames(self, season):
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
        if self.ROP == 'regular':
            for g in season[1:]:
                yield g
        else:
            if season and season[0] != 'G':
                for s in season:
                    for g in s:
                        yield g
    
    def seasonAVE(self, ind, item, ROP):
        # 求取赛季平均，传入参数：赛季序号、统计项名称、常规赛or季后赛
        s = 0
        seas = self.games[ind][1:]
        i = regular_items[item] if ROP == 'regular' else playoff_items[item]
        for g in seas:
            s += int(g[i])
        return s / len(seas)
    
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
        for s in self.yieldSeasons(pt=False):
            for game in self.yieldGames(s):
                res = 1
                for i, item in enumerate(game + ['']):
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
    
    
    
    
    
