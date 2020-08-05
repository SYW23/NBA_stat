import sys
sys.path.append('../')
from util import minusMinutes, LoadPickle

class Player():
    def __init__(self, pm, ROP):    # 构造参数：球员唯一识别号，常规赛or季后赛
        self.playerFileDir = './data/players/' + pm + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
        self.ROP = ROP
        self.games = LoadPickle(self.playerFileDir)
        self.seasons = len(self.games)\
                          if ROP == 'regular'\
                          else len(self.games) - 1
    
    def yieldSeasons(self):
        for season in range(self.seasons):
            yield self.games[season] if self.ROP == 'regular'\
                                           else self.games[season + 1]
    
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
